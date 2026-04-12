"""CareerAgent state definition for LangGraph workflows.

This TypedDict is the single shared state object that flows through all
agent nodes in every pipeline.  Not every field is populated on every run;
nodes read/write only the fields relevant to their pipeline.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


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

    # ------------------------------------------------------------------
    # Achievement pipeline
    # ------------------------------------------------------------------
    achievement_id: Optional[str]
    achievement_raw: Optional[str]
    achievement_parsed: Optional[dict[str, Any]]
    target_roles: Optional[list[dict[str, Any]]]

    # ------------------------------------------------------------------
    # Role initialization pipeline
    # ------------------------------------------------------------------
    target_role_input: Optional[dict[str, Any]]
    capability_model: Optional[dict[str, Any]]

    # ------------------------------------------------------------------
    # JD pipeline
    # ------------------------------------------------------------------
    jd_raw: Optional[str]
    jd_parsed: Optional[dict[str, Any]]
    jd_mode: Optional[str]  # "generate_new" | "tune_existing"
    base_resume_id: Optional[str]

    # ------------------------------------------------------------------
    # Shared outputs (written by agent nodes)
    # ------------------------------------------------------------------
    role_matches: Optional[list[dict[str, Any]]]
    suggestions: list[dict[str, Any]]
    gap_updates: list[dict[str, Any]]
    resume_draft: Optional[dict[str, Any]]
    match_scores: Optional[dict[str, Any]]

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------
    agent_logs: list[dict[str, Any]]
