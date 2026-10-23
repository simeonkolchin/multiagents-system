import asyncio
import os
import shutil
import tempfile

_AUDIO_FORMATS = {"wav", "mp3", "flac", "m4a", "ogg", "webm", "aac"}


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def write_temp(data: bytes, suffix: str = ".bin") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    return path


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _is_video(filename: str, content_type: str) -> bool:
    if content_type.startswith("video/"):
        return True
    return _extension(filename) in {"mp4", "mov", "mkv", "avi", "m4v", "wmv", "flv"}


async def ensure_audio(
    data: bytes, filename: str, content_type: str
) -> tuple[bytes, str]:
    if not _is_video(filename, content_type):
        fmt = _extension(filename)
        return data, fmt if fmt in _AUDIO_FORMATS else "mp3"

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg не найден: извлечение аудио из видео недоступно в этой среде."
        )

    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i",
        "pipe:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "mp3",
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(input=data)
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='ignore')[:500]}")
    return stdout, "mp3"


async def probe_duration(data: bytes) -> float:
    if shutil.which("ffprobe") is None:
        return 0.0
    path = write_temp(data)
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-i",
            path,
            "-show_entries",
            "format=duration",
            "-v",
            "quiet",
            "-of",
            "csv=p=0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
    finally:
        os.unlink(path)
    try:
        return float(stdout.decode().strip())
    except (ValueError, AttributeError):
        return 0.0


async def extract_chunk(path: str, start: float, duration: float) -> bytes:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-ss",
        str(start),
        "-t",
        str(duration),
        "-i",
        path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "mp3",
        "pipe:1",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg chunk failed: {stderr.decode(errors='ignore')[:300]}")
    return stdout
