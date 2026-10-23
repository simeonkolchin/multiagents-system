from pydantic import BaseModel, Field


class Competency(BaseModel):
    id: str
    name: str
    description: str = ""
    good_signals: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class RubricCreate(BaseModel):
    role: str
    level: str = ""
    competencies: list[Competency]


class RubricRead(RubricCreate):
    id: int


class GenerateRubricRequest(BaseModel):
    vacancy: str


class RubricDraft(RubricCreate):
    pass
