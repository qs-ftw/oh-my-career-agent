"""Achievement Analysis node — extracts structured data from raw achievement text."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def achievement_analysis(state: CareerAgentState) -> dict:
    """Parse raw achievement text into a structured achievement object.

    Sprint 3 will wire this to an LLM call using the prompt from
    src/prompts/achievement_analysis.py.
    """
    # Placeholder: echo back minimal parsed data.
    return {
        "achievement_parsed": {
            "summary": state.get("achievement_raw", "")[:200],
            "technical_points": [],
            "challenges": [],
            "solutions": [],
            "metrics": [],
            "interview_points": [],
            "importance_score": 0.0,
        },
    }
