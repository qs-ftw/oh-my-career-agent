"""Role Matching node — scores an achievement against target roles."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are matching a parsed achievement against a user's active target roles.

Given the parsed achievement and the list of target roles, compute a match
relevance score (0.0-1.0) for each role and explain why.

Return a JSON array of match objects:
[
  {
    "role_id": "the role's UUID",
    "match_score": 0.0-1.0,
    "reason": "brief explanation of relevance"
  }
]

Only include roles with match_score >= 0.3. Be generous in matching — even
partial relevance is valuable to surface.
Return ONLY the JSON array, no other text.
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
        from src.agent.configuration import AGENT_CONFIGURATION

        llm = get_llm("openai", AGENT_CONFIGURATION.role_matching)
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
