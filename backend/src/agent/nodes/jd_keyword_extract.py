"""JD Keyword Extract node — extracts weighted keywords from parsed JD."""

from __future__ import annotations

import asyncio
import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_LLM_TIMEOUT = 60

_SYSTEM_PROMPT = """\
你是一位ATS（申请人追踪系统）关键词分析专家。

根据解析后的职位描述，提取15-20个核心关键词，用于指导简历定制。

返回JSON对象：
{
  "keywords": [
    {"keyword": "Kubernetes", "weight": 0.95, "category": "technical"},
    {"keyword": "分布式系统", "weight": 0.85, "category": "domain"},
    {"keyword": "团队协作", "weight": 0.6, "category": "soft_skill"}
  ],
  "language": "zh",
  "archetype": "backend_engineer",
  "experience_level": "senior"
}

规则：
- 提取15-20个关键词
- weight: 1.0=必须, 0.5=加分
- category: "technical", "domain", "soft_skill", "methodology", "tool", "certification"
- 包含显式技能和隐式领域关键词
- 按weight降序排列
- 只返回JSON，不要其他文字。"""


async def jd_keyword_extract(state: CareerAgentState) -> dict:
    """Extract weighted keywords from parsed JD for ATS optimization."""
    jd_parsed = state.get("jd_parsed") or {}

    user_prompt = (
        f"解析后的职位描述：\n"
        f"{json.dumps(jd_parsed, ensure_ascii=False, indent=2)}"
    )

    result = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("jd_keyword_extract")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]),
            timeout=_LLM_TIMEOUT,
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        result = json.loads(content.strip())
    except asyncio.TimeoutError:
        logger.warning("[jd_keyword_extract] LLM timed out")
    except Exception as e:
        logger.info(f"LLM keyword extract failed ({e}), using fallback")

    if not result:
        required = jd_parsed.get("required_skills", [])
        bonus = jd_parsed.get("bonus_items", [])
        keywords = jd_parsed.get("keywords", [])
        style = jd_parsed.get("style", {})

        kw_list = []
        for i, s in enumerate(required[:10]):
            kw_list.append({"keyword": s, "weight": round(0.95 - i * 0.03, 2), "category": "technical"})
        for i, s in enumerate(bonus[:5]):
            kw_list.append({"keyword": s, "weight": round(0.6 - i * 0.05, 2), "category": "technical"})
        for i, s in enumerate(keywords[:5]):
            if not any(k["keyword"] == s for k in kw_list):
                kw_list.append({"keyword": s, "weight": 0.5, "category": "domain"})

        result = {
            "keywords": kw_list[:20],
            "language": "zh",
            "archetype": "backend_engineer",
            "experience_level": style.get("experience_level", "mid"),
        }

    return {
        "jd_keywords": result,
        "agent_logs": state.get("agent_logs", []) + [{
            "node": "jd_keyword_extract",
            "action": "extracted_keywords",
            "keyword_count": len(result.get("keywords", [])),
        }],
    }
