"""Role Matching node — scores an achievement against target roles."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
你正在将一个已解析的工作成果与用户的目标岗位进行匹配。

根据成果内容和目标岗位列表，计算每个岗位的相关度分数（0.0-1.0）并说明原因。

返回 JSON 数组：
[
  {
    "role_id": "岗位的 UUID",
    "match_score": 0.0-1.0,
    "reason": "简要说明相关性"
  }
]

只包含 match_score >= 0.3 的岗位。匹配时适当放宽——即使部分相关也有价值。
只返回 JSON 数组，不要其他文字。
"""


async def role_matching(state: CareerAgentState) -> dict:
    """Compare the parsed achievement against all active target roles.

    Uses LLM if available, otherwise assigns default scores.
    """
    achievement_parsed = state.get("achievement_parsed") or {}
    target_roles = state.get("target_roles") or []

    if not target_roles:
        return {
            "role_matches": [],
            "agent_logs": state.get("agent_logs", []) + [
                {"node": "role_matching", "action": "no_roles_found"}
            ],
        }

    # Build user prompt
    roles_description = json.dumps(
        [
            {
                "role_id": r.get("role_id"),
                "role_name": r.get("role_name"),
                "required_skills": r.get("required_skills", []),
                "description": r.get("description", ""),
            }
            for r in target_roles
        ],
        ensure_ascii=False,
        indent=2,
    )

    user_prompt = (
        f"Parsed achievement:\n{json.dumps(achievement_parsed, ensure_ascii=False, indent=2)}\n\n"
        f"Target roles:\n{roles_description}"
    )

    # Try LLM-based matching
    role_matches = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("role_matching")
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
        role_matches = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM role matching failed ({e}), using template fallback")

    # Fallback: assign moderate scores to all roles
    if not role_matches:
        role_matches = [
            {
                "role_id": r.get("role_id"),
                "match_score": 0.5,
                "reason": f"Possible relevance to {r.get('role_name', 'unknown role')}",
            }
            for r in target_roles
        ]

    return {
        "role_matches": role_matches,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "role_matching",
                "action": "matched_roles",
                "match_count": len(role_matches),
            }
        ],
    }
