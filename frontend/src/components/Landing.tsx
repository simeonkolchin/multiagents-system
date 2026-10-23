const FEATURES = [
  {
    title: "Основания у каждого вывода",
    text: "Каждая оценка привязана к эпизоду интервью с таймкодом — видно, на чём она держится.",
  },
  {
    title: "Подсказки и ход решения",
    text: "Система различает, пришёл ли кандидат к ответу сам или после подсказки интервьюера.",
  },
  {
    title: "Рассказал ≠ показал",
    text: "Отделяет заявленный в резюме опыт от продемонстрированного на интервью.",
  },
  {
    title: "Аудит выводов интервьюера",
    text: "Проверяет, не шире ли оценка, чем подтверждают эпизоды, и помечает спорное.",
  },
  {
    title: "Пробелы, а не низкие оценки",
    text: "Непроверенная компетенция — это «данных нет», а не плохая оценка.",
  },
  {
    title: "Вопросы для следующего этапа",
    text: "Готовые вопросы, чтобы закрыть именно те пробелы, что остались после интервью.",
  },
];

const STEPS = [
  "Загрузите вакансию, интервью (текст, видео или аудио) и резюме",
  "Три агента независимо анализируют и проверяют друг друга",
  "Получаете карточку с основаниями, сравнение и документ для скачивания",
];

export default function Landing({ onStart }: { onStart: () => void }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-indigo-700 text-sm font-black text-white">
            IC
          </div>
          <span className="font-extrabold">Interview Copilot</span>
        </div>
        <button className="btn-primary" onClick={onStart}>
          Войти
        </button>
      </header>

      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-[-10rem] h-[32rem] w-[32rem] -translate-x-1/2 rounded-full bg-brand-200/50 blur-3xl" />
          <div className="absolute right-[-8rem] top-10 h-80 w-80 rounded-full bg-indigo-200/40 blur-3xl" />
        </div>
        <div className="mx-auto max-w-4xl px-6 py-24 text-center">
          <span className="tag bg-brand-100 text-brand-700">
            Мультиагентная система для интервью
          </span>
          <h1 className="mt-5 text-5xl font-black leading-tight tracking-tight text-ink">
            Превращаем интервью в{" "}
            <span className="bg-gradient-to-r from-brand-600 to-indigo-600 bg-clip-text text-transparent">
              обоснованную обратную связь
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
            Не очередной суммаризатор. Система сопоставляет ответы с требованиями роли,
            показывает основания каждого вывода и проверяет их обоснованность.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <button className="btn-primary px-6 py-3 text-base shadow-lg" onClick={onStart}>
              Перейти к использованию →
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid gap-5 md:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="card p-6">
              <h3 className="font-bold text-ink">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-24">
        <div className="card overflow-hidden">
          <div className="bg-gradient-to-br from-brand-600 to-indigo-700 p-8 text-white">
            <h2 className="text-2xl font-bold">Как это работает</h2>
          </div>
          <div className="grid gap-6 p-8 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <div key={i} className="flex gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 font-bold text-brand-700">
                  {i + 1}
                </span>
                <p className="text-sm text-slate-600">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-400">
        Interview Copilot — учебный проект по мультиагентным системам
      </footer>
    </div>
  );
}
