import type { EvidenceKind, Provenance, Sufficiency } from "../types";

const SUFFICIENCY: Record<Sufficiency, { label: string; className: string }> = {
  confirmed: { label: "Подтверждено", className: "bg-emerald-100 text-emerald-700" },
  partial: { label: "Частично", className: "bg-amber-100 text-amber-700" },
  not_demonstrated: { label: "Не раскрыто", className: "bg-slate-200 text-slate-700" },
  no_data: { label: "Данных нет", className: "bg-sky-100 text-sky-700" },
};

const PROVENANCE: Record<Provenance, string> = {
  independent: "самостоятельно",
  clarified: "после уточнения",
  corrected: "после исправления",
  hinted: "после подсказки",
  unknown: "ход неизвестен",
};

const EVIDENCE: Record<EvidenceKind, string> = {
  demonstrated: "продемонстрировано",
  told: "со слов кандидата",
  mixed: "смешанно",
  none: "",
};

export function SufficiencyBadge({ value }: { value: Sufficiency }) {
  const item = SUFFICIENCY[value];
  return <span className={`tag ${item.className}`}>{item.label}</span>;
}

export function ProvenanceTag({ value }: { value: Provenance }) {
  const highlight = value === "hinted";
  return (
    <span
      className={`tag ${highlight ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"}`}
    >
      {PROVENANCE[value]}
    </span>
  );
}

export function EvidenceTag({ value }: { value: EvidenceKind }) {
  if (value === "none") return null;
  const highlight = value === "told";
  return (
    <span
      className={`tag ${highlight ? "bg-rose-100 text-rose-700" : "bg-indigo-100 text-indigo-700"}`}
    >
      {EVIDENCE[value]}
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      {label}
    </span>
  );
}
