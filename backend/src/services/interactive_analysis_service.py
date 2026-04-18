"""Interactive analysis service — multi-turn conversational achievement enrichment."""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.profile import CareerProfile

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
你是一位热情、温暖、鼓励型的职业教练，正在通过轻松对话帮助用户把一条工作成果做"厚"做"扎实"。你对用户的每一个分享都给予真诚的肯定和赞赏。

## 你的工作方式：
1. 先阅读用户已有的成果内容，分析哪些关键信息缺失
2. 针对**具体缺失的内容**提出追问，每次1-2个问题
3. 问题必须**基于已有内容定制**，不能使用固定模板
4. 每个问题之后，提供1-2个发散方向帮助用户回忆和组织信息
5. 当信息足够丰富时，热情地告诉用户可以生成最终成果了

## 你绝不能做的事：
- 编造用户没有提到的技术、数据或细节
- 猜测量化数据（如性能提升百分比）
- 使用固定的"你遇到了什么挑战"之类的模板问题
- 在用户明确表示不知道时继续追问同一方向
- 回复以陈述句结尾——你要问问题就必须用问号结尾

## 判断信息充分度的标准：
- S(情境): 是否有背景信息（项目/团队/业务场景）
- T(任务): 是否有明确的目标或问题
- A(行动): 是否有具体的技术方案和决策过程
- R(结果): 是否有可量化的成果或业务影响

## 重要规则：
- 你的回复必须包含真正的问句（以"？"结尾），不能只有陈述句
- 每问完问题后，紧跟1-2个发散提示帮助用户思考（例如："比如你可以聊聊用了什么设计模式、做了哪些技术选型、或者遇到了什么坑"）
- 肯定用户分享的每一条信息，让用户感受到你在认真倾听
- 当用户表示"够了"、"差不多了"、"可以了"、"OK"等意愿时，立即设置 ready_to_generate 为 true
- 对话超过4轮（用户回复4次以上）时，主动建议生成成果

## 输出格式：
每次回复都用以下JSON格式：
{
  "reply": "你的回复，包含肯定+追问+发散提示",
  "questions": ["问题1？", "问题2？"],
  "divergence_hints": ["发散提示1，例如：可以聊聊技术选型的考量", "发散提示2，例如：有没有用什么设计模式"],
  "sufficiency": {
    "situation": 0.0-1.0,
    "task": 0.0-1.0,
    "action": 0.0-1.0,
    "result": 0.0-1.0
  },
  "ready_to_generate": false,
  "content_update": "从用户最新回复中提炼的内容摘要，可直接追加到成果描述中（如果没有新信息则为null）",
  "suggestions": [
    {"suggestion": "可以回测QPS变化获取量化数据", "category": "metrics"}
  ]
}

如果用户表示无法提供某方面信息，在suggestions中给出获取该信息的具体建议。
当四个维度都>=0.7时，设置 ready_to_generate 为 true。
当用户主动表示够了/差不多了，也设置 ready_to_generate 为 true。
超过4轮对话，主动建议生成并设置 ready_to_generate 为 true。

只返回JSON，不要其他文字。"""

_GENERATE_PROMPT = """\
根据对话中收集的所有信息，生成最终的打磨成果。

## 对话记录：
{chat_history}

## 原始成果内容：
{raw_content}

返回JSON：
{{
  "narrative": "一段完整的叙事体描述，像讲一个故事，200-400字。包含背景、挑战、方案、结果，读起来自然流畅",
  "bullets": [
    "• 背景：...",
    "• 挑战：...",
    "• 方案：...",
    "• 成果：..."
  ],
  "tags": ["标签1", "标签2"],
  "importance_score": 0.0-1.0,
  "suggestions": [
    {{"suggestion": "建议内容", "category": "metrics|context|decision|impact"}}
  ]
}}

要求：
- narrative 用自然流畅的中文，像在面试中讲述一样
- bullets 用简洁的要点形式，每个要点一句话
- 只使用对话中用户明确提到的信息，绝不编造
- suggestions 中给出让成果更扎实建议（如果有）
- 只返回JSON"""

_MAX_ROUNDS = 5  # After this many user messages, force ready_to_generate
_LLM_TIMEOUT = 60


async def _load_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> Achievement | None:
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _build_chat_history(chat: list[dict]) -> str:
    """Format chat history for LLM prompt."""
    parts = []
    for msg in chat:
        role = "教练" if msg.get("role") == "ai" else "用户"
        content = msg.get("content", "")
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def _parse_json_response(content: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown code blocks."""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    return json.loads(content.strip())


def _count_user_rounds(chat: list[dict]) -> int:
    """Count how many times the user has sent a message."""
    return sum(1 for m in chat if m.get("role") == "user")


async def start_interactive_analysis(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> dict | None:
    """Start a new interactive analysis session. Returns the AI's opening message."""
    import asyncio
    from src.core.llm import get_llm

    achievement = await _load_achievement(session, user_id, achievement_id)
    if achievement is None:
        return None

    # Build initial context
    raw = achievement.raw_content or ""
    title = achievement.title
    initial_context = f"成果标题：{title}\n已有内容：{raw or '（暂无详细描述）'}"

    user_prompt = f"请分析这条成果，告诉我哪些信息缺失，并提出你的第一个问题。\n\n{initial_context}"

    try:
        llm = get_llm("interactive_analysis")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]),
            timeout=_LLM_TIMEOUT,
        )
        parsed = _parse_json_response(response.content)
    except Exception as e:
        logger.warning(f"[interactive_analysis] Start failed: {e}")
        parsed = None

    if not parsed:
        parsed = {
            "reply": "太棒了！这条成果很有价值，我来帮你把它打磨得更出彩。能先聊聊这个项目的背景是什么吗？当时团队面临什么样的挑战呢？\n\n💡 提示：可以聊聊项目的业务场景、团队规模、或者你在其中的角色",
            "questions": ["这个项目的背景和业务场景是什么？", "当时团队面临什么样的挑战？"],
            "divergence_hints": ["可以聊聊项目的业务场景和团队规模", "可以分享你在项目中的具体角色和职责"],
            "sufficiency": {"situation": 0.0, "task": 0.0, "action": 0.0, "result": 0.0},
            "ready_to_generate": False,
            "suggestions": [],
        }

    # Build reply with divergence hints
    reply_text = parsed.get("reply", "")
    hints = parsed.get("divergence_hints", [])
    if hints and "💡" not in reply_text:
        reply_text += "\n\n💡 " + " | ".join(hints)

    # Save initial chat
    chat_entry = [
        {"role": "ai", "content": reply_text},
    ]
    achievement.analysis_chat = chat_entry
    achievement.enrichment_suggestions = parsed.get("suggestions", []) or []
    await session.flush()

    return {
        "reply": reply_text,
        "questions": parsed.get("questions", []),
        "sufficiency": parsed.get("sufficiency", {}),
        "ready_to_generate": parsed.get("ready_to_generate", False),
    }


async def send_chat_message(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
    message: str,
) -> dict | None:
    """Send a user message in the interactive analysis chat."""
    import asyncio
    from src.core.llm import get_llm

    achievement = await _load_achievement(session, user_id, achievement_id)
    if achievement is None:
        return None

    chat = list(achievement.analysis_chat or [])

    # Add user message
    chat.append({"role": "user", "content": message})

    # Check if we should force ready (user says "够了" or max rounds)
    user_rounds = _count_user_rounds(chat)
    force_ready = user_rounds >= _MAX_ROUNDS
    lower_msg = message.lower().strip()
    user_wants_stop = any(kw in lower_msg for kw in ["够了", "差不多了", "可以了", "ok", "好", "行了", "就这样", "生成吧", "直接生成"])

    if force_ready or user_wants_stop:
        # Auto-generate instead of continuing chat
        chat.append({"role": "ai", "content": "太好了！我觉得信息已经很充分了，让我来帮你生成最终成果吧！" if user_wants_stop else "我们已经聊了很多了，让我来帮你整理一下成果吧！"})
        achievement.analysis_chat = chat
        await session.flush()
        return {
            "reply": chat[-1]["content"],
            "questions": [],
            "sufficiency": {"situation": 0.8, "task": 0.8, "action": 0.8, "result": 0.8},
            "ready_to_generate": True,
        }

    # Build conversation for LLM
    chat_history = _build_chat_history(chat)
    raw = achievement.raw_content or ""
    title = achievement.title

    round_hint = f"\n\n注意：用户已经回复了{user_rounds}次，{'如果信息已经基本充分就建议生成' if user_rounds >= 3 else '继续深入了解'}。"

    user_prompt = (
        f"成果标题：{title}\n"
        f"原始内容：{raw or '（暂无详细描述）'}\n\n"
        f"对话历史：\n{chat_history}\n"
        f"{round_hint}\n"
        f"请继续对话。"
    )

    try:
        llm = get_llm("interactive_analysis")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]),
            timeout=_LLM_TIMEOUT,
        )
        parsed = _parse_json_response(response.content)
    except Exception as e:
        logger.warning(f"[interactive_analysis] Chat failed: {e}")
        parsed = None

    if not parsed:
        parsed = {
            "reply": "抱歉，处理出了点问题，请再试一次吧~",
            "questions": [],
            "sufficiency": {"situation": 0.5, "task": 0.5, "action": 0.5, "result": 0.5},
            "ready_to_generate": False,
            "suggestions": [],
        }

    # Build reply with divergence hints
    reply_text = parsed.get("reply", "")
    hints = parsed.get("divergence_hints", [])
    if hints and "💡" not in reply_text:
        reply_text += "\n\n💡 " + " | ".join(hints)

    # Add AI reply to chat
    chat.append({"role": "ai", "content": reply_text})
    achievement.analysis_chat = chat

    # Update suggestions (merge, dedup)
    existing_suggestions = list(achievement.enrichment_suggestions or [])
    new_suggestions = parsed.get("suggestions", []) or []
    existing_texts = {s.get("suggestion", "") for s in existing_suggestions}
    for s in new_suggestions:
        if s.get("suggestion", "") not in existing_texts:
            existing_suggestions.append(s)
    achievement.enrichment_suggestions = existing_suggestions

    # Real-time content update: append new info to raw_content
    content_update = parsed.get("content_update")
    if content_update:
        current_raw = achievement.raw_content or ""
        if current_raw:
            achievement.raw_content = current_raw.rstrip() + "\n" + content_update
        else:
            achievement.raw_content = content_update

    # Force ready after max rounds
    if _count_user_rounds(chat) >= _MAX_ROUNDS:
        parsed["ready_to_generate"] = True
        reply_text += "\n\n我们已经聊得挺深入了，要不先生成看看效果？"
        chat[-1]["content"] = reply_text
        achievement.analysis_chat = chat

    await session.flush()

    return {
        "reply": reply_text,
        "questions": parsed.get("questions", []),
        "sufficiency": parsed.get("sufficiency", {}),
        "ready_to_generate": parsed.get("ready_to_generate", False),
    }


async def generate_final_result(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> dict | None:
    """Generate the final polished content from the chat history."""
    import asyncio
    from src.core.llm import get_llm

    achievement = await _load_achievement(session, user_id, achievement_id)
    if achievement is None:
        return None

    chat = achievement.analysis_chat or []
    chat_history = _build_chat_history(chat)
    raw = achievement.raw_content or ""

    user_prompt = _GENERATE_PROMPT.format(
        chat_history=chat_history or "（暂无对话记录，直接基于原始内容生成）",
        raw_content=raw or "（暂无）",
    )

    try:
        llm = get_llm("interactive_analysis")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": "你是成果打磨专家。只返回JSON。"},
                {"role": "user", "content": user_prompt},
            ]),
            timeout=90,
        )
        parsed = _parse_json_response(response.content)
    except Exception as e:
        logger.warning(f"[interactive_analysis] Generate failed: {e}")
        parsed = None

    if not parsed:
        parsed = {
            "narrative": raw or "",
            "bullets": [f"• {raw or ''}"],
            "tags": achievement.tags or [],
            "importance_score": achievement.importance_score or 0.5,
            "suggestions": [],
        }

    # Ensure all fields have valid values
    narrative = parsed.get("narrative") or raw or ""
    bullets = parsed.get("bullets") or [f"• {raw or ''}"]
    tags = parsed.get("tags") or achievement.tags or []
    importance_score = parsed.get("importance_score", achievement.importance_score or 0.5)

    # Save polished content
    achievement.polished_content = {
        "narrative": narrative,
        "bullets": bullets,
    }
    achievement.display_format = "narrative"
    achievement.importance_score = float(importance_score)
    if tags:
        achievement.tags = tags
    achievement.status = "analyzed"

    # Append generate message to chat
    chat.append({"role": "ai", "content": "成果已生成！你可以在右侧成果卡片中切换叙事体/要点体查看效果。"})

    # Merge final suggestions
    existing_suggestions = list(achievement.enrichment_suggestions or [])
    new_suggestions = parsed.get("suggestions") or []
    existing_texts = {s.get("suggestion", "") for s in existing_suggestions}
    for s in new_suggestions:
        if s.get("suggestion", "") not in existing_texts:
            existing_suggestions.append(s)
    achievement.enrichment_suggestions = existing_suggestions

    await session.flush()

    return {
        "narrative": narrative,
        "bullets": bullets,
        "tags": tags,
        "importance_score": float(importance_score),
        "suggestions": existing_suggestions,
    }
