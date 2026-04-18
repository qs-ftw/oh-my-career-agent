"""Resume Init node — generates an initial resume using user achievements."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert resume writer for software engineers.

Given a target role and the user's career achievements, generate a complete, \
content-rich resume as JSON:
{
  "summary": "A 2-3 sentence professional summary highlighting the user's most \
relevant experience for this role",
  "skills": ["list of key skills from the user's achievements that match the role"],
  "experiences": [{"company": "from context or generic", "title": "inferred role", \
"period": "inferred or omit", "description": "2-3 bullet points of concrete \
accomplishments with metrics where available"}],
  "projects": [{"name": "project name from achievements", "description": "what was \
built and why it matters", "tech_stack": ["technologies used"], "highlights": \
["key outcomes with metrics"]}],
  "highlights": ["3-5 standout technical achievements relevant to the role, with \
quantified results"],
  "metrics": [{"description": "what was improved", "value": "concrete number"}],
  "interview_points": ["3-5 talking points drawn from real achievements for \
interviews"]
}

IMPORTANT RULES:
- Use ONLY information from the provided achievements. Do not fabricate experiences.
- Extract concrete metrics, numbers, and outcomes from the achievements.
- Tailor descriptions to emphasize skills and outcomes relevant to the target role.
- Fill in real content everywhere — do NOT use "TBD" or placeholder text.
- If the user has achievements, each one should map to at least one project or \
experience entry.
- Write in the same language as the achievements (Chinese/English).

Return ONLY the JSON, no other text."""


async def resume_init(state: CareerAgentState) -> dict:
    """Generate a resume using user achievements and the capability model.

    Uses LLM with achievements data to produce a content-rich resume.
    Falls back to a basic template if LLM fails or no achievements exist.
    """
    role_input = state.get("target_role_input") or {}
    capability_model = state.get("capability_model") or {}
    career_assets = state.get("career_assets") or {}
    achievements = career_assets.get("achievements", [])
    role_name = role_input.get("role_name", "Unknown Role")

    # Build user prompt
    user_parts = [f"Target Role: {role_name}"]

    role_desc = role_input.get("description")
    if role_desc:
        user_parts.append(f"Role Description: {role_desc}")

    required_skills = role_input.get("required_skills", [])
    if required_skills:
        user_parts.append(f"Required Skills: {', '.join(required_skills)}")

    bonus_skills = role_input.get("bonus_skills", [])
    if bonus_skills:
        user_parts.append(f"Bonus Skills: {', '.join(bonus_skills)}")

    if capability_model:
        user_parts.append(
            f"\nCapability Model:\n"
            f"{json.dumps(capability_model, ensure_ascii=False, indent=2)}"
        )

    if achievements:
        user_parts.append(
            f"\nUser Achievements ({len(achievements)} total):"
        )
        for i, ach in enumerate(achievements, 1):
            ach_text = f"\n{i}. {ach['title']}"
            if ach.get("summary"):
                ach_text += f"\n   Summary: {ach['summary']}"
            if ach.get("raw_content"):
                ach_text += f"\n   Details: {ach['raw_content']}"
            if ach.get("tags"):
                ach_text += f"\n   Tags: {', '.join(ach['tags'])}"
            if ach.get("metrics"):
                metrics_str = "; ".join(
                    f"{m.get('description', '')}: {m.get('value', '')}"
                    for m in ach["metrics"]
                    if isinstance(m, dict)
                )
                if metrics_str:
                    ach_text += f"\n   Metrics: {metrics_str}"
            user_parts.append(ach_text)
    else:
        user_parts.append(
            "\nNote: The user has no recorded achievements yet. "
            "Generate a skeleton resume highlighting the role's required skills."
        )

    user_prompt = "\n".join(user_parts)

    # Try LLM-based generation
    resume_draft = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("resume_init")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if isinstance(content, str):
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
                "action": "generated_resume_from_achievements",
                "role_name": role_name,
                "achievements_count": len(achievements),
            }
        ],
    }
