import type { Scorecard } from "../types";

export default function NextQuestionsView({ scorecard }: { scorecard: Scorecard }) {
  if (scorecard.next_questions.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        Пробелов не осталось — все компетенции закрыты.
      </p>
    );
  }
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Вопросы для следующего этапа — по одному на каждый пробел.
      </p>
      {scorecard.next_questions.map((item, i) => (
        <div key={i} className="card p-5">
          <h3 className="font-bold">{item.question}</h3>
          <p className="mt-1 text-sm text-slate-500">
            Почему неизвестно: {item.why_unknown}
          </p>
          {item.checks && (
            <p className="mt-1 text-sm text-slate-500">Что проверяем: {item.checks}</p>
          )}
          {item.signals.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {item.signals.map((s, j) => (
                <span key={j} className="tag bg-brand-50 text-brand-700">
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
