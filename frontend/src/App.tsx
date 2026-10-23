import { useEffect, useState } from "react";

import { api, getToken, setToken, setUnauthorizedHandler } from "./api";
import AppShell from "./components/AppShell";
import AuthView from "./components/AuthView";
import Landing from "./components/Landing";
import type { Health, User } from "./types";

type Route = "landing" | "auth" | "app";

export default function App() {
  const [route, setRoute] = useState<Route>("landing");
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => undefined);
    setUnauthorizedHandler(() => {
      setUser(null);
      setRoute("auth");
    });
    if (getToken()) {
      api
        .me()
        .then((u) => {
          setUser(u);
          setRoute("app");
        })
        .catch(() => setToken(null))
        .finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, []);

  if (!ready) {
    return <div className="min-h-screen bg-slate-50" />;
  }

  if (route === "app" && user) {
    return (
      <AppShell
        user={user}
        health={health}
        onLogout={() => {
          setToken(null);
          setUser(null);
          setRoute("landing");
        }}
      />
    );
  }

  if (route === "auth") {
    return (
      <AuthView
        onAuth={(u) => {
          setUser(u);
          setRoute("app");
        }}
        onBack={() => setRoute("landing")}
      />
    );
  }

  return <Landing onStart={() => setRoute(user ? "app" : "auth")} />;
}
