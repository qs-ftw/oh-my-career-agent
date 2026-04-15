"""Service for JD/name analysis preview — no side effects."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

_JD_ANALYZE_PROMPT = """\
You are an expert job description parser for software engineering roles.

Given the raw job description text, extract AND EXPAND structured information as JSON:
{
  "role_name": "Position title — use the SAME language as the input JD",
  "description": "A well-structured 200-500 character description. MUST be in the SAME language as the input JD. Expand abstract requirements into concrete ones. E.g. instead of '熟悉前端框架', write '精通 React 或 Vue，包括状态管理（Redux/Pinia）、组件设计模式、性能优化'. Be specific, concrete, and well-organized.",
  "required_skills": ["list of SPECIFIC, concrete required skills. Use English for technical terms/frameworks/tools (e.g. 'React', 'TypeScript', 'Python'), but add Chinese translation in parentheses when the input is Chinese (e.g. 'Deep Learning (深度学习)', 'System Design (系统设计)'). Each skill should be a distinct technology or tool."],
  "bonus_skills": ["same format as required_skills"],
  "keywords": ["important keywords in the SAME language as the input JD. Use English for technical terms with Chinese in parentheses when input is Chinese."]
}

Rules:
- OUTPUT LANGUAGE MUST MATCH THE INPUT LANGUAGE. If the JD is in Chinese, all free-text fields (role_name, description) must be in Chinese.
- required_skills and bonus_skills: use English for technical terms/frameworks, with Chinese translation in parentheses when input is Chinese. E.g. "Reinforcement Learning (强化学习)", "Distributed Systems (分布式系统)".
- description must EXPAND vague JD language into specific, concrete requirements
- Include both explicit and implicit requirements
- Return ONLY the JSON object, no other text
"""

_NAME_ANALYZE_PROMPT = """\
You are an expert career advisor who understands the software industry deeply.

Given a job title, generate a comprehensive analysis of what this role typically requires. Return JSON:
{
  "role_name": "The exact job title provided — same language as input",
  "description": "A well-structured 200-500 character description of typical responsibilities, requirements, and expectations. MUST be in the SAME language as the input title. Be specific about technologies, methodologies, and skills commonly required.",
  "required_skills": ["list of 8-12 SPECIFIC, concrete skills typically required. Use English for technical terms/frameworks/tools, with Chinese translation in parentheses when input is Chinese (e.g. 'Machine Learning (机器学习)', 'NLP (自然语言处理)'). Each should be a distinct technology, framework, or tool."],
  "bonus_skills": ["same format as required_skills, 4-6 items"],
  "keywords": ["8-12 important keywords in the SAME language as input. Use English for technical terms with Chinese in parentheses when input is Chinese."]
}

Rules:
- OUTPUT LANGUAGE MUST MATCH THE INPUT LANGUAGE. If the job title is in Chinese, all free-text fields (role_name, description) must be in Chinese.
- Skills: use English for technical terms/frameworks, with Chinese translation in parentheses when input is Chinese. E.g. "Computer Vision (计算机视觉)", "Kubernetes (K8s容器编排)".
- Description should reflect industry-standard expectations for this role level
- Consider the current technology landscape (2025-2026)
- Return ONLY the JSON object, no other text
"""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response that may be wrapped in ```json```."""
    content = text
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return json.loads(content.strip())


async def analyze_jd(raw_jd: str) -> dict:
    """Analyze a JD text and return structured preview data. No DB writes."""
    try:
        from src.core.llm import get_llm

        llm = get_llm("jd_parsing")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _JD_ANALYZE_PROMPT},
                {"role": "user", "content": f"Parse this job description:\n\n{raw_jd}"},
            ]
        )
        parsed = _extract_json(response.content)
    except Exception as e:
        logger.warning(f"LLM JD analysis failed ({e}), returning minimal result")
        parsed = {
            "role_name": "Unknown Role",
            "description": raw_jd[:500] if len(raw_jd) > 500 else raw_jd,
            "required_skills": [],
            "bonus_skills": [],
            "keywords": [],
        }

    return {
        "role_name": parsed.get("role_name", ""),
        "role_type": "全职",
        "description": parsed.get("description", ""),
        "required_skills": parsed.get("required_skills", []),
        "bonus_skills": parsed.get("bonus_skills", []),
        "keywords": parsed.get("keywords", []),
    }


async def analyze_name(role_name: str) -> dict:
    """Analyze a role name and return typical JD data. No DB writes."""
    try:
        from src.core.llm import get_llm

        llm = get_llm("jd_parsing")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _NAME_ANALYZE_PROMPT},
                {"role": "user", "content": f"Generate a typical job profile for: {role_name}"},
            ]
        )
        parsed = _extract_json(response.content)
    except Exception as e:
        logger.warning(f"LLM name analysis failed ({e}), returning minimal result")
        parsed = {
            "role_name": role_name,
            "description": "",
            "required_skills": [],
            "bonus_skills": [],
            "keywords": [],
        }

    return {
        "role_name": parsed.get("role_name", role_name),
        "role_type": "全职",
        "description": parsed.get("description", ""),
        "required_skills": parsed.get("required_skills", []),
        "bonus_skills": parsed.get("bonus_skills", []),
        "keywords": parsed.get("keywords", []),
    }
