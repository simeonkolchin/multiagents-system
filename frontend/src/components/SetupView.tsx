import { useRef, useState } from "react";

import { api } from "../api";
import type { Competency, Interview, Session } from "../types";
import AnalysisProgress from "./AnalysisProgress";
import { Spinner } from "./ui";

function emptyCompetency(index: number): Competency {
  return {
    id: `comp_${index}`,
    name: "",
    description: "",
    good_signals: [],
    keywords: [],
  };
}

function FileButton({
  accept,
  onFile,
  label,
  busy,
}: {
  accept: string;
  onFile: (file: File) => void;
  label: string;
  busy: boolean;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = "";
        }}
      />
      <button
        type="button"
        className="btn-ghost"
        onClick={() => ref.current?.click()}
        disabled={busy}
      >
        {busy ? <Spinner /> : label}
      </button>
    </>
  );
}

export default function SetupView({
  onComplete,
}: {
  onComplete: (session: Session, interview: Interview) => void;
}) {
  const [role, setRole] = useState("");
  const [level, setLevel] = useState("");
  const [competencies, setCompetencies] = useState<Competency[]>([emptyCompetency(1)]);
  const [vacancy, setVacancy] = useState("");
  const [title, setTitle] = useState("Интервью");
  const [transcript, setTranscript] = useState("");
  const [resume, setResume] = useState("");
  const [mode, setMode] = useState<"text" | "media">("text");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const update = (index: number, patch: Partial<Competency>) =>
    setCompetencies((prev) => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)));

  const guard = async (key: string, fn: () => Promise<void>) => {
    setError(null);
    setBusy(key);
    try {
      await fn();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  };

  const loadDemo = () =>
    guard("demo", async () => {
      const d = await api.demoDataset();
      setRole(d.role);
      setLevel(d.level);
      setCompetencies(d.competencies);
      setVacancy(d.vacancy);
      setTitle(d.title);
      setTranscript(d.transcript);
      setResume(d.resume);
      setMode("text");
    });

  const generateRubric = () =>
    guard("gen", async () => {
      const draft = await api.generateRubric(vacancy);
      setRole(draft.role);
      setLevel(draft.level);
      setCompetencies(
        draft.competencies.length ? draft.competencies : [emptyCompetency(1)],
      );
    });

  const run = () =>
    guard("run", async () => {
      const rubric = await api.createRubric({
        role,
        level,
        competencies: competencies.filter((c) => c.name.trim()),
      });
      const interview = await api.createInterview({
        title: title || "Интервью",
        raw_text: transcript,
      });
      const session = await api.createSession({
        rubric_id: rubric.id,
        interview_id: interview.id,
        resume,
      });
      onComplete(session, interview);
    });

  const canRun =
    transcript.trim().length > 0 && competencies.some((c) => c.name.trim().length > 0);

  if (busy === "run") {
    return (
      <div className="mx-auto max-w-xl">
        <AnalysisProgress />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <h2 className="text-lg font-bold">Новый разбор интервью</h2>
          <p className="text-sm text-slate-500">
            Заполните вакансию, рубрику, расшифровку и резюме — или загрузите готовый
            пример одним кликом.
          </p>
        </div>
        <button className="btn-primary" onClick={loadDemo} disabled={busy !== null}>
          {busy === "demo" ? <Spinner label="Загрузка" /> : "✨ Загрузить демо"}
        </button>
      </div>

      <section className="card space-y-3 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold">1. Вакансия (необязательно)</h3>
          <div className="flex gap-2">
            <FileButton
              accept=".pdf,.txt,.md,text/plain,application/pdf"
              label="Загрузить PDF / текст"
              busy={busy === "vac-file"}
              onFile={(file) =>
                guard("vac-file", async () => {
                  const r = await api.extractFile(file);
                  setVacancy(r.text);
                })
              }
            />
            <button
              className="btn-ghost"
              onClick={generateRubric}
              disabled={busy !== null || !vacancy.trim()}
            >
              {busy === "gen" ? <Spinner /> : "Сгенерировать рубрику"}
            </button>
          </div>
        </div>
        <p className="text-sm text-slate-500">
          Вставьте описание вакансии или загрузите файл — система сама предложит
          рубрику компетенций, её можно отредактировать ниже.
        </p>
        <textarea
          className="input"
          rows={4}
          placeholder="Описание вакансии: обязанности, требования…"
          value={vacancy}
          onChange={(e) => setVacancy(e.target.value)}
        />
      </section>

      <section className="card space-y-4 p-6">
        <h3 className="text-base font-bold">2. Рубрика роли</h3>
        <p className="rounded-xl bg-brand-50 p-3 text-sm text-slate-600">
          <b>Роль</b> и <b>уровень</b> — какую позицию закрываете. <b>Компетенция</b> —
          отдельный навык, который проверяете. Для каждой: короткое описание, признаки
          хорошего ответа и ключевые слова, по которым система находит тему в
          расшифровке.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Роль</label>
            <input
              className="input"
              placeholder="например, Data Scientist"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Уровень</label>
            <input
              className="input"
              placeholder="например, middle"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-4">
          {competencies.map((comp, index) => (
            <div key={index} className="rounded-xl border border-slate-200 p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wide text-slate-400">
                  Компетенция {index + 1}
                </span>
                <button
                  className="text-sm text-slate-400 hover:text-rose-500"
                  onClick={() =>
                    setCompetencies((prev) => prev.filter((_, i) => i !== index))
                  }
                >
                  Удалить
                </button>
              </div>
              <label className="label">Название</label>
              <input
                className="input"
                placeholder="например, Валидация и метрики"
                value={comp.name}
                onChange={(e) => update(index, { name: e.target.value })}
              />
              <label className="label mt-2">Описание</label>
              <textarea
                className="input"
                rows={2}
                placeholder="что именно проверяем в этой компетенции"
                value={comp.description}
                onChange={(e) => update(index, { description: e.target.value })}
              />
              <label className="label mt-2">Ключевые слова (через запятую)</label>
              <input
                className="input"
                placeholder="кросс-валидация, roc-auc, переобучение"
                value={comp.keywords.join(", ")}
                onChange={(e) =>
                  update(index, {
                    keywords: e.target.value
                      .split(",")
                      .map((k) => k.trim())
                      .filter(Boolean),
                  })
                }
              />
              <label className="label mt-2">Признаки хорошего ответа (по строке)</label>
              <textarea
                className="input"
                rows={2}
                placeholder={"предлагает baseline\nиспользует отложенную выборку"}
                value={comp.good_signals.join("\n")}
                onChange={(e) =>
                  update(index, {
                    good_signals: e.target.value
                      .split("\n")
                      .map((k) => k.trim())
                      .filter(Boolean),
                  })
                }
              />
            </div>
          ))}
          <button
            className="btn-ghost w-full"
            onClick={() =>
              setCompetencies((prev) => [...prev, emptyCompetency(prev.length + 1)])
            }
          >
            + Добавить компетенцию
          </button>
        </div>
      </section>

      <section className="card space-y-4 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold">3. Интервью</h3>
          <div className="flex gap-2">
            <button
              className={`btn ${mode === "text" ? "bg-brand-600 text-white" : "btn-ghost"}`}
              onClick={() => setMode("text")}
            >
              Текст
            </button>
            <button
              className={`btn ${mode === "media" ? "bg-brand-600 text-white" : "btn-ghost"}`}
              onClick={() => setMode("media")}
            >
              Видео / аудио
            </button>
          </div>
        </div>

        {mode === "media" && (
          <div className="rounded-xl border-2 border-dashed border-slate-300 p-5 text-center">
            <p className="mb-3 text-sm text-slate-500">
              Загрузите запись — система распознает речь и расставит таймкоды
            </p>
            <FileButton
              accept="audio/*,video/*"
              label="Выбрать видео / аудио"
              busy={busy === "transcribe"}
              onFile={(file) =>
                guard("transcribe", async () => {
                  const r = await api.transcribe(file);
                  setTranscript(r.text);
                  setTitle(file.name);
                })
              }
            />
          </div>
        )}

        <div>
          <label className="label">Название</label>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="label">Расшифровка</label>
          <textarea
            className="input font-mono text-xs"
            rows={12}
            placeholder="[00:30] Интервьюер: ..."
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
          />
        </div>
      </section>

      <section className="card space-y-3 p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold">4. Резюме кандидата (необязательно)</h3>
          <FileButton
            accept=".pdf,.txt,.md,text/plain,application/pdf"
            label="Загрузить PDF / текст"
            busy={busy === "resume-file"}
            onFile={(file) =>
              guard("resume-file", async () => {
                const r = await api.extractFile(file);
                setResume(r.text);
              })
            }
          />
        </div>
        <p className="text-sm text-slate-500">
          Резюме учитывается как заявленный опыт: система отделит его от того, что
          кандидат реально продемонстрировал на интервью.
        </p>
        <textarea
          className="input"
          rows={5}
          placeholder="Вставьте текст резюме или загрузите PDF"
          value={resume}
          onChange={(e) => setResume(e.target.value)}
        />
      </section>

      <div className="sticky bottom-4">
        <button
          className="btn-primary w-full py-3 text-base shadow-lg"
          onClick={run}
          disabled={!canRun || busy !== null}
        >
          Запустить анализ
        </button>
        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
      </div>
    </div>
  );
}
