"""Resume Generation node — generates tailored resume with keyword injection."""

from __future__ import annotations

import asyncio
import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_LLM_TIMEOUT = 90

_SYSTEM_PROMPT = """\
你是一位资深简历撰写专家，专门针对特定JD定制简历。

根据JD关键词、筛选内容和候选人完整经历，生成一份高度定制的简历。

## 关键词注入规则（必须遵守）：
1. Summary中必须自然融入前5个关键词
2. 每段工作经历的第一条bullet必须包含一个匹配的关键词
3. Skills区域必须覆盖所有关键词
4. 只用JD的精确词汇重新表述真实经验
5. 绝不能添加候选人没有的技能或经验

## JD关键词（按权重排序）：
{jd_keywords_json}

## 筛选出的重点内容：
{selected_content_json}

## 候选人完整经历：
{career_content}

## 输出格式（ResumeContent JSON）：
{{
  "summary": "针对该岗位的专业总结",
  "skills": ["技能列表，必须覆盖所有JD关键词"],
  "experiences": [
    {{
      "company": "公司",
      "title": "职位",
      "period": "时间段",
      "description": "bullet points，每条包含一个JD关键词"
    }}
  ],
  "projects": [
    {{
      "name": "项目名",
      "description": "项目描述",
      "tech_stack": [],
      "highlights": []
    }}
  ],
  "highlights": ["2-3个与JD相关的亮点"],
  "metrics": [{{"description": "...", "value": "..."}}],
  "interview_points": ["面试谈话要点"]
}}

规则：
- 诚实——绝不编造经历
- 尽可能量化成果
- 使用JD的语言和术语
- 每条经历bullet读起来自然同时包含关键词
- 只返回JSON对象，不要其他文字。"""


async def resume_generation(state: CareerAgentState) -> dict:
    """Generate a tailored resume with keyword injection."""
    jd_keywords = state.get("jd_keywords") or {}
    selected_content = state.get("selected_content") or {}
    career_md = state.get("career_markdown") or ""
    career_assets = state.get("career_assets") or {}
    jd_mode = state.get("jd_mode", "generate_new")
    base_resume = state.get("base_resume_content") or {}

    jd_kw_json = json.dumps(jd_keywords, ensure_ascii=False, indent=2)
    sel_json = json.dumps(selected_content, ensure_ascii=False, indent=2)
    career_content = career_md or json.dumps(career_assets, ensure_ascii=False, indent=2)

    user_prompt = _SYSTEM_PROMPT.format(
        jd_keywords_json=jd_kw_json,
        selected_content_json=sel_json,
        career_content=career_content,
    )
    system_prompt = "你是资深简历撰写专家。只返回JSON。"

    if jd_mode == "tune_existing" and base_resume:
        user_prompt += (
            f"\n\n## 当前简历（优化基础）：\n"
            f"{json.dumps(base_resume, ensure_ascii=False, indent=2)}"
        )

    resume_draft = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("resume_generation")
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
        resume_draft = json.loads(content.strip())
    except asyncio.TimeoutError:
        logger.warning("[resume_generation] LLM timed out")
    except Exception as e:
        logger.info(f"LLM resume generation failed ({e}), using fallback")

    if not resume_draft:
        keywords = jd_keywords.get("keywords", [])
        skill_names = [k["keyword"] for k in keywords if k.get("weight", 0) >= 0.5]
        resume_draft = {
            "summary": f"具有相关经验的软件工程师，擅长 {', '.join(skill_names[:3])}。",
            "skills": skill_names[:12],
            "experiences": [],
            "projects": [],
            "highlights": [],
            "metrics": [],
            "interview_points": [],
        }

    return {
        "resume_draft": resume_draft,
        "agent_logs": state.get("agent_logs", []) + [{
            "node": "resume_generation",
            "action": "generated_resume",
            "keyword_coverage": 0,
        }],
    }
