"""Resume Init node — creates an initial resume skeleton for a new role."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert resume writer for software engineers.

Given a role's capability model, generate an initial resume skeleton as JSON:
{
  "summary": "A 2-3 sentence professional summary tailored to the role",
  "skills": ["list of key skills to highlight"],
  "experiences": [{"company": "TBD", "title": "TBD", "period": "TBD", "description": "TBD"}],
  "projects": [{"name": "TBD", "description": "TBD", "tech_stack": [], "highlights": []}],
  "highlights": ["2-3 technical highlights relevant to the role"],
  "metrics": [{"description": "TBD", "value": "TBD"}],
  "interview_points": ["2-3 talking points for interviews"]
}

The resume should be a skeleton with placeholders (TBD) where real data will go.
Focus on structuring it to highlight the capabilities needed for this specific role.
Return ONLY the JSON, no other text."""


async def resume_init(state: CareerAgentState) -> dict:
    """Generate a resume skeleton based on the capability model for a new role.

    Uses LLM if available, otherwise falls back to a template.
    """
    role_input = state.get("target_role_input") or {}
    capability_model = state.get("capability_model") or {}
    role_name = role_input.get("role_name", "Unknown Role")

    # Build prompt from capability model
    user_parts = [f"Role: {role_name}"]
    if capability_model:
        user_parts.append(f"\nCapability Model:\n{json.dumps(capability_model, ensure_ascii=False, indent=2)}")

    required_skills = role_input.get("required_skills", [])
    if required_skills:
        user_parts.append(f"Key Skills to Highlight: {', '.join(required_skills)}")

    user_prompt = "\n".join(user_parts)

    # Try LLM-based generation
    resume_draft = None
    try:
        from src.core.llm import get_llm
        from src.agent.configuration import AGENT_CONFIGURATION

        llm = get_llm("openai", AGENT_CONFIGURATION.resume_init)
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
        resume_draft = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM resume init failed ({e}), using template fallback")

    # Fallback: template-based resume
    if not resume_draft:
        resume_draft = {
            "summary": f"Experienced {role_name} with strong technical skills.",
            "skills": required_skills if required_skills else [],
            "experiences": [],
            "projects": [],
            "highlights": [],
            "metrics": [],
            "interview_points": [],
        }

    return {
        "resume_draft": resume_draft,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "resume_init",
                "action": "generated_resume_skeleton",
                "role_name": role_name,
            }
        ],
    }
