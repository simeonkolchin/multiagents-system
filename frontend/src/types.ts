export type Sufficiency = "confirmed" | "partial" | "not_demonstrated" | "no_data";
export type Provenance =
  | "independent"
  | "clarified"
  | "corrected"
  | "hinted"
  | "unknown";
export type EvidenceKind = "demonstrated" | "told" | "mixed" | "none";

export interface Competency {
  id: string;
  name: string;
  description: string;
  good_signals: string[];
  keywords: string[];
}

export interface Rubric {
  id: number;
  role: string;
  level: string;
  competencies: Competency[];
}

export interface Episode {
  id: number;
  t: string;
  speaker: "interviewer" | "candidate" | "unknown";
  text: string;
}

export interface Interview {
  id: number;
  title: string;
  episodes: Episode[];
}

export interface ScorecardRow {
  competency_id: string;
  name: string;
  observation: string;
  episode_refs: number[];
  conclusion: string;
  sufficiency: Sufficiency;
  provenance: Provenance;
  evidence_kind: EvidenceKind;
  disputed: boolean;
  dispute_reason: string;
  open_questions: string[];
}

export interface NextQuestion {
  competency_id: string;
  question: string;
  checks: string;
  why_unknown: string;
  signals: string[];
}

export interface CandidateView {
  strengths: string[];
  growth_areas: string[];
  examples: string[];
}

export interface ReviewIssue {
  competency_id: string;
  kind: string;
  detail: string;
}

export interface Scorecard {
  role: string;
  level: string;
  rows: ScorecardRow[];
  next_questions: NextQuestion[];
  candidate_view: CandidateView;
  disputes: ReviewIssue[];
}

export interface Session {
  id: number;
  rubric_id: number;
  interview_id: number;
  status: string;
  scorecard: Scorecard;
  trace: Record<string, unknown>;
}

export interface ApproachMetrics {
  approach: string;
  unsupported_conclusions: number;
  preserved_caveats: number;
  estimated_human_edits: number;
  rows: number;
  flagged_disputes: number;
}

export interface EvaluationResult {
  multi_agent: ApproachMetrics;
  baseline: ApproachMetrics;
  multi_agent_scorecard: Scorecard;
  baseline_scorecard: Scorecard;
  summary: string;
}

export interface ClaimAudit {
  competency_id: string;
  claim: string;
  supported: boolean;
  suggestion: string;
  episode_refs: number[];
}

export interface TranscribeResult {
  text: string;
  language: string;
  duration: number;
  episodes: Episode[];
}

export interface SessionSummary {
  id: number;
  rubric_id: number;
  interview_id: number;
  status: string;
  role: string;
  level: string;
  title: string;
  competencies: number;
  created_at: string | null;
}

export interface RubricDraft {
  role: string;
  level: string;
  competencies: Competency[];
}

export interface DemoDataset {
  role: string;
  level: string;
  competencies: Competency[];
  title: string;
  transcript: string;
  resume: string;
  vacancy: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Health {
  status: string;
  llm_provider: string;
  llm_model: string;
  transcribe_provider: string;
  transcribe_model: string;
}
