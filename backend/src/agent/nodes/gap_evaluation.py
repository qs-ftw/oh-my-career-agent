"""Gap Evaluation node — generates initial gap items for a role."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
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


async def gap_evaluation(state: CareerAgentState) -> dict:
    """Generate initial gap items based on capability model vs current state.

    For role initialization, compares the capability model against the
    (mostly empty) resume skeleton to identify gaps.
    """
    role_input = state.get("target_role_input") or {}
    capability_model = state.get("capability_model") or {}
    resume_draft = state.get("resume_draft") or {}
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
                {"role": "system", "content": _SYSTEM_PROMPT},
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
