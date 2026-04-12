"""Gap Evaluation node — identifies and updates skill gaps."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def gap_evaluation(state: CareerAgentState) -> dict:
    """Evaluate whether the achievement changes any gap status or creates new gaps.

    Sprint 3 will wire this to an LLM call.
    """
    return {
        "gap_updates": state.get("gap_updates", []),
    }
