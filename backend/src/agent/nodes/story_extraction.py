"""Story extraction node — converts achievement data into STAR interview stories."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState
from src.prompts.story_extraction import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def story_extraction(state: CareerAgentState) -> dict:
    """Extract STAR interview stories from achievement parsed data.

    Uses LLM if available, otherwise falls back to basic extraction.
    """
    achievement_parsed = state.get("achievement_parsed") or {}
    achievement_id = state.get("achievement_id", "")

    if not achievement_parsed:
        return {
            "story_candidates": [],
            "agent_logs": state.get("agent_logs", []) + [
                {"node": "story_extraction", "action": "skipped", "reason": "no data"}
            ],
        }

    user_prompt = f"Extract interview stories from this achievement:\n\n{json.dumps(achievement_parsed, ensure_ascii=False, indent=2)}"

    candidates = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("story_extraction")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        candidates = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM story extraction failed ({e}), using template fallback")

    if not candidates:
        # Fallback: create a basic story from available data
        title = achievement_parsed.get("title", "Achievement")
        summary = achievement_parsed.get("summary", "")
        tech_points = achievement_parsed.get("technical_points", [])
        metrics = achievement_parsed.get("metrics", [])
        tags = achievement_parsed.get("tags", [])

        candidates = [
            {
                "title": f"{title} - 面试故事",
                "theme": "general",
                "story_json": {
                    "situation": summary[:200] if summary else "",
                    "task": "",
                    "action": ", ".join(str(p) for p in tech_points[:3]),
                    "result": ", ".join(str(m) for m in metrics[:3]),
                },
                "best_for": tags[:5] if isinstance(tags, list) else [],
                "confidence_score": 0.5 if summary else 0.2,
            }
        ]

    return {
        "story_candidates": candidates,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "story_extraction",
                "action": "extracted_stories",
                "achievement_id": achievement_id,
                "count": len(candidates),
            }
        ],
    }
