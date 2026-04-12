"""JD Tailoring node — generates or tunes a resume for a specific JD."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def jd_tailoring(state: CareerAgentState) -> dict:
    """Create a tailored resume draft based on the parsed JD and career assets.

    Sprint 4 will wire this to an LLM call using the prompt from
    src/prompts/jd_tailoring.py.
    """
    return {
        "resume_draft": None,
        "match_scores": {
            "ability_match_score": 0.0,
            "resume_match_score": 0.0,
            "readiness_score": 0.0,
        },
    }
