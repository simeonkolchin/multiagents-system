import { useState } from "react";

import { api } from "../api";
import type { ApproachMetrics, EvaluationResult } from "../types";
import { Spinner } from "./ui";

const METRICS: { key: keyof ApproachMetrics; label: string; better: "low" | "high" }[] = [
  { key: "unsupported_conclusions", label: "Неподтверждённые выводы", better: "low" },
  { key: "preserved_caveats", label: "Сохранённые оговорки", better: "high" },
  { key: "estimated_human_edits", label: "Правок человеком", better: "low" },
  { key: "flagged_disputes", label: "Явно помечено спорных", better: "high" },
];

function Bar({ value, max, good }: { value: number; max: number; good: boolean }) {
  const width = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="h-2 w-full rounded-full bg-slate-100">
      <div
        className={`h-2 rounded-full ${good ? "bg-emerald-500" : "bg-rose-400"}`}
        style={{ width: `${Math.max(width, value > 0 ? 8 : 0)}%` }}
      />
    </div>
  );
}

export default function EvaluationView({ sessionId }: { sessionId: number }) {
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.evaluate(sessionId));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Сравнение мультиагентной системы с одним сильным LLM-вызовом на том же
        интервью и рубрике.
      </p>
      <button className="btn-primary" onClick={run} disabled={busy}>
        {busy ? <Spinner label="Считаем" /> : "Сравнить подходы"}
      </button>
      {error && <p className="text-sm text-rose-600">{error}</p>}

      {result && (
        <>
          <div className="card p-5 text-sm text-slate-700">{result.summary}</div>
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">Метрика</th>
                  <th className="px-5 py-3">Мультиагент</th>
                  <th className="px-5 py-3">Один вызов</th>
                </tr>
              </thead>
              <tbody>
                {METRICS.map((metric) => {
                  const ma = result.multi_agent[metric.key] as number;
                  const base = result.baseline[metric.key] as number;
                  const max = Math.max(ma, base, 1);
                  const maGood =
                    metric.better === "low" ? ma <= base : ma >= base;
                  const baseGood =
                    metric.better === "low" ? base <= ma : base >= ma;
                  return (
                    <tr key={metric.key} className="border-t border-slate-100">
                      <td className="px-5 py-3 font-medium">{metric.label}</td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <span className="w-6 font-bold">{ma}</span>
                          <Bar value={ma} max={max} good={maGood} />
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <span className="w-6 font-bold">{base}</span>
                          <Bar value={base} max={max} good={baseGood} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
