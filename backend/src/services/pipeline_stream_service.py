"""Pipeline streaming service — wraps LangGraph astream_events into SSE events."""

from __future__ import annotations

import json
import time
import logging
from collections.abc import AsyncGenerator

from langgraph.pregel import Pregel
from sse_starlette.sse import ServerSentEvent

logger = logging.getLogger(__name__)

_NODE_LABELS: dict[str, str] = {
    "achievement_analysis": "正在解析成果...",
    "role_matching": "正在匹配目标岗位...",
    "resume_update": "正在生成简历更新建议...",
    "gap_evaluation": "正在评估技能差距...",
    "explain": "正在生成分析总结...",
    "jd_parsing": "正在解析职位描述...",
    "jd_review": "正在深度分析JD...",
    "jd_tailoring": "正在定制简历...",
    "jd_keyword_extract": "正在提取JD关键词...",
    "project_selection": "正在筛选最佳项目经验...",
    "resume_generation": "正在生成定制简历...",
    "keyword_verification": "正在验证关键词覆盖率...",
    "capability_modeling": "正在构建能力模型...",
    "resume_init": "正在生成初始简历...",
}

_CHAIN_START = "on_chain_start"
_CHAIN_END = "on_chain_end"
_LLM_STREAM = "on_llm_new_token"


async def stream_pipeline(
    graph: Pregel,
    input_data: dict,
    *,
    node_labels: dict[str, str] | None = None,
    result_container: dict | None = None,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Run a LangGraph pipeline and yield ServerSentEvent objects.

    If *result_container* is provided, the final pipeline state dict is stored
    under ``result_container["output"]`` after streaming completes.
    """
    labels = {**_NODE_LABELS, **(node_labels or {})}
    node_start_times: dict[str, float] = {}
    current_node: str | None = None

    # Accumulate partial state from node outputs so we can reconstruct
    # the final result without re-running the pipeline.
    accumulated: dict = {
        "achievement_parsed": None,
        "role_matches": [],
        "suggestions": [],
        "gap_updates": [],
        "agent_logs": [],
    }

    try:
        async for event in graph.astream_events(
            input_data,
            version="v2",
            include_names=list(labels.keys()),
        ):
            kind = event["event"]
            name = event.get("name", "")

            if kind == _CHAIN_START and name in labels:
                current_node = name
                node_start_times[name] = time.monotonic()
                yield _sse("node_start", {
                    "node": name,
                    "label": labels[name],
                })

            elif kind == _LLM_STREAM and current_node:
                chunk = event.get("data", {}).get("chunk")
                if chunk:
                    text = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if text:
                        yield _sse("token", {
                            "node": current_node,
                            "text": text,
                        })

            elif kind == _CHAIN_END and name in labels:
                duration_ms = int((time.monotonic() - node_start_times.get(name, time.monotonic())) * 1000)
                output = event.get("data", {}).get("output", {})
                # Merge node output into accumulated state
                if isinstance(output, dict):
                    for key, value in output.items():
                        if value is not None:
                            accumulated[key] = value
                summary = _node_summary(name, output)
                yield _sse("node_complete", {
                    "node": name,
                    "duration_ms": duration_ms,
                    "summary": summary,
                })
                if current_node == name:
                    current_node = None

    except Exception as e:
        logger.error(f"Pipeline stream error: {e}")
        yield _sse("pipeline_error", {"error": str(e)})

    yield _sse("pipeline_complete", {})

    # Populate result_container with the accumulated final state
    if result_container is not None:
        # Merge the initial input with any accumulated outputs
        result_container["output"] = {**input_data, **accumulated}


def _sse(event_type: str, data: dict) -> ServerSentEvent:
    """Create a ServerSentEvent object."""
    return ServerSentEvent(event=event_type, data=json.dumps(data, ensure_ascii=False))


def _node_summary(node: str, output: dict) -> str:
    """Extract a short summary from a node's output."""
    logs = output.get("agent_logs", [])
    if logs:
        last_log = logs[-1] if isinstance(logs, list) else logs
        if isinstance(last_log, dict):
            action = last_log.get("action", "")
            if action == "parsed_achievement":
                tags_count = last_log.get("tags_count", 0)
                return f"解析完成，提取了 {tags_count} 个标签"
            if action == "matched_roles":
                return f"匹配了 {last_log.get('match_count', 0)} 个岗位"
            if action == "generated_suggestions":
                return f"生成了 {last_log.get('suggestions_count', 0)} 条建议"
            if action == "evaluated_gaps_for_achievement":
                return f"评估了 {last_log.get('roles_evaluated', 0)} 个岗位的差距"
            if action == "generated_tailored_resume":
                score = last_log.get("ability_score", 0)
                return f"匹配度 {score:.0%}"
            if action == "extracted_keywords":
                return f"提取了 {last_log.get('keyword_count', 0)} 个关键词"
            if action == "selected_content":
                return f"筛选了 {last_log.get('selected_projects', 0)} 个项目"
            if action == "verified_keywords":
                score = last_log.get("coverage_score", 0)
                return f"关键词覆盖率 {score:.0%}"
    return "完成"
