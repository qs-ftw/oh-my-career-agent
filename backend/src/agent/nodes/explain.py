"""Explain node — produces a human-readable summary of agent outputs."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a career advisor summarizing the results of an automated career analysis.

Given the pipeline outputs, write a concise, human-readable summary in Chinese that explains:
1. What was analyzed
2. Key findings (role matches, skill relevance)
3. Suggested actions (resume updates, gap improvements)
4. Overall assessment

Keep it under 200 words. Be encouraging but honest.
Return plain text, not JSON.
"""


async def explain(state: CareerAgentState) -> dict:
    """Summarize the results of the pipeline in natural language.

    Uses LLM if available, otherwise generates a template summary.
    """
    achievement_parsed = state.get("achievement_parsed") or {}
    role_matches = state.get("role_matches") or []
    suggestions = state.get("suggestions", [])
    gap_updates = state.get("gap_updates", [])

    # Build summary of pipeline outputs
    pipeline_outputs = {
        "achievement_summary": achievement_parsed.get("summary", ""),
        "role_matches_count": len(role_matches),
        "role_matches": [
            {"role_name": m.get("reason", "Unknown"), "score": m.get("match_score", 0)}
            for m in role_matches[:3]
        ],
        "suggestions_count": len(suggestions),
        "gap_updates_count": len(gap_updates),
    }

    user_prompt = f"Pipeline outputs:\n{json.dumps(pipeline_outputs, ensure_ascii=False, indent=2)}"

    # Try LLM-based explanation
    explanation = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("explain")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        explanation = response.content.strip()
    except Exception as e:
        logger.info(f"LLM explain failed ({e}), using template fallback")

    # Fallback: template summary
    if not explanation:
        match_info = ""
        if role_matches:
            match_info = f"匹配到 {len(role_matches)} 个目标岗位"
        explanation = (
            f"已分析成果。{match_info}。"
            f"生成了 {len(suggestions)} 条简历更新建议，"
            f"{len(gap_updates)} 项能力差距更新。"
        )

    return {
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "explain",
                "action": "generated_summary",
                "summary": explanation,
            }
        ],
    }
