import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import interviews as interviews_repo
from app.repositories import rubrics as rubrics_repo
from app.services.transcript import parse_transcript

_DIR = Path(__file__).resolve().parent
_RUBRIC = _DIR / "rubric_ml_middle.json"
_INTERVIEW = _DIR / "interview_demo.txt"


async def seed_demo(
    session: AsyncSession, owner_id: int | None = None
) -> dict[str, int]:
    existing = await rubrics_repo.list_all(session, owner_id=owner_id)
    if existing:
        interviews = await interviews_repo.list_all(session, owner_id=owner_id)
        return {
            "rubric_id": existing[0].id,
            "interview_id": interviews[0].id if interviews else 0,
        }

    rubric_data = json.loads(_RUBRIC.read_text(encoding="utf-8"))
    rubric = await rubrics_repo.create(
        session,
        role=rubric_data["role"],
        level=rubric_data["level"],
        competencies=rubric_data["competencies"],
        owner_id=owner_id,
    )

    raw_text = _INTERVIEW.read_text(encoding="utf-8")
    episodes = [e.model_dump() for e in parse_transcript(raw_text)]
    interview = await interviews_repo.create(
        session,
        title="Демо-интервью: middle ML-инженер",
        raw_text=raw_text,
        episodes=episodes,
        owner_id=owner_id,
    )
    return {"rubric_id": rubric.id, "interview_id": interview.id}
