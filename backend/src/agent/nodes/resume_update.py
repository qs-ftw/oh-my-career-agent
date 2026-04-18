"""Resume Update node — generates resume update suggestions based on an achievement."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
你是一位资深简历优化顾问，专注于软件工程师领域。

根据已解析的成果信息和目标岗位的当前简历内容，生成具体、可操作的简历更新建议。

返回 JSON 数组，每个元素格式如下：
[
  {
    "suggestion_type": "resume_update",
    "target_role_id": "岗位的 UUID",
    "title": "建议的简短描述",
    "content": {
      "section": "要更新的简历板块（如 skills, experiences, projects）",
      "action": "add|replace|modify",
      "text": "要添加或替换的具体文本",
      "reasoning": "为什么这个改动能改善简历"
    },
    "impact_score": 0.0-1.0,
    "risk_level": "low|medium|high"
  }
]

要求：
- 所有文本字段必须使用中文
- 具体且实用，专注于最有影响力的更新
- 只返回 JSON 数组，不要其他文字
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
            f"Parsed achievement:\n"
            f"{json.dumps(achievement_parsed, ensure_ascii=False, indent=2)}\n\n"
            f"Target role: {role_name}\n"
            f"Required skills: "
            f"{', '.join(role_data.get('required_skills', []))}\n\n"
            f"Current resume content:\n"
            f"{json.dumps(role_data.get('resume_content', {}), ensure_ascii=False, indent=2)}"
        )

        # Try LLM-based suggestion generation
        suggestions = None
        try:
            from src.core.llm import get_llm

            llm = get_llm("resume_update")
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
