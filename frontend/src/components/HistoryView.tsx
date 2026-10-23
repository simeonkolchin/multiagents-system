import { useEffect, useState } from "react";

import { api } from "../api";
import type { SessionSummary } from "../types";
import { Spinner } from "./ui";

function formatDate(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function HistoryView({
  onOpen,
}: {
  onOpen: (id: number) => void;
}) {
  const [items, setItems] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openingId, setOpeningId] = useState<number | null>(null);

  useEffect(() => {
    api
      .listSessions()
      .then(setItems)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <p className="text-sm text-rose-600">{error}</p>;
  if (!items) return <Spinner label="Загрузка истории" />;

  if (items.length === 0) {
    return (
      <div className="card p-8 text-center text-sm text-slate-500">
        Прогонов пока нет. Запустите первый разбор на вкладке «Новый разбор».
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">
        Все запуски сохраняются. Откройте любой, чтобы посмотреть карточку, версию
        для кандидата, вопросы и сравнение.
      </p>
      {items.map((item) => (
        <button
          key={item.id}
          onClick={async () => {
            setOpeningId(item.id);
            try {
              await onOpen(item.id);
            } finally {
              setOpeningId(null);
            }
          }}
          disabled={openingId !== null}
          className="card flex w-full items-center justify-between gap-4 p-5 text-left transition hover:border-brand-500 hover:shadow-md"
        >
          <div>
            <div className="font-bold">
              {item.role || "Без роли"}{" "}
              <span className="font-normal text-slate-400">{item.level}</span>
            </div>
            <div className="text-sm text-slate-500">{item.title || "—"}</div>
            <div className="mt-1 text-xs text-slate-400">
              #{item.id} · {item.competencies} компетенций · {formatDate(item.created_at)}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={`tag ${
                item.status === "ready"
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-200 text-slate-600"
              }`}
            >
              {item.status === "ready" ? "готово" : item.status}
            </span>
            {openingId === item.id ? (
              <Spinner />
            ) : (
              <span className="text-brand-600">→</span>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
