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

    Error handling strategy:
    - LLM timeout/network errors → propagate (not recoverable)
    - JSON parse errors → fallback to basic keyword extraction (recoverable)
    """
    achievement_raw = state.get("achievement_raw", "")

    user_prompt = f"Analyze this achievement:\n\n{achievement_raw}"

    logs = list(state.get("agent_logs", []))

    # Try LLM-based analysis
    parsed = None
    llm_error = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("achievement_analysis")
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
    except json.JSONDecodeError as e:
        # Recoverable: LLM returned non-JSON, use fallback
        logger.warning(f"LLM returned non-JSON for achievement analysis: {e}")
        logs.append({
            "node": "achievement_analysis",
            "level": "warning",
            "message": f"LLM response was not valid JSON, using fallback: {e}",
        })
    except Exception as e:
        # Severe: timeout, network error, API error — must propagate
        error_type = type(e).__name__
        logger.error(f"LLM achievement analysis failed ({error_type}): {e}")
        llm_error = f"{error_type}: {e}"

    # Fallback: basic keyword extraction (only for recoverable errors)
    if not parsed:
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

    result_logs = logs + [
        {
            "node": "achievement_analysis",
            "action": "parsed_achievement",
            "tags_count": len(parsed.get("tags", [])),
            "metrics_count": len(parsed.get("metrics", [])),
        }
    ]

    result = {
        "achievement_parsed": parsed,
        "agent_logs": result_logs,
    }

    # Propagate LLM errors so the service layer can decide what to do
    if llm_error:
        result["pipeline_error"] = llm_error

    return result
