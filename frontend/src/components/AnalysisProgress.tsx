import { useEffect, useState } from "react";

const STAGES = [
  { title: "Аналитик компетенций", hint: "сопоставляет ответы с рубрикой" },
  { title: "Аналитик интервью", hint: "ищет подсказки и ход решения" },
  { title: "Ревизор оснований", hint: "проверяет цитаты и выводы" },
  { title: "Сборка карточки", hint: "формирует итоговую карточку" },
];

export default function AnalysisProgress() {
  const [active, setActive] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const stage = setInterval(
      () => setActive((v) => Math.min(v + 1, STAGES.length - 1)),
      9000,
    );
    const timer = setInterval(() => setElapsed((v) => v + 1), 1000);
    return () => {
      clearInterval(stage);
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <h3 className="font-bold">Идёт мультиагентный разбор</h3>
        <span className="text-sm tabular-nums text-slate-400">{elapsed} c</span>
      </div>
      <ol className="mt-4 space-y-3">
        {STAGES.map((stage, index) => {
          const done = index < active;
          const current = index === active;
          return (
            <li key={stage.title} className="flex items-center gap-3">
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                  done
                    ? "bg-emerald-500 text-white"
                    : current
                      ? "bg-brand-600 text-white"
                      : "bg-slate-200 text-slate-500"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>
              <div className="flex-1">
                <div
                  className={`text-sm font-semibold ${current ? "text-ink" : "text-slate-500"}`}
                >
                  {stage.title}
                </div>
                <div className="text-xs text-slate-400">{stage.hint}</div>
              </div>
              {current && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
