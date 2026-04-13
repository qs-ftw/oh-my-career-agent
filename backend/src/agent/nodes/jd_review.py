"""JD Review node — produces structured review artifact before tailoring."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState
from src.prompts.jd_review import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def jd_review(state: CareerAgentState) -> dict:
    """Produce a structured JD review artifact.

    Analyzes the parsed JD against the candidate's profile and career assets
    to produce an evidence-based review with gap analysis and recommendations.
    """
    jd_parsed = state.get("jd_parsed") or {}
    candidate_profile = state.get("candidate_profile") or {}
    career_assets = state.get("career_assets") or {}

    role_name = jd_parsed.get("role_name", "Unknown Role")

    user_parts = [
        f"Parsed JD:\n{json.dumps(jd_parsed, ensure_ascii=False, indent=2)}",
    ]

    if candidate_profile:
        user_parts.append(
            f"\nCandidate Profile:\n{json.dumps(candidate_profile, ensure_ascii=False, indent=2)}"
        )

    if career_assets:
        user_parts.append(
            f"\nCareer Assets:\n{json.dumps(career_assets, ensure_ascii=False, indent=2)}"
        )

    user_prompt = "\n".join(user_parts)

    artifact = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("jd_review")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        artifact = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM JD review failed ({e}), using template fallback")

    if not artifact:
        required_skills = jd_parsed.get("required_skills", [])
        user_skills = set()
        if career_assets:
            for ach in career_assets.get("achievements", []):
                user_skills.update(t.lower() for t in ach.get("tags", []))
            for role in career_assets.get("roles", []):
                user_skills.update(s.lower() for s in role.get("required_skills", []))

        matched = [s for s in required_skills if s.lower() in user_skills]
        missing = [s for s in required_skills if s.lower() not in user_skills]
        match_pct = len(matched) / max(1, len(required_skills))

        if match_pct >= 0.7:
            rec = "apply_now"
        elif match_pct >= 0.5:
            rec = "tune_then_apply"
        elif match_pct >= 0.3:
            rec = "fill_gap_first"
        else:
            rec = "not_recommended"

        artifact = {
            "role_summary": {
                "title": role_name,
                "level": jd_parsed.get("style", {}).get("experience_level", "mid"),
                "team_context": "",
                "core_responsibilities": required_skills[:5],
            },
            "evidence_matrix": [
                {"requirement": s, "evidence_strength": "strong" if s.lower() in user_skills else "none", "evidence_refs": []}
                for s in required_skills[:10]
            ],
            "gap_analysis": [
                {"gap": s, "severity": "blocker" if i < 3 else "nice_to_have", "suggested_action": f"准备{s}相关经验或项目"}
                for i, s in enumerate(missing[:5])
            ],
            "personalization_plan": [
                {"focus_area": "技能匹配", "strategy": "突出匹配的技能", "keywords_to_emphasize": matched[:5]},
            ],
            "interview_plan": [],
            "recommendation_summary": {
                "recommendation": rec,
                "reasoning": f"匹配率 {match_pct:.0%}",
                "key_strengths": matched[:3],
                "key_concerns": missing[:3],
            },
        }

    return {
        "jd_review_artifact": artifact,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "jd_review",
                "action": "reviewed_jd",
                "role_name": role_name,
                "recommendation": artifact.get("recommendation_summary", {}).get("recommendation", ""),
            }
        ],
    }
