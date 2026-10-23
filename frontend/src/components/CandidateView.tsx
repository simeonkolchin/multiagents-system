import type { Scorecard } from "../types";

function Column({ title, items, tone }: { title: string; items: string[]; tone: string }) {
  return (
    <div className="card p-5">
      <h3 className={`text-sm font-bold uppercase tracking-wide ${tone}`}>{title}</h3>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-400">—</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {items.map((item, i) => (
            <li key={i} className="rounded-lg bg-slate-50 p-2">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function CandidateView({ scorecard }: { scorecard: Scorecard }) {
  const view = scorecard.candidate_view;
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Согласованная версия для кандидата: только то, что подтверждено
        основаниями. Утверждает интервьюер.
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        <Column title="Сильные стороны" items={view.strengths} tone="text-emerald-600" />
        <Column title="Зоны роста" items={view.growth_areas} tone="text-amber-600" />
        <Column title="Примеры" items={view.examples} tone="text-brand-600" />
      </div>
    </div>
  );
}
