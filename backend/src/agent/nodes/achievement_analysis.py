"""Achievement Analysis node — extracts structured data from raw achievement text."""

from __future__ import annotations

import json
import logging

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
你是一位资深职业教练，正在分析一位软件工程师的工作成果。

根据原始成果文本，提取结构化信息，以 JSON 格式返回：
{
  "summary": "成果的一段话精炼摘要",
  "technical_points": [{"point": "涉及的技术、模式或架构决策"}],
  "challenges": [{"challenge": "遇到的问题及其背景"}],
  "solutions": [{"solution": "如何解决该问题"}],
  "metrics": [{"metric": "可量化的成果", "value": "具体数字或百分比"}],
  "interview_points": [{"point": "在行为面试中如何表述该成果"}],
  "tags": ["相关", "技能", "标签"],
  "importance_score": 0.0-1.0
}

要求：
- 所有文本字段必须使用中文
- 具体且实用，提取真实的技术细节和可量化结果
- 只返回 JSON 对象，不要其他文字
"""


async def achievement_analysis(state: CareerAgentState) -> dict:
    """Parse raw achievement text into a structured achievement object.

    Error handling strategy:
    - LLM timeout/network errors → propagate (not recoverable)
    - JSON parse errors → fallback to basic keyword extraction (recoverable)
    """
    achievement_raw = state.get("achievement_raw", "")

    user_prompt = f"Analyze this achievement:\n\n{achievement_raw}"

    logs = list(state.get("agent_logs", []))

    # Try LLM-based analysis
    parsed = None
    llm_error = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("achievement_analysis")
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
        parsed = json.loads(content.strip())
    except json.JSONDecodeError as e:
        # Recoverable: LLM returned non-JSON, use fallback
        logger.warning(f"LLM returned non-JSON for achievement analysis: {e}")
        logs.append({
            "node": "achievement_analysis",
            "level": "warning",
            "message": f"LLM response was not valid JSON, using fallback: {e}",
        })
    except Exception as e:
        # Severe: timeout, network error, API error — must propagate
        error_type = type(e).__name__
        logger.error(f"LLM achievement analysis failed ({error_type}): {e}")
        llm_error = f"{error_type}: {e}"

    # Fallback: basic keyword extraction (only for recoverable errors)
    if not parsed:
        raw_lower = achievement_raw.lower()
        common_techs = [
            "python", "javascript", "typescript", "react", "vue", "go", "rust", "java",
            "kafka", "redis", "postgresql", "mysql", "mongodb", "docker", "kubernetes",
            "aws", "gcp", "azure", "fastapi", "django", "flask", "node",
            "microservice", "api", "ci/cd", "devops", "testing",
        ]
        tags = [t for t in common_techs if t in raw_lower]

        parsed = {
            "summary": achievement_raw[:300] if len(achievement_raw) > 300 else achievement_raw,
            "technical_points": [],
            "challenges": [],
            "solutions": [],
            "metrics": [],
            "interview_points": [],
            "tags": tags[:5],
            "importance_score": 0.5,
        }

    result_logs = logs + [
        {
            "node": "achievement_analysis",
            "action": "parsed_achievement",
            "tags_count": len(parsed.get("tags", [])),
            "metrics_count": len(parsed.get("metrics", [])),
        }
    ]

    result = {
        "achievement_parsed": parsed,
        "agent_logs": result_logs,
    }

    # Propagate LLM errors so the service layer can decide what to do
    if llm_error:
        result["pipeline_error"] = llm_error

    return result
