// ── Common ─────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// ── Role ───────────────────────────────────────────────

export interface TargetRole {
  id: string;
  role_name: string;
  role_type: string;
  description: string;
  keywords: string[];
  required_skills: string[];
  bonus_skills: string[];
  priority: number;
  status: "active" | "paused" | "deleted";
  source_jd_summary?: string;
  created_at: string;
  updated_at: string;
}

export interface RoleCreateRequest {
  role_name: string;
  role_type: string;
  description?: string;
  keywords?: string[];
  required_skills?: string[];
  bonus_skills?: string[];
  priority?: number;
  source_jd?: string;
}

// ── Resume ─────────────────────────────────────────────

export interface ResumeContent {
  summary: string;
  skills: string[];
  experiences: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  highlights: string[];
  metrics: Record<string, unknown>[];
  interview_points: string[];
}

export interface Resume {
  id: string;
  target_role_id: string;
  resume_name: string;
  resume_type: "master" | "customized";
  current_version_no: number;
  status: "draft" | "active" | "archived";
  completeness_score: number;
  match_score: number;
  content: ResumeContent;
  created_at: string;
  updated_at: string;
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_no: number;
  content: ResumeContent;
  generated_by: "user" | "agent" | "hybrid";
  source_type: "achievement" | "jd" | "manual_edit";
  source_ref_id?: string;
  summary_note?: string;
  completeness_score: number;
  match_score: number;
  created_at: string;
}

// ── Achievement ────────────────────────────────────────

export interface Achievement {
  id: string;
  source_type: string;
  title: string;
  raw_content: string;
  parsed_summary?: string;
  technical_points?: Record<string, unknown>[];
  challenges?: Record<string, unknown>[];
  solutions?: Record<string, unknown>[];
  metrics?: Record<string, unknown>[];
  interview_points?: string[];
  tags: string[];
  importance_score: number;
  created_at: string;
  updated_at: string;
}

export interface AchievementCreateRequest {
  source_type: string;
  title: string;
  raw_content: string;
  tags?: string[];
}

// ── Gap ────────────────────────────────────────────────

export interface GapItem {
  id: string;
  target_role_id: string;
  skill_name: string;
  gap_type:
    | "missing"
    | "weak_evidence"
    | "weak_expression"
    | "low_depth"
    | "low_metrics"
    | "jd_mismatch";
  priority: number;
  current_state: string;
  target_state: string;
  evidence: Record<string, unknown>;
  improvement_plan: Record<string, unknown>;
  progress: number;
  status: "open" | "in_progress" | "closed";
  created_at: string;
  updated_at: string;
}

// ── JD ─────────────────────────────────────────────────

export interface JDParsed {
  role_name: string;
  keywords: string[];
  required_skills: string[];
  bonus_items: string[];
  style: Record<string, unknown>;
}

export interface JDTailorResult {
  resume: ResumeContent;
  ability_match_score: number;
  resume_match_score: number;
  readiness_score: number;
  recommendation:
    | "apply_now"
    | "tune_then_apply"
    | "fill_gap_first"
    | "not_recommended";
  missing_items: string[];
  optimization_notes: string[];
}

// ── Suggestion ─────────────────────────────────────────

export interface UpdateSuggestion {
  id: string;
  suggestion_type: "resume_update" | "gap_update" | "jd_tune";
  target_role_id: string;
  resume_id?: string;
  title: string;
  content: Record<string, unknown>;
  impact_score: Record<string, unknown>;
  risk_level: "low" | "medium" | "high";
  status: "pending" | "accepted" | "rejected" | "applied";
  created_at: string;
  updated_at: string;
}
