"""Role Matching node — scores an achievement against target roles."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def role_matching(state: CareerAgentState) -> dict:
    """Compare the parsed achievement against all active target roles and
    return a list of (role_id, match_score, reason) tuples.

    Sprint 3 will wire this to an LLM call.
    """
    return {"role_matches": []}
