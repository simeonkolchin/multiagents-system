import os

import httpx

from app.config import Settings
from app.transcribe.audio import (
    ensure_audio,
    extract_chunk,
    ffmpeg_available,
    probe_duration,
    write_temp,
)
from app.transcribe.client import TranscriptResult, TranscriptSegment


class OpenRouterTranscriber:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._endpoint = f"{settings.llm_base_url.rstrip('/')}/audio/transcriptions"

    async def transcribe(
        self, audio: bytes, filename: str, content_type: str
    ) -> TranscriptResult:
        payload, fmt = await ensure_audio(audio, filename, content_type)
        duration = await probe_duration(payload)
        chunk = self._settings.transcribe_chunk_seconds

        if duration > chunk and ffmpeg_available():
            return await self._transcribe_chunked(payload, duration, chunk)
        return await self._transcribe_single(payload, fmt)

    async def _transcribe_single(self, payload: bytes, fmt: str) -> TranscriptResult:
        body = await self._request(payload, fmt)
        segments = self._segments(body, offset=0.0)
        return TranscriptResult(
            text=body.get("text", ""),
            language=body.get("language", ""),
            duration=float(body.get("duration", 0.0)),
            segments=segments,
        )

    async def _transcribe_chunked(
        self, payload: bytes, duration: float, chunk: float
    ) -> TranscriptResult:
        segments: list[TranscriptSegment] = []
        texts: list[str] = []
        path = write_temp(payload, ".mp3")
        try:
            start = 0.0
            while start < duration:
                piece = await extract_chunk(path, start, chunk)
                body = await self._request(piece, "mp3")
                segments.extend(self._segments(body, offset=start))
                if body.get("text"):
                    texts.append(body["text"])
                start += chunk
        finally:
            os.unlink(path)
        return TranscriptResult(
            text=" ".join(texts),
            language="",
            duration=duration,
            segments=segments,
        )

    def _segments(self, body: dict, offset: float) -> list[TranscriptSegment]:
        segments = [
            TranscriptSegment(
                start=float(item.get("start", 0.0)) + offset,
                end=float(item.get("end", 0.0)) + offset,
                text=str(item.get("text", "")),
                speaker=item.get("speaker"),
            )
            for item in body.get("segments", [])
        ]
        if not segments and body.get("text"):
            segments = [
                TranscriptSegment(start=offset, end=offset, text=body["text"])
            ]
        return segments

    async def _request(self, payload: bytes, fmt: str) -> dict:
        headers = {"Authorization": f"Bearer {self._settings.openrouter_api_key}"}
        files = {"file": (f"audio.{fmt}", payload, f"audio/{fmt}")}
        data = {
            "model": self._settings.transcribe_model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "segment",
        }
        async with httpx.AsyncClient(
            timeout=self._settings.llm_request_timeout
        ) as client:
            response = await client.post(
                self._endpoint, headers=headers, data=data, files=files
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenRouter STT {response.status_code}: {response.text[:400]}"
            )
        return response.json()
