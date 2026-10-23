import json
from pathlib import Path

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas.rubric import Competency
from app.schemas.session import DemoDataset, SeedResult
from app.seed.seed import seed_demo

router = APIRouter(prefix="/demo", tags=["demo"])

_SEED = Path(__file__).resolve().parent.parent.parent / "seed"


@router.post("/seed", response_model=SeedResult)
async def seed(session: SessionDep, user: CurrentUser) -> SeedResult:
    return SeedResult(**await seed_demo(session, owner_id=user.id))


@router.get("/dataset", response_model=DemoDataset)
async def dataset(user: CurrentUser) -> DemoDataset:
    rubric = json.loads((_SEED / "rubric_classic_ml.json").read_text(encoding="utf-8"))
    return DemoDataset(
        role=rubric["role"],
        level=rubric["level"],
        competencies=[Competency(**c) for c in rubric["competencies"]],
        title="МОК по classic ML (middle Data Science)",
        transcript=(_SEED / "interview_classic_ml.txt").read_text(encoding="utf-8"),
        resume=(_SEED / "resume_demo.txt").read_text(encoding="utf-8"),
        vacancy=(_SEED / "vacancy_classic_ml.txt").read_text(encoding="utf-8"),
    )
