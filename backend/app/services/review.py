from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.schemas.scorecard import CompetencyFinding, ReviewIssue, ReviewResult
from app.services import heuristics


def deterministic_review(
    episodes: list[Episode],
    competencies: list[Competency],
    findings: list[CompetencyFinding],
) -> ReviewResult:
    episode_ids = {e.id for e in episodes}
    hinted = heuristics.hinted_competency_ids(episodes, competencies)
    told_only = heuristics.told_only_competency_ids(episodes, competencies)

    issues: list[ReviewIssue] = []
    reanalyze: set[str] = set()

    for finding in findings:
        cid = finding.competency_id
        for ref in finding.episode_refs:
            if ref not in episode_ids:
                issues.append(
                    ReviewIssue(
                        competency_id=cid,
                        kind="missing_episode",
                        detail=f"Ссылка на эпизод {ref} отсутствует в расшифровке.",
                    )
                )
                reanalyze.add(cid)
        if finding.sufficiency == "confirmed" and cid in hinted:
            issues.append(
                ReviewIssue(
                    competency_id=cid,
                    kind="missing_caveat",
                    detail="Вывод не учитывает, что ответ дан после подсказки.",
                )
            )
        if finding.sufficiency == "confirmed" and cid in told_only:
            issues.append(
                ReviewIssue(
                    competency_id=cid,
                    kind="missing_caveat",
                    detail="Опыт заявлен, но не продемонстрирован; нужен разбор.",
                )
            )

    for claim in heuristics.overbroad_claims(episodes, competencies):
        issues.append(
            ReviewIssue(
                competency_id=claim["competency_id"],
                kind="overbroad_conclusion",
                detail=(
                    "Оценка интервьюера шире, чем подтверждают эпизоды: "
                    f"«{claim['claim']}»."
                ),
            )
        )

    return ReviewResult(
        issues=issues,
        reanalyze=sorted(reanalyze),
        notes="Механическая проверка цитат, авторства и обоснованности выводов.",
    )


def merge_reviews(primary: ReviewResult, secondary: ReviewResult) -> ReviewResult:
    seen: set[tuple[str, str]] = set()
    merged: list[ReviewIssue] = []
    for issue in [*primary.issues, *secondary.issues]:
        key = (issue.competency_id, issue.kind)
        if key in seen:
            continue
        seen.add(key)
        merged.append(issue)
    reanalyze = sorted(set(primary.reanalyze) | set(secondary.reanalyze))
    notes = "; ".join(n for n in [primary.notes, secondary.notes] if n)
    return ReviewResult(issues=merged, reanalyze=reanalyze, notes=notes)
