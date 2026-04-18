"""Project Selection node — selects best projects/experiences for the JD."""

from __future__ import annotations

import asyncio
import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_LLM_TIMEOUT = 60

_SYSTEM_PROMPT = """\
你是一位职业策略师，正在为定制简历筛选最佳内容。

根据JD关键词和候选人的职业经历，选出最匹配的项目和工作经历。

候选人职业经历（Markdown）：
{career_markdown}

JD关键词（按权重排序）：
{jd_keywords_json}

返回JSON对象：
{{
  "selected_experiences": [
    {{
      "company": "公司名",
      "title": "职位",
      "period": "时间段",
      "relevance_reason": "为什么相关",
      "keywords_matched": ["匹配的关键词"],
      "bullet_priorities": ["应强调的要点"]
    }}
  ],
  "selected_projects": [
    {{
      "name": "项目名",
      "source": "work_experience:公司名 或 standalone",
      "relevance_reason": "为什么相关",
      "keywords_matched": ["匹配的关键词"],
      "highlight_angles": ["描述角度"]
    }}
  ],
  "omitted_projects": [
    {{"name": "项目名", "reason": "省略原因"}}
  ],
  "coverage_notes": "整体匹配度评估"
}}

规则：
- 选3-4个项目和2-3段工作经历
- 优先匹配最高权重的关键词
- 绝不编造项目或经历
- 在coverage_notes中诚实说明覆盖缺口
- 只返回JSON，不要其他文字。"""


async def project_selection(state: CareerAgentState) -> dict:
    """Select best projects and experiences for the tailored resume."""
    jd_keywords = state.get("jd_keywords") or {}
    career_md = state.get("career_markdown") or ""
    career_assets = state.get("career_assets") or {}
    jd_mode = state.get("jd_mode", "generate_new")
    base_resume = state.get("base_resume_content") or {}

    # If tuning, the base resume IS the selection
    if jd_mode == "tune_existing" and base_resume:
        return {
            "selected_content": {
                "selected_experiences": base_resume.get("experiences", []),
                "selected_projects": base_resume.get("projects", []),
                "omitted_projects": [],
                "coverage_notes": "基于现有简历进行优化",
            },
            "agent_logs": state.get("agent_logs", []) + [{
                "node": "project_selection",
                "action": "selected_content",
                "selected_projects": len(base_resume.get("projects", [])),
            }],
        }

    kw_json = json.dumps(jd_keywords, ensure_ascii=False, indent=2)
    user_prompt = _SYSTEM_PROMPT.format(
        career_markdown=career_md or json.dumps(career_assets, ensure_ascii=False, indent=2),
        jd_keywords_json=kw_json,
    )
    system_prompt = "你是职业策略师，根据JD关键词筛选最佳项目和工作经历。只返回JSON。"

    result = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("project_selection")
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
        result = json.loads(content.strip())
    except asyncio.TimeoutError:
        logger.warning("[project_selection] LLM timed out")
    except Exception as e:
        logger.info(f"LLM project selection failed ({e}), using fallback")

    if not result:
        result = {
            "selected_experiences": [],
            "selected_projects": [],
            "omitted_projects": [],
            "coverage_notes": "Fallback: 全部内容纳入",
        }
        if career_assets:
            for ach in career_assets.get("achievements", [])[:6]:
                result["selected_projects"].append({
                    "name": ach.get("title", "Project"),
                    "source": "standalone",
                    "relevance_reason": "从已有成果中选择",
                    "keywords_matched": ach.get("tags", [])[:3],
                    "highlight_angles": [],
                })

    proj_count = len(result.get("selected_projects", []))
    return {
        "selected_content": result,
        "agent_logs": state.get("agent_logs", []) + [{
            "node": "project_selection",
            "action": "selected_content",
            "selected_projects": proj_count,
        }],
    }
