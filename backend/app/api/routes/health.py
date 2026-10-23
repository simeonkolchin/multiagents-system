from fastapi import APIRouter

from app.api.deps import SettingsDep

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: SettingsDep) -> dict[str, object]:
    return {
        "status": "ok",
        "llm_provider": "mock" if settings.is_mock else settings.llm_provider,
        "llm_model": settings.llm_model,
        "transcribe_provider": (
            "mock" if settings.is_transcribe_mock else settings.transcribe_provider
        ),
        "transcribe_model": settings.transcribe_model,
    }
