from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import CurrentUser, SettingsDep
from app.llm.factory import build_llm_client
from app.schemas.session import TranscribeResult
from app.services.transcript import format_episodes
from app.transcribe.factory import build_transcriber
from app.transcribe.formatter import result_to_episodes
from app.transcribe.roles import assign_roles

router = APIRouter(prefix="/transcribe", tags=["transcribe"])


@router.post("", response_model=TranscribeResult)
async def transcribe(
    settings: SettingsDep, user: CurrentUser, file: UploadFile = File(...)
) -> TranscribeResult:
    data = await file.read()
    limit = settings.max_upload_mb * 1024 * 1024
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"файл больше {settings.max_upload_mb} МБ",
        )

    transcriber = build_transcriber(settings)
    try:
        result = await transcriber.transcribe(
            data, file.filename or "upload", file.content_type or ""
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    episodes = result_to_episodes(result)
    if not settings.is_mock:
        episodes = await assign_roles(build_llm_client(settings), episodes)
    return TranscribeResult(
        text=format_episodes(episodes),
        language=result.language,
        duration=result.duration,
        episodes=episodes,
    )
