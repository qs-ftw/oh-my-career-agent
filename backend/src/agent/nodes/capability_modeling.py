"""Capability Modeling node — builds a structured capability model for a role."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert career advisor analyzing a job role.

Given the role information, produce a structured capability model as JSON with these fields:
{
  "core_capabilities": ["list of 5-8 core technical capabilities required"],
  "secondary_capabilities": ["list of 3-5 secondary skills"],
  "bonus_capabilities": ["list of nice-to-have skills"],
  "project_requirements": ["types of projects this role typically works on"],
  "evaluation_rules": ["how to evaluate if someone meets each capability"]
}

Be specific and practical. Focus on real-world skills and technologies."""


async def capability_modeling(state: CareerAgentState) -> dict:
    """Analyze role input and generate a capability model.

    Uses LLM if available, otherwise falls back to a template-based approach.
    """
    role_input = state.get("target_role_input") or {}
    role_name = role_input.get("role_name", "Unknown Role")
    role_type = role_input.get("role_type", "")
    description = role_input.get("description", "")
    required_skills = role_input.get("required_skills", [])
    bonus_skills = role_input.get("bonus_skills", [])
    keywords = role_input.get("keywords", [])
    source_jd = role_input.get("source_jd", "")

    # Build user prompt from role data
    user_parts = [f"Role Name: {role_name}"]
    if role_type:
        user_parts.append(f"Role Type: {role_type}")
    if description:
        user_parts.append(f"Description: {description}")
    if required_skills:
        user_parts.append(f"Required Skills: {', '.join(required_skills)}")
    if bonus_skills:
        user_parts.append(f"Bonus Skills: {', '.join(bonus_skills)}")
    if keywords:
        user_parts.append(f"Keywords: {', '.join(keywords)}")
    if source_jd:
        user_parts.append(f"Source JD:\n{source_jd[:2000]}")

    user_prompt = "\n".join(user_parts)

    # Try LLM-based generation
    capability_model = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("capability_modeling")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        capability_model = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM capability modeling failed ({e}), using template fallback")

    # Fallback: template-based capability model
    if not capability_model:
        capability_model = {
            "core_capabilities": (
                required_skills[:8] if required_skills else [f"{role_name} core skill"]
            ),
            "secondary_capabilities": bonus_skills[:5] if bonus_skills else [],
            "bonus_capabilities": keywords[:5] if keywords else [],
            "project_requirements": [
                f"Building {role_name.lower()} related systems",
                "Collaborating with cross-functional teams",
                "Delivering production-quality code",
            ],
            "evaluation_rules": [
                "Check for real project experience with required skills",
                "Evaluate depth of technical knowledge",
                "Assess problem-solving ability",
            ],
        }

    return {
        "capability_model": capability_model,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "capability_modeling",
                "action": "generated_capability_model",
                "role_name": role_name,
                "core_count": len(capability_model.get("core_capabilities", [])),
            }
        ],
    }
