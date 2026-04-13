"""CareerAgent state definition for LangGraph workflows.

This TypedDict is the single shared state object that flows through all
agent nodes in every pipeline.  Not every field is populated on every run;
nodes read/write only the fields relevant to their pipeline.
"""

from __future__ import annotations

from typing import Any, TypedDict


class CareerAgentState(TypedDict, total=False):
    """Shared state for all CareerAgent LangGraph pipelines.

    Fields are grouped by pipeline for readability, but all share the same
    state dict so the graph can branch and merge freely.
    """

    # ------------------------------------------------------------------
    # Context (set by the API layer before invoking the graph)
    # ------------------------------------------------------------------
    user_id: str
    workspace_id: str
    candidate_profile: dict[str, Any] | None  # Canonical profile context

    # ------------------------------------------------------------------
    # Achievement pipeline
    # ------------------------------------------------------------------
    achievement_id: str | None
    achievement_raw: str | None
    achievement_parsed: dict[str, Any] | None
    target_roles: list[dict[str, Any]] | None

    # ------------------------------------------------------------------
    # Role initialization pipeline
    # ------------------------------------------------------------------
    target_role_input: dict[str, Any] | None
    capability_model: dict[str, Any] | None

    # ------------------------------------------------------------------
    # JD pipeline
    # ------------------------------------------------------------------
    jd_raw: str | None
    jd_parsed: dict[str, Any] | None
    jd_mode: str | None  # "generate_new" | "tune_existing"
    base_resume_id: str | None
    career_assets: dict[str, Any] | None  # Pre-loaded achievements, roles, skills
    base_resume_content: dict[str, Any] | None  # Base resume for tune mode

    # ------------------------------------------------------------------
    # Story extraction
    # ------------------------------------------------------------------
    story_candidates: list[dict[str, Any]] | None

    # ------------------------------------------------------------------
    # Shared outputs (written by agent nodes)
    # ------------------------------------------------------------------
    role_matches: list[dict[str, Any]] | None
    suggestions: list[dict[str, Any]]
    gap_updates: list[dict[str, Any]]
    resume_draft: dict[str, Any] | None
    match_scores: dict[str, Any] | None

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------
    agent_logs: list[dict[str, Any]]
