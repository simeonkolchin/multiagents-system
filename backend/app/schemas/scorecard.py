from typing import Literal

from pydantic import BaseModel, Field

Sufficiency = Literal["confirmed", "partial", "not_demonstrated", "no_data"]
Provenance = Literal["independent", "clarified", "corrected", "hinted", "unknown"]
EvidenceKind = Literal["demonstrated", "told", "mixed", "none"]


class CompetencyFinding(BaseModel):
    competency_id: str
    observation: str = ""
    episode_refs: list[int] = Field(default_factory=list)
    interpretation: str = ""
    sufficiency: Sufficiency = "no_data"
    confidence: float = 0.0


class HintNote(BaseModel):
    competency_id: str
    episode_refs: list[int] = Field(default_factory=list)
    provenance: Provenance = "unknown"
    note: str = ""


class EvidenceNote(BaseModel):
    competency_id: str
    episode_refs: list[int] = Field(default_factory=list)
    kind: EvidenceKind = "none"
    note: str = ""


class CoverageNote(BaseModel):
    competency_id: str
    covered: bool = False
    note: str = ""


class InterviewAnalysis(BaseModel):
    coverage: list[CoverageNote] = Field(default_factory=list)
    hints: list[HintNote] = Field(default_factory=list)
    evidence: list[EvidenceNote] = Field(default_factory=list)
    reasoning_notes: str = ""


class ReviewIssue(BaseModel):
    competency_id: str
    kind: Literal[
        "missing_episode",
        "quote_mismatch",
        "wrong_speaker",
        "overbroad_conclusion",
        "missing_caveat",
    ]
    detail: str = ""


class ReviewResult(BaseModel):
    issues: list[ReviewIssue] = Field(default_factory=list)
    reanalyze: list[str] = Field(default_factory=list)
    notes: str = ""


class ScorecardRow(BaseModel):
    competency_id: str
    name: str
    observation: str = ""
    episode_refs: list[int] = Field(default_factory=list)
    conclusion: str = ""
    sufficiency: Sufficiency = "no_data"
    provenance: Provenance = "unknown"
    evidence_kind: EvidenceKind = "none"
    disputed: bool = False
    dispute_reason: str = ""
    open_questions: list[str] = Field(default_factory=list)


class NextQuestion(BaseModel):
    competency_id: str
    question: str
    checks: str = ""
    why_unknown: str = ""
    signals: list[str] = Field(default_factory=list)


class CandidateView(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    growth_areas: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class Scorecard(BaseModel):
    role: str = ""
    level: str = ""
    rows: list[ScorecardRow] = Field(default_factory=list)
    next_questions: list[NextQuestion] = Field(default_factory=list)
    candidate_view: CandidateView = Field(default_factory=CandidateView)
    disputes: list[ReviewIssue] = Field(default_factory=list)


class InterviewerClaimAudit(BaseModel):
    competency_id: str
    claim: str
    supported: bool
    suggestion: str = ""
    episode_refs: list[int] = Field(default_factory=list)


class EditConclusion(BaseModel):
    competency_id: str
    conclusion: str


class DisputeRequest(BaseModel):
    competency_id: str
    reason: str = ""
