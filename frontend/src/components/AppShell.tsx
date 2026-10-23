import { useState } from "react";

import { api } from "../api";
import type { Health, Interview, Session, User } from "../types";
import CandidateView from "./CandidateView";
import EvaluationView from "./EvaluationView";
import HistoryView from "./HistoryView";
import NextQuestionsView from "./NextQuestionsView";
import ScorecardView from "./ScorecardView";
import SetupView from "./SetupView";

type Mode = "setup" | "history" | "result";
type Tab = "scorecard" | "candidate" | "questions" | "evaluation";

const TABS: { id: Tab; label: string }[] = [
  { id: "scorecard", label: "Карточка" },
  { id: "candidate", label: "Для кандидата" },
  { id: "questions", label: "Следующий этап" },
  { id: "evaluation", label: "Сравнение" },
];

export default function AppShell({
  user,
  health,
  onLogout,
}: {
  user: User;
  health: Health | null;
  onLogout: () => void;
}) {
  const [session, setSession] = useState<Session | null>(null);
  const [interview, setInterview] = useState<Interview | null>(null);
  const [tab, setTab] = useState<Tab>("scorecard");
  const [mode, setMode] = useState<Mode>("setup");

  const startNew = () => {
    setSession(null);
    setInterview(null);
    setTab("scorecard");
    setMode("setup");
  };

  const openSession = async (id: number) => {
    const loaded = await api.getSession(id);
    const loadedInterview = await api.getInterview(loaded.interview_id);
    setSession(loaded);
    setInterview(loadedInterview);
    setTab("scorecard");
    setMode("result");
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-indigo-700 text-sm font-black text-white">
              IC
            </div>
            <div>
              <div className="text-sm font-extrabold leading-tight">Interview Copilot</div>
              <div className="text-xs text-slate-400">
                {health?.llm_provider === "mock" ? "demo" : health?.llm_model}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              className={mode === "setup" ? "btn-primary" : "btn-ghost"}
              onClick={startNew}
            >
              Новый разбор
            </button>
            <button
              className={mode === "history" ? "btn-primary" : "btn-ghost"}
              onClick={() => setMode("history")}
            >
              История
            </button>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-1.5">
              <span className="text-xs text-slate-500">{user.email}</span>
              <button
                className="text-xs font-semibold text-slate-400 hover:text-rose-500"
                onClick={onLogout}
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {mode === "history" ? (
          <HistoryView onOpen={openSession} />
        ) : mode === "setup" || !session || !interview ? (
          <SetupView
            onComplete={(createdSession, createdInterview) => {
              setSession(createdSession);
              setInterview(createdInterview);
              setTab("scorecard");
              setMode("result");
            }}
          />
        ) : (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold">
                  {session.scorecard.role}{" "}
                  <span className="text-slate-400">{session.scorecard.level}</span>
                </h2>
                <p className="text-sm text-slate-500">{interview.title}</p>
              </div>
              <div className="flex gap-2">
                <button className="btn-ghost" onClick={() => api.download(session.id, "docx")}>
                  Скачать .docx
                </button>
                <button className="btn-ghost" onClick={() => api.download(session.id, "md")}>
                  Скачать .md
                </button>
              </div>
            </div>

            <nav className="flex flex-wrap gap-2">
              {TABS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setTab(item.id)}
                  className={`btn ${
                    tab === item.id
                      ? "bg-brand-600 text-white"
                      : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </nav>

            {tab === "scorecard" && (
              <ScorecardView session={session} interview={interview} onUpdate={setSession} />
            )}
            {tab === "candidate" && <CandidateView scorecard={session.scorecard} />}
            {tab === "questions" && <NextQuestionsView scorecard={session.scorecard} />}
            {tab === "evaluation" && <EvaluationView sessionId={session.id} />}
          </div>
        )}
      </main>
    </div>
  );
}
