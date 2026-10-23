import { useLayoutEffect, useRef, useState } from "react";

import { api } from "../api";
import type { ClaimAudit, Episode, Interview, ScorecardRow, Session } from "../types";
import ScorecardSummary from "./ScorecardSummary";
import { EvidenceTag, ProvenanceTag, Spinner, SufficiencyBadge } from "./ui";

function AutoTextarea({
  value,
  onChange,
  className = "",
}: {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const resize = () => {
    const el = ref.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  };
  useLayoutEffect(resize, [value]);
  return (
    <textarea
      ref={ref}
      className={`input resize-none overflow-hidden leading-relaxed ${className}`}
      value={value}
      rows={2}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

function EpisodeRefs({ refs, map }: { refs: number[]; map: Map<number, Episode> }) {
  const [open, setOpen] = useState(false);
  const items = refs.map((id) => map.get(id)).filter(Boolean) as Episode[];
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <button
        className="text-xs font-semibold text-brand-600 hover:underline"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "Скрыть основания" : `Показать основания (${items.length})`}
      </button>
      {open && (
        <ul className="mt-2 space-y-2">
          {items.map((ep) => (
            <li key={ep.id} className="rounded-lg bg-slate-50 p-3 text-sm">
              <span className="font-semibold text-slate-500">
                {ep.t} ·{" "}
                {ep.speaker === "candidate"
                  ? "Кандидат"
                  : ep.speaker === "interviewer"
                    ? "Интервьюер"
                    : "Спикер"}
              </span>
              <p className="mt-1 text-slate-700">{ep.text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function RowCard({
  row,
  episodeMap,
  sessionId,
  onUpdate,
}: {
  row: ScorecardRow;
  episodeMap: Map<number, Episode>;
  sessionId: number;
  onUpdate: (session: Session) => void;
}) {
  const [conclusion, setConclusion] = useState(row.conclusion);
  const [reason, setReason] = useState("");
  const [showDispute, setShowDispute] = useState(false);
  const [claim, setClaim] = useState("");
  const [audit, setAudit] = useState<ClaimAudit | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const save = async () => {
    setBusy("save");
    try {
      onUpdate(await api.editConclusion(sessionId, row.competency_id, conclusion));
    } finally {
      setBusy(null);
    }
  };

  const dispute = async () => {
    setBusy("dispute");
    try {
      onUpdate(await api.dispute(sessionId, row.competency_id, reason));
      setShowDispute(false);
      setReason("");
    } finally {
      setBusy(null);
    }
  };

  const runAudit = async () => {
    setBusy("audit");
    try {
      setAudit(await api.audit(sessionId, row.competency_id, claim));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-bold">{row.name}</h3>
        <div className="flex flex-wrap gap-1.5">
          <SufficiencyBadge value={row.sufficiency} />
          <ProvenanceTag value={row.provenance} />
          <EvidenceTag value={row.evidence_kind} />
        </div>
      </div>

      {row.observation && (
        <p className="mt-3 whitespace-pre-wrap text-[15px] leading-relaxed text-slate-600">
          {row.observation}
        </p>
      )}

      <EpisodeRefs refs={row.episode_refs} map={episodeMap} />

      {row.disputed && (
        <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          ⚠ Спорный вывод: {row.dispute_reason}
        </div>
      )}

      <div className="mt-4">
        <label className="label">Вывод (можно отредактировать)</label>
        <AutoTextarea value={conclusion} onChange={setConclusion} />
      </div>

      {row.open_questions.length > 0 && (
        <ul className="mt-3 list-inside list-disc text-sm text-slate-500">
          {row.open_questions.map((q, i) => (
            <li key={i}>{q}</li>
          ))}
        </ul>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          className="btn-primary"
          onClick={save}
          disabled={busy !== null || conclusion === row.conclusion}
        >
          {busy === "save" ? <Spinner /> : "Сохранить вывод"}
        </button>
        <button className="btn-ghost" onClick={() => setShowDispute((v) => !v)}>
          Оспорить интерпретацию
        </button>
      </div>

      {showDispute && (
        <div className="mt-3 space-y-2">
          <textarea
            className="input"
            rows={2}
            placeholder="Почему вывод спорный?"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <button className="btn-ghost" onClick={dispute} disabled={busy !== null}>
            {busy === "dispute" ? <Spinner /> : "Пометить спорным"}
          </button>
        </div>
      )}

      <div className="mt-4 rounded-xl bg-slate-50 p-3">
        <label className="label">Аудит вывода интервьюера</label>
        <div className="flex gap-2">
          <input
            className="input"
            placeholder="напр. слабый system design"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
          />
          <button
            className="btn-ghost shrink-0"
            onClick={runAudit}
            disabled={busy !== null || !claim.trim()}
          >
            {busy === "audit" ? <Spinner /> : "Проверить"}
          </button>
        </div>
        {audit && (
          <div
            className={`mt-2 rounded-lg p-3 text-sm ${
              audit.supported
                ? "bg-emerald-50 text-emerald-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {audit.supported ? "Подтверждается эпизодами. " : "Недостаточно оснований. "}
            {audit.suggestion}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ScorecardView({
  session,
  interview,
  onUpdate,
}: {
  session: Session;
  interview: Interview;
  onUpdate: (session: Session) => void;
}) {
  const episodeMap = new Map(interview.episodes.map((e) => [e.id, e]));
  return (
    <div className="space-y-5">
      <ScorecardSummary scorecard={session.scorecard} />
      <div className="grid items-start gap-5 md:grid-cols-2">
        {session.scorecard.rows.map((row) => (
          <RowCard
            key={row.competency_id}
            row={row}
            episodeMap={episodeMap}
            sessionId={session.id}
            onUpdate={onUpdate}
          />
        ))}
      </div>
    </div>
  );
}
