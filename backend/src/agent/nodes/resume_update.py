"""Resume Update node — generates resume update suggestions based on an achievement."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert resume writer for software engineers.

Given a parsed achievement and a target role with its current resume content,
generate specific, actionable suggestions for updating the resume.

Return a JSON array of suggestion objects:
[
  {
    "suggestion_type": "resume_update",
    "target_role_id": "the role's UUID",
    "title": "short description of the suggestion",
    "content": {
      "section": "which resume section to update (e.g. skills, experiences, projects)",
      "action": "add|replace|modify",
      "text": "the exact text to add or replace with",
      "reasoning": "why this change improves the resume"
    },
    "impact_score": 0.0-1.0,
    "risk_level": "low|medium|high"
  }
]

Be specific and practical. Focus on the most impactful updates.
Return ONLY the JSON array, no other text.
"""


async def resume_update(state: CareerAgentState) -> dict:
    """Generate resume update suggestions for each matched role.

    Iterates over role_matches, looks up the role data, and produces
    one or more suggestions per role.
    """
    achievement_parsed = state.get("achievement_parsed") or {}
    role_matches = state.get("role_matches") or []
    target_roles = state.get("target_roles") or []

    all_suggestions = list(state.get("suggestions", []))

    for match in role_matches:
        role_id = match.get("role_id")
        match_score = match.get("match_score", 0.0)

        # Find the full role data
        role_data = None
        for r in target_roles:
            if r.get("role_id") == role_id:
                role_data = r
                break

        if not role_data:
            continue

        role_name = role_data.get("role_name", "Unknown Role")

        # Build prompt for this role
        user_prompt = (
            f"Parsed achievement:\n{json.dumps(achievement_parsed, ensure_ascii=False, indent=2)}\n\n"
            f"Target role: {role_name}\n"
            f"Required skills: {', '.join(role_data.get('required_skills', []))}\n\n"
            f"Current resume content:\n{json.dumps(role_data.get('resume_content', {}), ensure_ascii=False, indent=2)}"
        )

        # Try LLM-based suggestion generation
        suggestions = None
        try:
            from src.core.llm import get_llm
            from src.agent.configuration import AGENT_CONFIGURATION

            llm = get_llm("openai", AGENT_CONFIGURATION.resume_update)
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
            suggestions = json.loads(content.strip())
        except Exception as e:
            logger.info(f"LLM resume update failed for {role_name} ({e}), using fallback")

        # Fallback: one generic suggestion per role
        if not suggestions:
            suggestions = [
                {
                    "suggestion_type": "resume_update",
                    "target_role_id": role_id,
                    "title": f"将成果添加到简历 - {role_name}",
                    "content": {
                        "section": "experiences",
                        "action": "add",
                        "text": achievement_parsed.get("summary", ""),
                        "reasoning": "该成果与目标岗位相关，建议添加到经历部分",
                    },
                    "impact_score": match_score * 0.8,
                    "risk_level": "low",
                }
            ]
        else:
            # Ensure each suggestion has target_role_id
            for sug in suggestions:
                if not sug.get("target_role_id"):
                    sug["target_role_id"] = role_id
                if not sug.get("suggestion_type"):
                    sug["suggestion_type"] = "resume_update"

        all_suggestions.extend(suggestions)

    return {
        "suggestions": all_suggestions,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "resume_update",
                "action": "generated_suggestions",
                "roles_processed": len(role_matches),
                "suggestions_count": len(all_suggestions) - len(state.get("suggestions", [])),
            }
        ],
    }
