"""JD Parsing node — extracts structured data from raw JD text."""

from __future__ import annotations

from src.agent.state import CareerAgentState


async def jd_parsing(state: CareerAgentState) -> dict:
    """Parse raw JD text into a structured JD object with skills and keywords.

    Sprint 4 will wire this to an LLM call.
    """
    return {
        "jd_parsed": {
            "role_name": "",
            "keywords": [],
            "required_skills": [],
            "bonus_items": [],
            "style": {},
        },
    }
