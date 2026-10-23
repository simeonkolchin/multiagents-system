from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import Scorecard


class SessionCreate(BaseModel):
    rubric_id: int
    interview_id: int
    resume: str = ""


class SessionRead(BaseModel):
    id: int
    rubric_id: int
    interview_id: int
    status: str
    scorecard: Scorecard = Field(default_factory=Scorecard)
    trace: dict[str, Any] = Field(default_factory=dict)


class SessionSummary(BaseModel):
    id: int
    rubric_id: int
    interview_id: int
    status: str
    role: str = ""
    level: str = ""
    title: str = ""
    competencies: int = 0
    created_at: datetime | None = None


class TranscribeResult(BaseModel):
    text: str
    language: str = ""
    duration: float = 0.0
    episodes: list[Episode] = Field(default_factory=list)


class AuditRequest(BaseModel):
    competency_id: str
    claim: str


class SeedResult(BaseModel):
    rubric_id: int
    interview_id: int


class ExtractResult(BaseModel):
    text: str


class DemoDataset(BaseModel):
    role: str
    level: str
    competencies: list[Competency]
    title: str
    transcript: str
    resume: str
    vacancy: str
