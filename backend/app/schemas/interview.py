from typing import Literal

from pydantic import BaseModel, Field

Speaker = Literal["interviewer", "candidate", "unknown"]


class Episode(BaseModel):
    id: int
    t: str
    speaker: Speaker
    text: str


class InterviewCreate(BaseModel):
    title: str
    raw_text: str


class InterviewRead(BaseModel):
    id: int
    title: str
    episodes: list[Episode] = Field(default_factory=list)
