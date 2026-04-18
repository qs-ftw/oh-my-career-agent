"""Gap Evaluation node — generates initial gap items for a role.

Also handles gap updates in the achievement pipeline context.
"""

from __future__ import annotations

import asyncio
import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_LLM_TIMEOUT_SECONDS = 60

_ROLE_INIT_PROMPT = """\
你是一位资深职业顾问，正在进行技能差距分析。

根据岗位的能力模型和简历骨架，识别技能差距，以 JSON 数组返回：
[
  {
    "skill_name": "技能/能力名称",
    "gap_type": "missing|weak_evidence|weak_expression|low_depth|low_metrics",
    "priority": 1-10,
    "current_state": "当前状态描述",
    "target_state": "达标状态的描述",
    "improvement_plan": {"action": "具体行动", "expected_output": "预期产出"}
  }
]

差距类型：
- missing: 用户完全没有该技能经验
- weak_evidence: 用户可能具备该技能但简历中没有证明
- weak_expression: 技能存在但描述不充分
- low_depth: 提到了技能但缺乏深度
- low_metrics: 没有可量化的指标

专注于最有影响力的差距，最多返回 3-7 项。
只返回 JSON 数组，不要其他文字。"""

_ACHIEVEMENT_GAP_PROMPT = """\
你正在评估软件工程师的能力档案与目标岗位之间的技能差距。

根据新成果和每个匹配岗位的当前差距，判断：
1. 这个成果是否弥补了某些现有差距？如果是，建议更新进度。
2. 这个成果是否暴露了新的差距？

返回 JSON 数组：
[
  {
    "action": "update_gap",
    "gap_id": "现有差距的 UUID（如果是更新）",
    "progress": 0.0-1.0,
    "status": "open|in_progress|closed",
    "reason": "进度变化的原因"
  },
  {
    "action": "create_gap",
    "role_id": "岗位的 UUID",
    "items": [
      {
        "skill_name": "技能名称",
        "gap_type": "missing|weak_evidence|weak_expression|low_depth|low_metrics",
        "priority": 1-10,
        "current_state": "当前状态描述",
        "target_state": "目标状态描述",
        "improvement_plan": {"action": "具体行动", "expected_output": "预期产出"}
      }
    ]
  }
]

谨慎判断——只更新确实被该成果影响的差距。
只返回 JSON 数组，不要其他文字。"""


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
        user_parts.append(
            f"\nCapability Model:\n"
            f"{json.dumps(capability_model, ensure_ascii=False, indent=2)}"
        )
    if resume_draft:
        user_parts.append(
            f"\nCurrent Resume:\n"
            f"{json.dumps(resume_draft, ensure_ascii=False, indent=2)}"
        )

    user_prompt = "\n".join(user_parts)

    # Try LLM-based gap generation
    gap_items = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("gap_evaluation")
        logger.info(f"[gap_evaluation] Calling LLM for role_init: {role_name}")
        response = await asyncio.wait_for(
            llm.ainvoke(
                [
                    {"role": "system", "content": _ROLE_INIT_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            ),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        gap_items = json.loads(content.strip())
        logger.info(f"[gap_evaluation] LLM returned {len(gap_items)} gaps for {role_name}")
    except asyncio.TimeoutError:
        logger.warning(f"[gap_evaluation] LLM timed out for role_init: {role_name}")
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

    Used in the achievement pipeline. Evaluates all matching roles in parallel.
    """
    achievement_parsed = state.get("achievement_parsed") or {}
    role_matches = state.get("role_matches") or []
    target_roles = state.get("target_roles") or []

    existing_gap_updates = list(state.get("gap_updates", []))

    # Build tasks for parallel execution
    tasks: list[dict] = []
    for match in role_matches:
        role_id = match.get("role_id")
        if not role_id:
            continue

        role_data = None
        for r in target_roles:
            if r.get("role_id") == role_id:
                role_data = r
                break

        if not role_data:
            continue

        current_gaps = role_data.get("current_gaps", [])
        if not current_gaps:
            continue

        tasks.append({
            "role_id": role_id,
            "role_name": role_data.get("role_name", "Unknown Role"),
            "current_gaps": current_gaps,
        })

    # Run all gap evaluations in parallel
    results = await asyncio.gather(
        *[_eval_gaps_for_role(achievement_parsed, t) for t in tasks],
        return_exceptions=True,
    )

    all_gap_updates = list(existing_gap_updates)
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"[gap_evaluation] Parallel task failed: {result}")
            continue
        if result:
            all_gap_updates.extend(result)

    new_updates_count = len(all_gap_updates) - len(existing_gap_updates)
    return {
        "gap_updates": all_gap_updates,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "gap_evaluation",
                "action": "evaluated_gaps_for_achievement",
                "roles_evaluated": len(tasks),
                "updates_count": new_updates_count,
            }
        ],
    }


async def _eval_gaps_for_role(
    achievement_parsed: dict,
    task: dict,
) -> list[dict]:
    """Evaluate gaps for a single role — designed to run in parallel."""
    role_name = task["role_name"]
    current_gaps = task["current_gaps"]

    user_prompt = (
        f"Achievement:\n{json.dumps(achievement_parsed, ensure_ascii=False, indent=2)}\n\n"
        f"Role: {role_name}\n"
        f"Current gaps:\n{json.dumps(current_gaps, ensure_ascii=False, indent=2)}"
    )

    gap_updates: list[dict] | None = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("gap_evaluation")
        logger.info(f"[gap_evaluation] Calling LLM for achievement gap: {role_name}")
        response = await asyncio.wait_for(
            llm.ainvoke(
                [
                    {"role": "system", "content": _ACHIEVEMENT_GAP_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            ),
            timeout=_LLM_TIMEOUT_SECONDS,
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        gap_updates = json.loads(content.strip())
        logger.info(f"[gap_evaluation] LLM returned {len(gap_updates)} updates for {role_name}")
    except asyncio.TimeoutError:
        logger.warning(f"[gap_evaluation] LLM timed out for achievement gap: {role_name}")
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

    return gap_updates or []
