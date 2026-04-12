"""Gap Evaluation node — generates initial gap items for a role.

Also handles gap updates in the achievement pipeline context.
"""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_ROLE_INIT_PROMPT = """\
You are an expert career advisor performing a gap analysis.

Given a role's capability model and resume skeleton, identify skill gaps as JSON array:
[
  {
    "skill_name": "name of the skill/capability",
    "gap_type": "missing|weak_evidence|weak_expression|low_depth|low_metrics",
    "priority": 1-10,
    "current_state": "description of current state",
    "target_state": "what meeting this capability looks like",
    "improvement_plan": {"action": "what to do", "expected_output": "what to produce"}
  }
]

Gap types:
- missing: user has no experience with this skill
- weak_evidence: user likely has the skill but no proof in resume
- weak_expression: skill is present but poorly described
- low_depth: skill is mentioned but lacks depth
- low_metrics: no quantifiable metrics for this capability

Focus on the most impactful gaps. Return 3-7 items max.
Return ONLY the JSON array, no other text."""

_ACHIEVEMENT_GAP_PROMPT = """\
You are evaluating skill gaps between a software engineer's profile and target roles.

Given a new achievement and the current gaps for each matched role, determine:
1. Does this achievement address any existing gaps? If yes, suggest progress updates.
2. Does this achievement reveal any new gaps?

Return a JSON array of gap update objects:
[
  {
    "action": "update_gap",
    "gap_id": "UUID of existing gap (if updating)",
    "progress": 0.0-1.0,
    "status": "open|in_progress|closed",
    "reason": "why the progress changed"
  },
  {
    "action": "create_gap",
    "role_id": "UUID of the role",
    "items": [
      {
        "skill_name": "name",
        "gap_type": "missing|weak_evidence|weak_expression|low_depth|low_metrics",
        "priority": 1-10,
        "current_state": "description",
        "target_state": "description",
        "improvement_plan": {"action": "what to do", "expected_output": "what to produce"}
      }
    ]
  }
]

Be conservative — only update gaps that are clearly affected by this achievement.
Return ONLY the JSON array, no other text."""


async def gap_evaluation(state: CareerAgentState) -> dict:
    """Evaluate gaps — works in two contexts:

    1. Role init: generates initial gaps from capability model vs resume skeleton.
    2. Achievement pipeline: checks how a new achievement affects existing gaps.
    """
    achievement_parsed = state.get("achievement_parsed")
    role_matches = state.get("role_matches") or []

    # Detect context: achievement pipeline vs role init
    if achievement_parsed and role_matches:
        return await _gap_evaluation_achievement(state)
    else:
        return await _gap_evaluation_role_init(state)


async def _gap_evaluation_role_init(state: CareerAgentState) -> dict:
    """Generate initial gap items based on capability model vs current state.

    Used in the role initialization pipeline.
    """
    role_input = state.get("target_role_input") or {}
    capability_model = state.get("capability_model") or {}
    resume_draft = state.get("resume_draft", {})
    role_name = role_input.get("role_name", "Unknown Role")

    # Build prompt
    user_parts = [f"Role: {role_name}"]
    if capability_model:
        user_parts.append(f"\nCapability Model:\n{json.dumps(capability_model, ensure_ascii=False, indent=2)}")
    if resume_draft:
        user_parts.append(f"\nCurrent Resume:\n{json.dumps(resume_draft, ensure_ascii=False, indent=2)}")

    user_prompt = "\n".join(user_parts)

    # Try LLM-based gap generation
    gap_items = None
    try:
        from src.core.llm import get_llm
        from src.agent.configuration import AGENT_CONFIGURATION

        llm = get_llm("openai", AGENT_CONFIGURATION.gap_evaluation)
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _ROLE_INIT_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        gap_items = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM gap evaluation failed ({e}), using template fallback")

    # Fallback: generate gaps from core capabilities
    if not gap_items:
        core_caps = capability_model.get("core_capabilities", [])
        required_skills = role_input.get("required_skills", [])
        all_skills = list(set(core_caps + required_skills))[:5]

        gap_items = []
        for i, skill in enumerate(all_skills):
            gap_items.append({
                "skill_name": skill,
                "gap_type": "weak_evidence",
                "priority": max(1, 10 - i * 2),
                "current_state": f"未在简历中体现 {skill} 相关经验",
                "target_state": f"在简历中有清晰的 {skill} 项目经验和成果",
                "improvement_plan": {
                    "action": f"补充 {skill} 相关的项目经验和量化指标",
                    "expected_output": f"包含 {skill} 技术细节的项目描述",
                },
            })

    return {
        "gap_updates": state.get("gap_updates", []) + [
            {
                "action": "create_gap",
                "role_name": role_name,
                "items": gap_items,
            }
        ],
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "gap_evaluation",
                "action": "generated_initial_gaps",
                "role_name": role_name,
                "gap_count": len(gap_items),
            }
        ],
    }


async def _gap_evaluation_achievement(state: CareerAgentState) -> dict:
    """Evaluate how a new achievement affects existing gaps.

    Used in the achievement pipeline. Iterates over role_matches and checks
    current gaps for each role.
    """
    achievement_parsed = state.get("achievement_parsed") or {}
    role_matches = state.get("role_matches") or []
    target_roles = state.get("target_roles") or []

    all_gap_updates = list(state.get("gap_updates", []))

    for match in role_matches:
        role_id = match.get("role_id")
        if not role_id:
            continue

        # Find role data with current gaps
        role_data = None
        for r in target_roles:
            if r.get("role_id") == role_id:
                role_data = r
                break

        if not role_data:
            continue

        role_name = role_data.get("role_name", "Unknown Role")
        current_gaps = role_data.get("current_gaps", [])

        if not current_gaps:
            continue

        # Build prompt
        user_prompt = (
            f"Achievement:\n{json.dumps(achievement_parsed, ensure_ascii=False, indent=2)}\n\n"
            f"Role: {role_name}\n"
            f"Current gaps:\n{json.dumps(current_gaps, ensure_ascii=False, indent=2)}"
        )

        # Try LLM-based gap evaluation
        gap_updates = None
        try:
            from src.core.llm import get_llm
            from src.agent.configuration import AGENT_CONFIGURATION

            llm = get_llm("openai", AGENT_CONFIGURATION.gap_evaluation)
            response = await llm.ainvoke(
                [
                    {"role": "system", "content": _ACHIEVEMENT_GAP_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            )
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            gap_updates = json.loads(content.strip())
        except Exception as e:
            logger.info(f"LLM gap evaluation (achievement) failed for {role_name} ({e}), using fallback")

        # Fallback: bump progress on gaps related to achievement tags
        if not gap_updates:
            achievement_tags = [t.lower() for t in achievement_parsed.get("tags", [])]
            for gap in current_gaps:
                skill_lower = gap.get("skill_name", "").lower()
                if any(tag in skill_lower or skill_lower in tag for tag in achievement_tags):
                    gap_updates = gap_updates or []
                    gap_updates.append({
                        "action": "update_gap",
                        "gap_id": gap["id"],
                        "progress": min(1.0, gap.get("progress", 0.0) + 0.2),
                        "status": "in_progress",
                        "reason": f"成果中涉及 {gap['skill_name']} 相关技能",
                    })

        if gap_updates:
            all_gap_updates.extend(gap_updates)

    return {
        "gap_updates": all_gap_updates,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "gap_evaluation",
                "action": "evaluated_gaps_for_achievement",
                "roles_evaluated": len(role_matches),
                "updates_count": len(all_gap_updates) - len(state.get("gap_updates", [])),
            }
        ],
    }
