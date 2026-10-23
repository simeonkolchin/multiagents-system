import json
from typing import Any

from app.llm.client import LLMResult
from app.schemas.interview import Episode
from app.schemas.rubric import Competency
from app.services import heuristics


def _episodes(payload: dict[str, Any]) -> list[Episode]:
    return [Episode(**e) for e in payload.get("episodes", [])]


def _competencies(payload: dict[str, Any]) -> list[Competency]:
    rubric = payload.get("rubric", {})
    return [Competency(**c) for c in rubric.get("competencies", [])]


def _snippet(episode: Episode) -> str:
    text = episode.text.strip()
    if len(text) > 180:
        text = text[:177] + "..."
    return f"{episode.t}: {text}"


class MockLLMClient:
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult:
        payload = self._payload(messages)
        task = payload.get("task", "")
        handler = {
            "competency_analysis": self._competency_analysis,
            "interview_analysis": self._interview_analysis,
            "evidence_review": self._evidence_review,
            "baseline_scorecard": self._baseline_scorecard,
            "build_rubric": self._build_rubric,
        }.get(task)
        if handler is None:
            return LLMResult(content=json.dumps({"error": f"unknown task {task}"}))
        return LLMResult(content=json.dumps(handler(payload), ensure_ascii=False))

    def _payload(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        for message in reversed(messages):
            if message.get("role") != "user":
                continue
            content = message.get("content", "")
            try:
                return json.loads(content)
            except (TypeError, json.JSONDecodeError):
                return {}
        return {}

    def _competency_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        episodes = _episodes(payload)
        competencies = _competencies(payload)
        by_id = {e.id: e for e in episodes}
        hinted = heuristics.hinted_competency_ids(episodes, competencies)
        told_only = heuristics.told_only_competency_ids(episodes, competencies)

        findings = []
        for comp in competencies:
            match = heuristics.match_competency(episodes, comp)
            if not match.any_ids:
                findings.append(
                    {
                        "competency_id": comp.id,
                        "observation": "Тему не обсуждали.",
                        "episode_refs": [],
                        "interpretation": "Данных для оценки нет.",
                        "sufficiency": "no_data",
                        "confidence": 0.0,
                    }
                )
                continue
            if match.candidate_ids:
                refs = match.candidate_ids
                observation = _snippet(by_id[refs[0]])
                if comp.id in hinted:
                    sufficiency, confidence = "partial", 0.5
                    interpretation = (
                        "Решение обсудили, но ключевую идею кандидат дал после "
                        "подсказки; самостоятельный выбор подхода не проверен."
                    )
                elif comp.id in told_only:
                    sufficiency, confidence = "partial", 0.45
                    interpretation = (
                        "Кандидат заявил опыт, но самостоятельного разбора на "
                        "конкретном примере не продемонстрировал."
                    )
                else:
                    sufficiency, confidence = "confirmed", 0.8
                    interpretation = "Есть подтверждение самостоятельного понимания."
            else:
                refs = match.interviewer_ids
                observation = _snippet(by_id[refs[0]])
                sufficiency, confidence = "not_demonstrated", 0.3
                interpretation = (
                    "Тему затронул интервьюер, кандидат вклад не раскрыл."
                )
            findings.append(
                {
                    "competency_id": comp.id,
                    "observation": observation,
                    "episode_refs": refs,
                    "interpretation": interpretation,
                    "sufficiency": sufficiency,
                    "confidence": confidence,
                }
            )
        return {"findings": findings}

    def _interview_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        episodes = _episodes(payload)
        competencies = _competencies(payload)
        resume = (payload.get("resume") or "").lower()

        coverage = [
            {
                "competency_id": comp.id,
                "covered": bool(heuristics.match_competency(episodes, comp).any_ids),
                "note": "",
            }
            for comp in competencies
        ]

        hints = []
        for event in heuristics.detect_hints(episodes, competencies):
            for cid in event.competency_ids:
                hints.append(
                    {
                        "competency_id": cid,
                        "episode_refs": [
                            event.hint_episode_id,
                            event.answer_episode_id,
                        ],
                        "provenance": "hinted",
                        "note": "Ответ прозвучал после прямой подсказки интервьюера.",
                    }
                )

        evidence = []
        for ep in episodes:
            if ep.speaker != "candidate":
                continue
            kind = heuristics.evidence_kind_for(ep.text)
            if kind == "none":
                continue
            for comp in competencies:
                if heuristics._matches_competency(ep.text, comp):
                    evidence.append(
                        {
                            "competency_id": comp.id,
                            "episode_refs": [ep.id],
                            "kind": kind,
                            "note": (
                                "Заявление об опыте, а не продемонстрированное "
                                "рассуждение."
                                if kind == "told"
                                else "Продемонстрированное рассуждение."
                            ),
                        }
                    )

        demonstrated = {
            e["competency_id"] for e in evidence if e["kind"] == "demonstrated"
        }
        if resume:
            for comp in competencies:
                needles = [comp.name.lower()] + [k.lower() for k in comp.keywords]
                if comp.id in demonstrated:
                    continue
                if any(n and n in resume for n in needles):
                    evidence.append(
                        {
                            "competency_id": comp.id,
                            "episode_refs": [],
                            "kind": "told",
                            "note": "Заявлено в резюме, в интервью не продемонстрировано.",
                        }
                    )

        return {
            "coverage": coverage,
            "hints": hints,
            "evidence": evidence,
            "reasoning_notes": (
                "Разделены рассказанный опыт и продемонстрированное рассуждение; "
                "отмечены ответы после подсказок и заявления из резюме."
            ),
        }

    def _evidence_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        episodes = _episodes(payload)
        competencies = _competencies(payload)
        episode_ids = {e.id for e in episodes}
        findings = payload.get("competency_findings", [])
        hinted = heuristics.hinted_competency_ids(episodes, competencies)
        told_only = heuristics.told_only_competency_ids(episodes, competencies)

        issues = []
        reanalyze: set[str] = set()

        for finding in findings:
            cid = finding.get("competency_id", "")
            for ref in finding.get("episode_refs", []):
                if ref not in episode_ids:
                    issues.append(
                        {
                            "competency_id": cid,
                            "kind": "missing_episode",
                            "detail": f"Ссылка на эпизод {ref} отсутствует в расшифровке.",
                        }
                    )
                    reanalyze.add(cid)
            if finding.get("sufficiency") == "confirmed" and cid in hinted:
                issues.append(
                    {
                        "competency_id": cid,
                        "kind": "missing_caveat",
                        "detail": "Вывод не учитывает, что ответ дан после подсказки.",
                    }
                )
            if finding.get("sufficiency") == "confirmed" and cid in told_only:
                issues.append(
                    {
                        "competency_id": cid,
                        "kind": "missing_caveat",
                        "detail": "Опыт заявлен, но не продемонстрирован; нужен разбор.",
                    }
                )

        for claim in heuristics.overbroad_claims(episodes, competencies):
            issues.append(
                {
                    "competency_id": claim["competency_id"],
                    "kind": "overbroad_conclusion",
                    "detail": (
                        "Оценка интервьюера шире, чем подтверждают эпизоды: "
                        f"«{claim['claim']}»."
                    ),
                }
            )
            reanalyze.add(claim["competency_id"])

        return {
            "issues": issues,
            "reanalyze": sorted(reanalyze),
            "notes": "Проверены цитаты, авторство реплик и обоснованность выводов.",
        }

    def _build_rubric(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "role": "Специалист",
            "level": "middle",
            "competencies": [
                {
                    "id": "domain_knowledge",
                    "name": "Профильные знания",
                    "description": "Понимает ключевые концепции предметной области.",
                    "good_signals": ["объясняет базовые концепции", "приводит примеры"],
                    "keywords": ["алгоритм", "модель", "данные", "метрик"],
                },
                {
                    "id": "practical_skill",
                    "name": "Практические навыки",
                    "description": "Умеет применять знания на конкретных задачах.",
                    "good_signals": ["разбирает конкретный случай", "обосновывает выбор"],
                    "keywords": ["задача", "решение", "подход", "реализац"],
                },
                {
                    "id": "experience",
                    "name": "Опыт",
                    "description": "Разбирает собственный опыт с рассуждением.",
                    "good_signals": ["разбирает свой проект", "делает выводы"],
                    "keywords": ["проект", "опыт", "команда", "роль"],
                },
            ],
        }

    def _baseline_scorecard(self, payload: dict[str, Any]) -> dict[str, Any]:
        episodes = _episodes(payload)
        competencies = _competencies(payload)
        rubric = payload.get("rubric", {})
        by_id = {e.id: e for e in episodes}

        rows = []
        strengths = []
        growth = []
        for comp in competencies:
            match = heuristics.match_competency(episodes, comp)
            if match.any_ids:
                ref = (match.candidate_ids or match.interviewer_ids)[0]
                rows.append(
                    {
                        "competency_id": comp.id,
                        "name": comp.name,
                        "observation": _snippet(by_id[ref]),
                        "episode_refs": match.any_ids,
                        "conclusion": f"Кандидат показал компетенцию «{comp.name}».",
                        "sufficiency": "confirmed",
                        "provenance": "independent",
                        "evidence_kind": "none",
                        "disputed": False,
                        "dispute_reason": "",
                        "open_questions": [],
                    }
                )
                strengths.append(comp.name)
            else:
                rows.append(
                    {
                        "competency_id": comp.id,
                        "name": comp.name,
                        "observation": "",
                        "episode_refs": [],
                        "conclusion": (
                            f"Компетенция «{comp.name}» не раскрыта, вероятно "
                            "ниже ожиданий."
                        ),
                        "sufficiency": "not_demonstrated",
                        "provenance": "unknown",
                        "evidence_kind": "none",
                        "disputed": False,
                        "dispute_reason": "",
                        "open_questions": [],
                    }
                )
                growth.append(comp.name)

        return {
            "role": rubric.get("role", ""),
            "level": rubric.get("level", ""),
            "rows": rows,
            "next_questions": [],
            "candidate_view": {
                "strengths": strengths,
                "growth_areas": growth,
                "examples": [],
            },
            "disputes": [],
        }
