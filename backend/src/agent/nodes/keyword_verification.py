"""Keyword Verification node — checks JD keyword coverage in the resume."""

from __future__ import annotations

import asyncio
import copy
import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_LLM_TIMEOUT = 60

_SYSTEM_PROMPT = """\
你是一位ATS优化审核员，验证简历中的关键词覆盖率。

检查每个JD关键词在简历中的出现情况。

## JD关键词：
{jd_keywords_json}

## 简历内容：
{resume_draft_json}

返回JSON对象：
{{
  "coverage_score": 0.0-1.0,
  "keyword_details": [
    {{
      "keyword": "Kubernetes",
      "weight": 0.95,
      "covered": true,
      "location": "skills, experience[0].bullet[2]",
      "coverage_quality": "explicit"
    }}
  ],
  "total_keywords": 18,
  "covered_keywords": 15,
  "uncovered_keywords": ["keyword1"],
  "patches": [
    {{
      "keyword": "...",
      "suggestion": "在skills中添加该关键词",
      "target_section": "skills",
      "suggested_text": "具体文本"
    }}
  ],
  "overall_assessment": "简要评估"
}}

coverage_quality: "explicit"(精确匹配) | "implicit"(语义匹配) | "missing"(未覆盖)
只返回JSON，不要其他文字。"""


def _simple_coverage_check(jd_keywords: dict, resume_draft: dict) -> dict:
    """Fallback: string-based keyword coverage check."""
    resume_text = json.dumps(resume_draft, ensure_ascii=False).lower()
    keywords = jd_keywords.get("keywords", [])

    keyword_details = []
    covered = 0
    patches = []

    for kw in keywords:
        keyword = kw.get("keyword", "")
        weight = kw.get("weight", 0.5)
        is_covered = keyword.lower() in resume_text
        if is_covered:
            covered += 1
        else:
            patches.append({
                "keyword": keyword,
                "suggestion": f"在简历中添加 '{keyword}'",
                "target_section": "skills",
                "suggested_text": keyword,
            })
        keyword_details.append({
            "keyword": keyword,
            "weight": weight,
            "covered": is_covered,
            "location": "found in text" if is_covered else "not found",
            "coverage_quality": "explicit" if is_covered else "missing",
        })

    total = len(keywords)
    score = covered / max(1, total)
    return {
        "coverage_score": round(score, 2),
        "keyword_details": keyword_details,
        "total_keywords": total,
        "covered_keywords": covered,
        "uncovered_keywords": [k["keyword"] for k in keyword_details if not k["covered"]],
        "patches": patches,
        "overall_assessment": f"覆盖率 {score:.0%}，{total - covered} 个关键词未覆盖",
    }


def _apply_patches(resume_draft: dict, patches: list[dict]) -> dict:
    """Apply patches to resume for uncovered keywords."""
    patched = copy.deepcopy(resume_draft)
    skills = set(patched.get("skills", []))

    for patch in patches:
        section = patch.get("target_section", "skills")
        keyword = patch.get("keyword", "")
        if section == "skills" and keyword and keyword not in skills:
            skills.add(keyword)

    patched["skills"] = list(skills)
    return patched


async def keyword_verification(state: CareerAgentState) -> dict:
    """Verify keyword coverage and auto-patch if below threshold."""
    jd_keywords = state.get("jd_keywords") or {}
    resume_draft = state.get("resume_draft") or {}

    kw_json = json.dumps(jd_keywords, ensure_ascii=False, indent=2)
    resume_json = json.dumps(resume_draft, ensure_ascii=False, indent=2)
    user_prompt = _SYSTEM_PROMPT.format(
        jd_keywords_json=kw_json,
        resume_draft_json=resume_json,
    )
    system_prompt = "你是ATS优化审核员。只返回JSON。"

    coverage = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("keyword_verification")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]),
            timeout=_LLM_TIMEOUT,
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        coverage = json.loads(content.strip())
    except asyncio.TimeoutError:
        logger.warning("[keyword_verification] LLM timed out")
    except Exception as e:
        logger.info(f"LLM keyword verification failed ({e}), using fallback")

    if not coverage:
        coverage = _simple_coverage_check(jd_keywords, resume_draft)

    resume_patches = coverage.get("patches", [])
    patched_resume = resume_draft

    # Auto-patch if coverage < 0.7, then re-check once
    if coverage.get("coverage_score", 0) < 0.7 and resume_patches:
        patched_resume = _apply_patches(resume_draft, resume_patches)
        recheck = _simple_coverage_check(jd_keywords, patched_resume)
        if recheck["coverage_score"] > coverage.get("coverage_score", 0):
            coverage = recheck
            logger.info(
                f"[keyword_verification] Auto-patched: "
                f"{coverage.get('coverage_score', 0):.0%} coverage"
            )

    return {
        "resume_draft": patched_resume,
        "keyword_coverage": coverage,
        "resume_patches": resume_patches,
        "agent_logs": state.get("agent_logs", []) + [{
            "node": "keyword_verification",
            "action": "verified_keywords",
            "coverage_score": coverage.get("coverage_score", 0),
        }],
    }
