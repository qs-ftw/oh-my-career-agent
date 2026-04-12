"""Resume Update node — generates resume update suggestions based on an achievement."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def resume_update(state: CareerAgentState) -> dict:
    """Produce resume update suggestions for each matched role.

    Sprint 3 will wire this to an LLM call using the prompt from
    src/prompts/resume_update.py.
    """
    return {
        "suggestions": state.get("suggestions", []),
    }
