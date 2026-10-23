import type {
  ClaimAudit,
  Competency,
  DemoDataset,
  EvaluationResult,
  Health,
  Interview,
  Rubric,
  RubricDraft,
  Session,
  SessionSummary,
  TranscribeResult,
  TokenResponse,
  User,
} from "./types";

const BASE = "/api";
const TOKEN_KEY = "ic_token";

let token: string | null = localStorage.getItem(TOKEN_KEY);
let onUnauthorized: () => void = () => undefined;

export function setToken(value: string | null): void {
  token = value;
  try {
    if (value) localStorage.setItem(TOKEN_KEY, value);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function getToken(): string | null {
  return token;
}

export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn;
}

function authHeaders(): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    setToken(null);
    onUnauthorized();
    throw new Error("Сессия истекла, войдите снова");
  }
  if (!response.ok) {
    throw new Error((await response.text()) || `Ошибка ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options?.headers || {}),
    },
  });
  return handle<T>(response);
}

async function upload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  return handle<T>(response);
}

export const api = {
  health: () => request<Health>("/health"),

  register: (email: string, password: string, name: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/auth/me"),

  demoDataset: () => request<DemoDataset>("/demo/dataset"),

  extractFile: (file: File) => upload<{ text: string }>("/extract", file),

  generateRubric: (vacancy: string) =>
    request<RubricDraft>("/rubrics/generate", {
      method: "POST",
      body: JSON.stringify({ vacancy }),
    }),

  getRubric: (id: number) => request<Rubric>(`/rubrics/${id}`),
  getInterview: (id: number) => request<Interview>(`/interviews/${id}`),

  createRubric: (payload: { role: string; level: string; competencies: Competency[] }) =>
    request<Rubric>("/rubrics", { method: "POST", body: JSON.stringify(payload) }),

  createInterview: (payload: { title: string; raw_text: string }) =>
    request<Interview>("/interviews", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  createSession: (payload: {
    rubric_id: number;
    interview_id: number;
    resume?: string;
  }) =>
    request<Session>("/sessions", { method: "POST", body: JSON.stringify(payload) }),

  getSession: (id: number) => request<Session>(`/sessions/${id}`),
  listSessions: () => request<SessionSummary[]>("/sessions"),

  editConclusion: (id: number, competency_id: string, conclusion: string) =>
    request<Session>(`/sessions/${id}/edit`, {
      method: "POST",
      body: JSON.stringify({ competency_id, conclusion }),
    }),

  dispute: (id: number, competency_id: string, reason: string) =>
    request<Session>(`/sessions/${id}/dispute`, {
      method: "POST",
      body: JSON.stringify({ competency_id, reason }),
    }),

  audit: (id: number, competency_id: string, claim: string) =>
    request<ClaimAudit>(`/sessions/${id}/audit`, {
      method: "POST",
      body: JSON.stringify({ competency_id, claim }),
    }),

  evaluate: (id: number) => request<EvaluationResult>(`/sessions/${id}/evaluation`),

  transcribe: (file: File) => upload<TranscribeResult>("/transcribe", file),

  download: async (id: number, kind: "docx" | "md"): Promise<void> => {
    const response = await fetch(`${BASE}/sessions/${id}/export.${kind}`, {
      headers: authHeaders(),
    });
    if (!response.ok) throw new Error(`Ошибка ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `scorecard_${id}.${kind}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },
};
