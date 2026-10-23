from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import (
    CandidateView,
    CompetencyFinding,
    InterviewAnalysis,
    InterviewerClaimAudit,
    NextQuestion,
    ReviewResult,
    Scorecard,
    ScorecardRow,
)
from app.services import heuristics

_DISPUTE_KINDS = {
    "overbroad_conclusion",
    "quote_mismatch",
    "wrong_speaker",
    "missing_episode",
}

_WHY_UNKNOWN = {
    "no_data": "Тему не обсуждали на интервью.",
    "not_demonstrated": "Тему затронули, но кандидат её не раскрыл.",
    "partial": "Ответ подтверждён частично или прозвучал после подсказки.",
}


def synthesize_scorecard(
    role: str,
    level: str,
    competencies: list[Competency],
    episodes: list[Episode],
    findings: list[CompetencyFinding],
    interview_analysis: InterviewAnalysis,
    review: ReviewResult,
) -> Scorecard:
    finding_by_id = {f.competency_id: f for f in findings}
    hint_by_id = {h.competency_id: h for h in interview_analysis.hints}
    evidence_by_id = {
        e.competency_id: e for e in interview_analysis.evidence if e.kind != "none"
    }
    issues_by_id: dict[str, list] = {}
    for issue in review.issues:
        issues_by_id.setdefault(issue.competency_id, []).append(issue)

    rows: list[ScorecardRow] = []
    for comp in competencies:
        finding = finding_by_id.get(comp.id, CompetencyFinding(competency_id=comp.id))
        issues = issues_by_id.get(comp.id, [])
        sufficiency = finding.sufficiency

        hint = hint_by_id.get(comp.id)
        if hint:
            provenance = "hinted"
        elif sufficiency == "confirmed":
            provenance = "independent"
        else:
            provenance = "unknown"

        if any(i.kind == "missing_caveat" for i in issues) and sufficiency == "confirmed":
            sufficiency = "partial"

        evidence = evidence_by_id.get(comp.id)
        evidence_kind = evidence.kind if evidence else "none"

        dispute_issues = [i for i in issues if i.kind in _DISPUTE_KINDS]
        open_questions = []
        if sufficiency != "confirmed":
            open_questions.append(
                _WHY_UNKNOWN.get(sufficiency, "Требуется дополнительная проверка.")
            )

        rows.append(
            ScorecardRow(
                competency_id=comp.id,
                name=comp.name,
                observation=finding.observation,
                episode_refs=finding.episode_refs,
                conclusion=finding.interpretation,
                sufficiency=sufficiency,
                provenance=provenance,
                evidence_kind=evidence_kind,
                disputed=bool(dispute_issues),
                dispute_reason="; ".join(i.detail for i in dispute_issues),
                open_questions=open_questions,
            )
        )

    return Scorecard(
        role=role,
        level=level,
        rows=rows,
        next_questions=_next_questions(competencies, rows),
        candidate_view=_candidate_view(rows),
        disputes=list(review.issues),
    )


def _next_questions(
    competencies: list[Competency], rows: list[ScorecardRow]
) -> list[NextQuestion]:
    comp_by_id = {c.id: c for c in competencies}
    questions: list[NextQuestion] = []
    for row in rows:
        if row.sufficiency == "confirmed":
            continue
        comp = comp_by_id.get(row.competency_id)
        if comp is None:
            continue
        questions.append(
            NextQuestion(
                competency_id=comp.id,
                question=(
                    f"Попросите кандидата разобрать конкретный случай по теме "
                    f"«{comp.name}»."
                ),
                checks=comp.description or comp.name,
                why_unknown=_WHY_UNKNOWN.get(row.sufficiency, ""),
                signals=comp.good_signals,
            )
        )
    return questions


def _candidate_view(rows: list[ScorecardRow]) -> CandidateView:
    strengths = [r.name for r in rows if r.sufficiency == "confirmed"]
    growth = [
        r.name for r in rows if r.sufficiency in ("partial", "not_demonstrated")
    ]
    examples = [
        r.observation
        for r in rows
        if r.sufficiency == "confirmed" and r.observation
    ]
    return CandidateView(strengths=strengths, growth_areas=growth, examples=examples)


def apply_edit(scorecard: dict, competency_id: str, conclusion: str) -> dict:
    for row in scorecard.get("rows", []):
        if row.get("competency_id") == competency_id:
            row["conclusion"] = conclusion
    return scorecard


def apply_dispute(scorecard: dict, competency_id: str, reason: str) -> dict:
    for row in scorecard.get("rows", []):
        if row.get("competency_id") == competency_id:
            row["disputed"] = True
            existing = row.get("dispute_reason", "")
            row["dispute_reason"] = "; ".join(p for p in [existing, reason] if p)
    return scorecard


def audit_interviewer_claim(
    competency_id: str,
    claim: str,
    competencies: list[Competency],
    episodes: list[Episode],
) -> InterviewerClaimAudit:
    comp = next((c for c in competencies if c.id == competency_id), None)
    if comp is None:
        return InterviewerClaimAudit(
            competency_id=competency_id,
            claim=claim,
            supported=False,
            suggestion="Компетенция не найдена в рубрике.",
        )
    match = heuristics.match_competency(episodes, comp)
    hinted = competency_id in heuristics.hinted_competency_ids(episodes, competencies)
    supported = len(match.candidate_ids) >= 2 and not hinted
    if supported:
        suggestion = "Вывод подтверждается несколькими самостоятельными ответами."
    elif not match.any_ids:
        suggestion = "Тему не обсуждали — вывод не на чем основать."
    elif hinted:
        suggestion = "Ответ прозвучал после подсказки; уточните формулировку вывода."
    else:
        suggestion = "Оснований мало — переформулируйте вывод осторожнее."
    return InterviewerClaimAudit(
        competency_id=competency_id,
        claim=claim,
        supported=supported,
        suggestion=suggestion,
        episode_refs=match.any_ids,
    )
