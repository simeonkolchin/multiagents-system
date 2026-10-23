import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import type { Scorecard } from "../types";

const SUFFICIENCY = [
  { key: "confirmed", label: "Подтверждено", color: "#10b981" },
  { key: "partial", label: "Частично", color: "#f59e0b" },
  { key: "not_demonstrated", label: "Не раскрыто", color: "#94a3b8" },
  { key: "no_data", label: "Данных нет", color: "#38bdf8" },
];

function Stat({ value, label, tone }: { value: number; label: string; tone: string }) {
  return (
    <div className="rounded-xl bg-slate-50 px-4 py-3">
      <div className={`text-2xl font-black ${tone}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

export default function ScorecardSummary({ scorecard }: { scorecard: Scorecard }) {
  const rows = scorecard.rows;
  const counts = SUFFICIENCY.map((s) => ({
    ...s,
    value: rows.filter((r) => r.sufficiency === s.key).length,
  }));
  const data = counts.filter((c) => c.value > 0);
  const disputed = rows.filter((r) => r.disputed).length;
  const hinted = rows.filter((r) => r.provenance === "hinted").length;
  const confirmed = counts[0].value;

  return (
    <div className="card p-6">
      <div className="grid items-center gap-6 md:grid-cols-[180px_1fr]">
        <div className="relative h-[160px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                innerRadius={52}
                outerRadius={74}
                paddingAngle={2}
                stroke="none"
              >
                {data.map((d) => (
                  <Cell key={d.key} fill={d.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-black">{rows.length}</span>
            <span className="text-xs text-slate-400">компетенций</span>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat value={confirmed} label="Подтверждено" tone="text-emerald-600" />
            <Stat value={hinted} label="После подсказки" tone="text-amber-600" />
            <Stat value={counts[3].value} label="Данных нет" tone="text-sky-600" />
            <Stat value={disputed} label="Спорных" tone="text-rose-600" />
          </div>
          <div className="flex flex-wrap gap-3">
            {counts.map((c) => (
              <span key={c.key} className="flex items-center gap-1.5 text-xs text-slate-500">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: c.color }} />
                {c.label}: {c.value}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
