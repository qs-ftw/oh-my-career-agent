// ── Common ─────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// ── Profile ────────────────────────────────────────────

export interface ProfileContact {
  email: string;
  phone: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  location: string;
}

export interface CareerProfile {
  id: string;
  name: string;
  headline: string;
  email: string;
  phone: string;
  linkedin_url: string;
  portfolio_url: string;
  github_url: string;
  location: string;
  professional_summary: string;
  skill_categories: Record<string, string[]>;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpsertRequest {
  name: string;
  headline: string;
  email: string;
  phone: string;
  linkedin_url: string;
  portfolio_url: string;
  github_url: string;
  location: string;
  professional_summary: string;
  skill_categories: Record<string, string[]>;
}

export interface ProfileCompleteness {
  total_fields: number;
  filled_fields: number;
  completeness_pct: number;
  missing_high_value: string[];
  missing_low_value: string[];
}

export interface ResumeImportResult {
  profile: CareerProfile;
  work_experiences: Array<{
    id: string;
    company_name: string;
    role_title: string;
    action: "created" | "updated";
  }>;
  projects: Array<{
    id: string;
    name: string;
    company_name: string | null;
    action: "created" | "updated";
  }>;
  achievements: Array<{
    id: string;
    title: string;
    action: "created";
  }>;
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
  skip_init?: boolean;
}

export interface RoleAnalysisResponse {
  role_name: string;
  role_type: string;
  description: string;
  required_skills: string[];
  bonus_skills: string[];
  keywords: string[];
}

// ── Resume ─────────────────────────────────────────────

export interface ContactInfo {
  email: string;
  phone: string;
  linkedin_url: string;
  portfolio_url: string;
  location: string;
}

export interface ResumeContent {
  summary: string;
  skills: string[];
  experiences: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  highlights: string[];
  metrics: Record<string, unknown>[];
  interview_points: string[];
  contact: ContactInfo;
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
  profile_id: string;
  project_id: string | null;
  work_experience_id: string | null;
  education_id: string | null;
  title: string;
  raw_content: string;
  parsed_data: Record<string, unknown> | null;
  tags: string[];
  importance_score: number;
  source_type: string;
  status: "raw" | "analyzed" | "applied";
  date_occurred: string | null;
  analysis_error?: string;
  analysis_chat: Array<{ role: "ai" | "user"; content: string }> | null;
  enrichment_suggestions: Array<{ suggestion: string; category: string }> | null;
  polished_content: { narrative: string; bullets: string[] } | null;
  display_format: "raw" | "narrative" | "bullets";
  created_at: string;
}

export interface AchievementCreateRequest {
  source_type: string;
  title: string;
  raw_content: string;
  tags?: string[];
  project_id?: string | null;
  work_experience_id?: string | null;
  education_id?: string | null;
  date_occurred?: string | null;
}

// ── Work Experience ─────────────────────────────────────

export interface WorkExperience {
  id: string;
  profile_id: string;
  company_name: string;
  company_url: string;
  location: string;
  role_title: string;
  start_date: string;
  end_date: string | null;
  description: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// ── Project ─────────────────────────────────────────────

export interface Project {
  id: string;
  profile_id: string;
  work_experience_id: string | null;
  education_id: string | null;
  name: string;
  description: string;
  tech_stack: string[];
  url: string;
  start_date: string | null;
  end_date: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// ── Education ─────────────────────────────────────────────

export interface Education {
  id: string;
  profile_id: string;
  institution_name: string;
  institution_url: string;
  degree: string;
  field_of_study: string;
  location: string;
  start_date: string;
  end_date: string | null;
  gpa: string;
  description: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
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
  review_artifact?: JDReviewArtifact;
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

export interface JDReviewArtifact {
  role_summary: Record<string, unknown>;
  evidence_matrix: Record<string, unknown>[];
  gap_analysis: Record<string, unknown>[];
  personalization_plan: Record<string, unknown>[];
  interview_plan: Record<string, unknown>[];
  recommendation_summary: Record<string, unknown>;
}

// ── Suggestion ─────────────────────────────────────────

export interface UpdateSuggestion {
  id: string;
  suggestion_type: "resume_update" | "gap_update" | "jd_tune";
  target_role_id: string;
  resume_id?: string;
  source_achievement_id?: string;
  title: string;
  content: Record<string, unknown>;
  impact_score: number;
  risk_level: "low" | "medium" | "high";
  status: "pending" | "accepted" | "rejected" | "applied";
  applied_resume_version_id?: string;
  apply_result?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ── Story ──────────────────────────────────────────────

export interface InterviewStory {
  id: string;
  title: string;
  theme: string;
  source_type: string;
  source_ref_id?: string;
  story_json: Record<string, unknown>;
  best_for_json: string[];
  confidence_score: number;
  created_at: string;
  updated_at: string;
}

// ── Dashboard ──────────────────────────────────────────

export interface DashboardStats {
  role_count: number;
  resume_count: number;
  high_priority_gap_count: number;
  recent_achievement_count: number;
  pending_suggestion_count: number;
  story_count: number;
}

export interface JDRecentDecision {
  task_id: string;
  recommendation: string;
  ability_match_score: number;
  resume_match_score: number;
  created_at: string;
}

export interface RoleSummary {
  id: string;
  role_name: string;
  role_type: string;
  status: string;
  priority: number;
  completeness_score: number;
  match_score: number;
  gap_count: number;
  updated_at: string;
}

export interface GapSummary {
  id: string;
  skill_name: string;
  gap_type: string;
  priority: number;
  status: string;
  progress: number;
  target_role_id: string;
}

// ── Interactive Analysis ──────────────────────────────────

export interface InteractiveChatResponse {
  reply: string;
  questions: string[];
  sufficiency: Record<string, number>;
  ready_to_generate: boolean;
}

export interface InteractiveGenerateResponse {
  narrative: string;
  bullets: string[];
  tags: string[];
  importance_score: number;
  suggestions: Array<{ suggestion: string; category: string }>;
}
