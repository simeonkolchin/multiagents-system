import os
from pathlib import Path

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("TRANSCRIBE_PROVIDER", "mock")
os.environ.setdefault("OPENROUTER_API_KEY", "")

_DB_PATH = Path(__file__).resolve().parent / "test_copilot.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH}"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.db.base import create_all, engine  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _prepare_db():
    if _DB_PATH.exists():
        _DB_PATH.unlink()
    await create_all()
    yield
    await engine.dispose()
    if _DB_PATH.exists():
        _DB_PATH.unlink()


@pytest.fixture
def competencies():
    import json

    from app.schemas.rubric import Competency

    data = json.loads(
        (Path(__file__).resolve().parent.parent / "app/seed/rubric_ml_middle.json").read_text(
            encoding="utf-8"
        )
    )
    return [Competency(**c) for c in data["competencies"]]


@pytest.fixture
def episodes():
    from app.services.transcript import parse_transcript

    raw = (
        Path(__file__).resolve().parent.parent / "app/seed/interview_demo.txt"
    ).read_text(encoding="utf-8")
    return parse_transcript(raw)
