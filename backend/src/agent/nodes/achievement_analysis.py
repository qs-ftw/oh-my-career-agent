"""Achievement Analysis node — extracts structured data from raw achievement text."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert career coach analyzing a software engineer's work achievement.

Given the raw achievement text, extract structured information as JSON:
{
  "summary": "A concise one-paragraph summary of the achievement",
  "technical_points": [{"point": "technology, pattern, or architecture decision involved"}],
  "challenges": [{"challenge": "problem encountered and its context"}],
  "solutions": [{"solution": "how the challenge was addressed"}],
  "metrics": [{"metric": "quantifiable outcome", "value": "specific number or percentage"}],
  "interview_points": [{"point": "how to articulate this in a behavioral interview"}],
  "tags": ["relevant", "skill", "tags"],
  "importance_score": 0.0-1.0
}

Be specific and practical. Extract real technical details and quantifiable results.
Return ONLY the JSON object, no other text.
"""


async def achievement_analysis(state: CareerAgentState) -> dict:
    """Parse raw achievement text into a structured achievement object.

    Uses LLM if available, otherwise falls back to basic extraction.
    """
    achievement_raw = state.get("achievement_raw", "")

    user_prompt = f"Analyze this achievement:\n\n{achievement_raw}"

    # Try LLM-based analysis
    parsed = None
    try:
        from src.core.llm import get_llm
        from src.agent.configuration import AGENT_CONFIGURATION

        llm = get_llm("openai", AGENT_CONFIGURATION.achievement_analysis)
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM achievement analysis failed ({e}), using template fallback")

    # Fallback: basic extraction
    if not parsed:
        # Extract tags from common keywords
        raw_lower = achievement_raw.lower()
        common_techs = [
            "python", "javascript", "typescript", "react", "vue", "go", "rust", "java",
            "kafka", "redis", "postgresql", "mysql", "mongodb", "docker", "kubernetes",
            "aws", "gcp", "azure", "fastapi", "django", "flask", "node",
            "microservice", "api", "ci/cd", "devops", "testing",
        ]
        tags = [t for t in common_techs if t in raw_lower]

        parsed = {
            "summary": achievement_raw[:300] if len(achievement_raw) > 300 else achievement_raw,
            "technical_points": [],
            "challenges": [],
            "solutions": [],
            "metrics": [],
            "interview_points": [],
            "tags": tags[:5],
            "importance_score": 0.5,
        }

    return {
        "achievement_parsed": parsed,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "achievement_analysis",
                "action": "parsed_achievement",
                "tags_count": len(parsed.get("tags", [])),
                "metrics_count": len(parsed.get("metrics", [])),
            }
        ],
    }
