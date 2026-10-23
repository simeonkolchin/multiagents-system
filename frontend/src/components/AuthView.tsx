import { useState } from "react";

import { api, setToken } from "../api";
import type { User } from "../types";
import { Spinner } from "./ui";

export default function AuthView({
  onAuth,
  onBack,
}: {
  onAuth: (user: User) => void;
  onBack: () => void;
}) {
  const [register, setRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      const result = register
        ? await api.register(email.trim().toLowerCase(), password, name)
        : await api.login(email.trim().toLowerCase(), password);
      setToken(result.access_token);
      onAuth(result.user);
    } catch (e) {
      setError(String(e).replace("Error: ", ""));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <button className="mb-4 text-sm text-slate-400 hover:text-slate-600" onClick={onBack}>
          ← на главную
        </button>
        <div className="card p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-indigo-700 font-black text-white">
              IC
            </div>
            <div>
              <h1 className="text-lg font-extrabold">
                {register ? "Регистрация" : "Вход"}
              </h1>
              <p className="text-sm text-slate-400">Interview Copilot</p>
            </div>
          </div>

          <div className="space-y-3">
            {register && (
              <div>
                <label className="label">Имя</label>
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
            )}
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Пароль</label>
              <input
                className="input"
                type="password"
                autoComplete={register ? "new-password" : "current-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
              />
            </div>
          </div>

          {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}

          <button
            className="btn-primary mt-5 w-full py-2.5"
            onClick={submit}
            disabled={busy || !email || password.length < 6}
          >
            {busy ? <Spinner /> : register ? "Создать аккаунт" : "Войти"}
          </button>

          <p className="mt-4 text-center text-sm text-slate-500">
            {register ? "Уже есть аккаунт?" : "Нет аккаунта?"}{" "}
            <button
              className="font-semibold text-brand-600 hover:underline"
              onClick={() => {
                setRegister((v) => !v);
                setError(null);
              }}
            >
              {register ? "Войти" : "Зарегистрироваться"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
