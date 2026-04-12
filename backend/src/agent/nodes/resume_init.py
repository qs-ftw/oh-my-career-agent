"""Resume Init node — creates an initial resume skeleton for a new role."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def resume_init(state: CareerAgentState) -> dict:
    """Generate a resume skeleton based on the capability model for a new role.

    Sprint 2 will wire this to an LLM call.
    """
    return {
        "resume_draft": None,
    }
