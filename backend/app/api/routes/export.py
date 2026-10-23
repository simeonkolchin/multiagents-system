from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

from app.api.deps import CurrentUser, SessionDep
from app.repositories import sessions as sessions_repo
from app.schemas.scorecard import Scorecard
from app.services.export import scorecard_to_docx, scorecard_to_markdown

router = APIRouter(prefix="/sessions", tags=["export"])

_DOCX_MEDIA = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


async def _scorecard(session: SessionDep, session_id: int, user) -> Scorecard:
    record = await sessions_repo.get(session, session_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="session not found")
    if not record.scorecard:
        raise HTTPException(status_code=409, detail="session has no scorecard yet")
    return Scorecard(**record.scorecard)


@router.get("/{session_id}/export.docx")
async def export_docx(
    session_id: int, session: SessionDep, user: CurrentUser
) -> Response:
    scorecard = await _scorecard(session, session_id, user)
    data = scorecard_to_docx(scorecard)
    return Response(
        content=data,
        media_type=_DOCX_MEDIA,
        headers={
            "Content-Disposition": f'attachment; filename="scorecard_{session_id}.docx"'
        },
    )


@router.get("/{session_id}/export.md", response_class=PlainTextResponse)
async def export_markdown(
    session_id: int, session: SessionDep, user: CurrentUser
) -> str:
    scorecard = await _scorecard(session, session_id, user)
    return scorecard_to_markdown(scorecard)
