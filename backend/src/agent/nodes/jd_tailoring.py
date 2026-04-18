"""JD Tailoring node — generates or tunes a resume for a specific JD."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert resume writer specializing in tailoring resumes for specific job descriptions.

Given the parsed JD and the candidate's career assets (or an existing resume for tuning),
generate a tailored resume and evaluate the match.

{mode_instruction}

## Output Format
Return a JSON object with:
{{
  "resume": {{
    "summary": "Professional summary tailored to the role",
    "skills": ["list of skills highlighting JD requirements"],
    "experiences": [{{"company": "...", "title": "...", "period": "...", "description": "..."}}],
    "projects": [{{"name": "...", "description": "...", "tech_stack": [], "highlights": []}}],
    "highlights": ["2-3 key highlights relevant to the JD"],
    "metrics": [{{"description": "...", "value": "..."}}],
    "interview_points": ["talking points for interviews"]
  }},
  "scores": {{
    "ability_match_score": 0.0-1.0,
    "resume_match_score": 0.0-1.0,
    "readiness_score": 0.0-1.0,
    "recommendation": "apply_now|tune_then_apply|fill_gap_first|not_recommended",
    "missing_items": ["skills or experience gaps"],
    "optimization_notes": ["suggestions for improvement"]
  }}
}}

Be honest — never fabricate experience. Quantify achievements where possible.
Return ONLY the JSON object, no other text.
"""

_GENERATE_INSTRUCTION = """\
Mode: GENERATE NEW RESUME
Use the candidate's career assets (achievements, roles, skills) to create a resume
from scratch that maximizes the match with the JD.
"""

_TUNE_INSTRUCTION = """\
Mode: TUNE EXISTING RESUME
Optimize the existing resume to better match the JD. Keep the structure but:
- Reorder and emphasize relevant experience
- Add JD keywords naturally
- Strengthen weak descriptions
- Adjust the summary to target this specific role
"""


async def jd_tailoring(state: CareerAgentState) -> dict:
    """Generate or tune a resume for a specific JD.

    Handles two modes: generate_new (from career assets) and tune_existing.
    Also calculates match scores.
    """
    jd_parsed = state.get("jd_parsed") or {}
    jd_mode = state.get("jd_mode", "generate_new")
    career_assets = state.get("career_assets") or {}
    base_resume_content = state.get("base_resume_content") or {}
    review_artifact = state.get("jd_review_artifact")

    role_name = jd_parsed.get("role_name", "Unknown Role")
    required_skills = jd_parsed.get("required_skills", [])

    # Build mode-specific instruction
    mode_instruction = _GENERATE_INSTRUCTION if jd_mode == "generate_new" else _TUNE_INSTRUCTION

    # Build user prompt with JD and career data
    user_parts = [
        f"Target Role: {role_name}",
        f"Required Skills: {', '.join(required_skills)}",
        f"\nParsed JD:\n{json.dumps(jd_parsed, ensure_ascii=False, indent=2)}",
    ]

    if jd_mode == "generate_new" and career_assets:
        user_parts.append(
            f"\nCareer Assets:\n"
            f"{json.dumps(career_assets, ensure_ascii=False, indent=2)}"
        )
    elif jd_mode == "tune_existing" and base_resume_content:
        user_parts.append(
            f"\nCurrent Resume:\n"
            f"{json.dumps(base_resume_content, ensure_ascii=False, indent=2)}"
        )

    # Include review artifact for context-aware tailoring
    if review_artifact:
        user_parts.append(
            f"\nJD Review (use this to inform what to emphasize and gaps to address):\n"
            f"{json.dumps(review_artifact, ensure_ascii=False, indent=2)}"
        )

    user_prompt = "\n".join(user_parts)
    system_prompt = _SYSTEM_PROMPT.format(mode_instruction=mode_instruction)

    # Try LLM-based tailoring
    result = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("jd_tailoring")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        result = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM JD tailoring failed ({e}), using template fallback")

    # Fallback: template resume with JD keywords
    if not result:
        # Calculate basic scores
        user_skills = set()
        if career_assets:
            for ach in career_assets.get("achievements", []):
                user_skills.update(t.lower() for t in ach.get("tags", []))
            for role in career_assets.get("roles", []):
                user_skills.update(s.lower() for s in role.get("required_skills", []))

        matched_skills = [s for s in required_skills if s.lower() in user_skills]
        ability_score = (
            min(1.0, len(matched_skills) / max(1, len(required_skills)))
            if required_skills
            else 0.5
        )

        resume = base_resume_content if jd_mode == "tune_existing" and base_resume_content else {
            "summary": f"Experienced software engineer with relevant skills for {role_name}.",
            "skills": required_skills[:8],
            "experiences": [],
            "projects": [],
            "highlights": [],
            "metrics": [],
            "interview_points": [],
        }

        # Determine recommendation
        if ability_score >= 0.7:
            recommendation = "apply_now"
        elif ability_score >= 0.5:
            recommendation = "tune_then_apply"
        elif ability_score >= 0.3:
            recommendation = "fill_gap_first"
        else:
            recommendation = "not_recommended"

        missing = [s for s in required_skills if s.lower() not in user_skills][:5]

        result = {
            "resume": resume,
            "scores": {
                "ability_match_score": ability_score,
                "resume_match_score": ability_score * 0.9,
                "readiness_score": ability_score * 0.85,
                "recommendation": recommendation,
                "missing_items": missing,
                "optimization_notes": ["建议补充更多量化指标", "优化技能描述以匹配JD关键词"],
            },
        }

    # Extract resume and scores from result
    resume_draft = result.get("resume", result)
    scores = result.get("scores", {})

    # If result doesn't have nested structure, treat whole thing as resume
    if "scores" not in result and "resume" not in result:
        resume_draft = result
        scores = {
            "ability_match_score": 0.5,
            "resume_match_score": 0.5,
            "readiness_score": 0.5,
            "recommendation": "tune_then_apply",
            "missing_items": [],
            "optimization_notes": [],
        }

    return {
        "resume_draft": resume_draft,
        "match_scores": {
            "ability_match_score": scores.get("ability_match_score", 0.0),
            "resume_match_score": scores.get("resume_match_score", 0.0),
            "readiness_score": scores.get("readiness_score", 0.0),
            "recommendation": scores.get("recommendation", "not_recommended"),
            "missing_items": scores.get("missing_items", []),
            "optimization_notes": scores.get("optimization_notes", []),
        },
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "jd_tailoring",
                "action": "generated_tailored_resume",
                "mode": jd_mode,
                "role_name": role_name,
                "ability_score": scores.get("ability_match_score", 0.0),
            }
        ],
    }
