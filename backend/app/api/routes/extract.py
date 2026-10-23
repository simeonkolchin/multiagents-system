from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import CurrentUser, SettingsDep
from app.schemas.session import ExtractResult
from app.services.extract import extract_text

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("", response_model=ExtractResult)
async def extract(
    settings: SettingsDep, user: CurrentUser, file: UploadFile = File(...)
) -> ExtractResult:
    data = await file.read()
    limit = settings.max_upload_mb * 1024 * 1024
    if len(data) > limit:
        raise HTTPException(
            status_code=413, detail=f"файл больше {settings.max_upload_mb} МБ"
        )
    try:
        text = extract_text(data, file.filename or "upload", file.content_type or "")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"не удалось прочитать файл: {exc}") from exc
    if not text:
        raise HTTPException(status_code=422, detail="из файла не извлёкся текст")
    return ExtractResult(text=text)
