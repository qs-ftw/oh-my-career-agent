# AI 互动剖析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a multi-turn conversational "AI 互动剖析" feature that interactively enriches achievements through context-aware questioning, as an alternative to the existing one-shot auto-analysis.

**Architecture:** New DB columns on `achievements` store conversation history, AI suggestions, and multi-format polished output. A new API endpoint pair handles chat turns (start session + send message). The LLM analyzes existing content, generates targeted follow-up questions based on what's missing (not templates), and eventually produces a polished achievement in both narrative and bullet formats. Frontend uses a side panel chat UI.

**Tech Stack:** FastAPI, SQLAlchemy async, LangChain ChatModels (via existing `get_llm`), PostgreSQL JSONB, React + TanStack Query, SSE for streaming chat responses

---

## File Structure

### New files:
- `backend/alembic/versions/20260416_01_add_interactive_analysis_fields.py` — Migration
- `backend/src/services/interactive_analysis_service.py` — Chat logic, LLM prompt construction, turn management
- `backend/src/api/interactive_analysis.py` — API endpoints for chat
- `frontend/src/components/portfolio/InteractiveAnalysisPanel.tsx` — Side panel chat UI
- `frontend/src/hooks/useInteractiveAnalysis.ts` — React hooks for chat API

### Modified files:
- `backend/src/models/achievement.py` — Add 4 new columns
- `backend/src/schemas/achievement.py` — Add new fields to response + update schemas
- `backend/src/services/achievement_service.py` — Update `_to_response` for new fields
- `backend/src/core/llm.py` — Add agent mapping
- `config.yaml` — Add agent model mapping
- `backend/src/main.py` — Register new router
- `frontend/src/types/index.ts` — Add new fields to Achievement interface
- `frontend/src/lib/api.ts` — Add chat API methods
- `frontend/src/pages/CareerPortfolio/ProjectDetail.tsx` — Add "互动剖析" button and panel
- `frontend/src/components/portfolio/AchievementExpandable.tsx` — Show polished content

---

### Task 1: Add new columns to Achievement model

**Files:**
- Modify: `backend/src/models/achievement.py`
- Create: `backend/alembic/versions/20260416_01_add_interactive_analysis_fields.py`

- [ ] **Step 1: Add columns to the model**

In `backend/src/models/achievement.py`, add after the `date_occurred` column (line 35):

```python
    # Interactive analysis fields
    analysis_chat: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    enrichment_suggestions: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    polished_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    display_format: Mapped[str] = mapped_column(String(20), nullable=False, default="raw")
```

- [ ] **Step 2: Create alembic migration**

```bash
cd backend && alembic revision -m "add_interactive_analysis_fields" --autogenerate
```

Review the generated migration. It should contain 4 `op.add_column` calls for `analysis_chat`, `enrichment_suggestions`, `polished_content`, `display_format` on `achievements`.

- [ ] **Step 3: Run migration**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 4: Verify**

```bash
cd backend && python -c "from src.models.achievement import Achievement; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/models/achievement.py backend/alembic/versions/
git commit -m "feat(model): add interactive analysis columns to achievements"
```

---

### Task 2: Update schemas and service for new fields

**Files:**
- Modify: `backend/src/schemas/achievement.py`
- Modify: `backend/src/services/achievement_service.py`

- [ ] **Step 1: Add fields to AchievementResponse**

In `backend/src/schemas/achievement.py`, add to `AchievementResponse` after `analysis_error`:

```python
    analysis_chat: list[dict[str, Any]] | None = None
    enrichment_suggestions: list[dict[str, Any]] | None = None
    polished_content: dict[str, Any] | None = None
    display_format: str = "raw"
```

- [ ] **Step 2: Add display_format to AchievementUpdate**

In `AchievementUpdate`, add:

```python
    display_format: str | None = None
```

- [ ] **Step 3: Update _to_response in achievement_service.py**

In `backend/src/services/achievement_service.py`, update `_to_response` to include new fields:

```python
def _to_response(a: Achievement, analysis_error: str | None = None) -> AchievementResponse:
    return AchievementResponse(
        id=a.id,
        profile_id=a.profile_id,
        project_id=a.project_id,
        work_experience_id=a.work_experience_id,
        title=a.title,
        raw_content=a.raw_content or "",
        parsed_data=a.parsed_data,
        tags=a.tags if isinstance(a.tags, list) else [],
        importance_score=a.importance_score,
        source_type=a.source_type,
        status=a.status,
        date_occurred=a.date_occurred,
        analysis_error=analysis_error,
        analysis_chat=a.analysis_chat,
        enrichment_suggestions=a.enrichment_suggestions,
        polished_content=a.polished_content,
        display_format=a.display_format or "raw",
        created_at=a.created_at,
    )
```

- [ ] **Step 4: Handle display_format in update_achievement**

In `update_achievement`, add after the existing tag update block:

```python
    if data.display_format is not None:
        achievement.display_format = data.display_format
```

- [ ] **Step 5: Verify**

```bash
cd backend && python -c "from src.schemas.achievement import AchievementResponse; print('OK')"
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/schemas/achievement.py backend/src/services/achievement_service.py
git commit -m "feat(schema): add interactive analysis fields to achievement response"
```

---

### Task 3: Register LLM agent mapping

**Files:**
- Modify: `backend/src/core/llm.py`
- Modify: `config.yaml`

- [ ] **Step 1: Add to _DEFAULT_CONFIG in llm.py**

In the `agents` dict, add:

```python
        "interactive_analysis": "default-openai",
```

- [ ] **Step 2: Add to config.yaml**

In the `agents` section, add after the existing entries:

```yaml
  # Interactive analysis
  interactive_analysis: glm-5-turbo
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/core/llm.py config.yaml
git commit -m "feat(llm): register interactive_analysis agent mapping"
```

---

### Task 4: Create interactive analysis service

**Files:**
- Create: `backend/src/services/interactive_analysis_service.py`

This is the core logic. The service manages the multi-turn chat, builds prompts with full conversation context, and decides when enough information has been gathered.

- [ ] **Step 1: Create the service file**

```python
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
你是一位资深职业教练和成果打磨专家，正在通过对话帮助用户把一条工作成果做"厚"做"扎实"。

## 你的工作方式：
1. 先阅读用户已有的成果内容，分析哪些关键信息缺失
2. 针对**具体缺失的内容**提出追问，每次1-2个问题
3. 问题必须**基于已有内容定制**，不能使用固定模板
4. 当信息足够丰富时，告诉用户可以生成最终成果

## 你绝不能做的事：
- 编造用户没有提到的技术、数据或细节
- 猜测量化数据（如性能提升百分比）
- 使用固定的"你遇到了什么挑战"之类的模板问题
- 在用户明确表示不知道时继续追问同一方向

## 判断信息充分度的标准：
- S(情境): 是否有背景信息（项目/团队/业务场景）
- T(任务): 是否有明确的目标或问题
- A(行动): 是否有具体的技术方案和决策过程
- R(结果): 是否有可量化的成果或业务影响

## 输出格式：
每次回复都用以下JSON格式：
{
  "reply": "你的回复，包含追问或确认",
  "questions": ["问题1", "问题2"],
  "sufficiency": {
    "situation": 0.0-1.0,
    "task": 0.0-1.0,
    "action": 0.0-1.0,
    "result": 0.0-1.0
  },
  "ready_to_generate": false,
  "suggestions": [
    {"suggestion": "可以回测QPS变化获取量化数据", "category": "metrics"}
  ]
}

如果用户表示无法提供某方面信息，在suggestions中给出获取该信息的具体建议。
当四个维度都>=0.7时，设置 ready_to_generate 为 true。

只返回JSON，不要其他文字。"""

_GENERATE_PROMPT = """\
根据对话中收集的所有信息，生成最终的打磨成果。

## 对话记录：
{chat_history}

## 原始成果内容：
{raw_content}

返回JSON：
{
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
    {"suggestion": "建议内容", "category": "metrics|context|decision|impact"}
  ]
}

要求：
- narrative 用自然流畅的中文，像在面试中讲述一样
- bullets 用简洁的要点形式，每个要点一句话
- 只使用对话中用户明确提到的信息，绝不编造
- suggestions 中给出让成果更扎实建议（如果有）
- 只返回JSON"""

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


async def start_interactive_analysis(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> dict:
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

    chat = [{"role": "system", "content": f"成果上下文：\n{initial_context}"}]

    user_prompt = "请分析这条成果，告诉我哪些信息缺失，并提出你的第一个问题。"

    try:
        llm = get_llm("interactive_analysis")
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
        parsed = json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[interactive_analysis] Start failed: {e}")
        parsed = {
            "reply": "我来帮你打磨这条成果。能先说说这个项目的背景是什么吗？当时团队面临什么问题？",
            "questions": ["项目背景是什么？", "当时遇到了什么问题？"],
            "sufficiency": {"situation": 0.0, "task": 0.0, "action": 0.0, "result": 0.0},
            "ready_to_generate": False,
            "suggestions": [],
        }

    # Save initial chat
    chat_entry = [
        {"role": "ai", "content": parsed.get("reply", "")},
    ]
    achievement.analysis_chat = chat_entry
    achievement.enrichment_suggestions = parsed.get("suggestions", [])
    await session.flush()

    return {
        "reply": parsed.get("reply", ""),
        "questions": parsed.get("questions", []),
        "sufficiency": parsed.get("sufficiency", {}),
        "ready_to_generate": parsed.get("ready_to_generate", False),
    }


async def send_chat_message(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
    message: str,
) -> dict:
    """Send a user message in the interactive analysis chat."""
    import asyncio
    from src.core.llm import get_llm

    achievement = await _load_achievement(session, user_id, achievement_id)
    if achievement is None:
        return None

    chat = achievement.analysis_chat or []

    # Add user message
    chat.append({"role": "user", "content": message})

    # Build conversation for LLM
    chat_history = _build_chat_history(chat)
    raw = achievement.raw_content or ""
    title = achievement.title

    user_prompt = (
        f"成果标题：{title}\n"
        f"原始内容：{raw or '（暂无详细描述）'}\n\n"
        f"对话历史：\n{chat_history}\n\n"
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
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[interactive_analysis] Chat failed: {e}")
        parsed = {
            "reply": "抱歉，处理出了问题。请再试一次。",
            "questions": [],
            "sufficiency": {"situation": 0.5, "task": 0.5, "action": 0.5, "result": 0.5},
            "ready_to_generate": False,
            "suggestions": [],
        }

    # Add AI reply to chat
    chat.append({"role": "ai", "content": parsed.get("reply", "")})
    achievement.analysis_chat = chat

    # Update suggestions (merge, dedup)
    existing_suggestions = achievement.enrichment_suggestions or []
    new_suggestions = parsed.get("suggestions", [])
    existing_texts = {s.get("suggestion", "") for s in existing_suggestions}
    for s in new_suggestions:
        if s.get("suggestion", "") not in existing_texts:
            existing_suggestions.append(s)
    achievement.enrichment_suggestions = existing_suggestions

    await session.flush()

    return {
        "reply": parsed.get("reply", ""),
        "questions": parsed.get("questions", []),
        "sufficiency": parsed.get("sufficiency", {}),
        "ready_to_generate": parsed.get("ready_to_generate", False),
    }


async def generate_final_result(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
) -> dict:
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
        chat_history=chat_history,
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
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[interactive_analysis] Generate failed: {e}")
        parsed = {
            "narrative": achievement.raw_content or "",
            "bullets": [f"• {achievement.raw_content or ''}"],
            "tags": achievement.tags or [],
            "importance_score": 0.5,
            "suggestions": [],
        }

    # Save polished content
    achievement.polished_content = {
        "narrative": parsed.get("narrative", ""),
        "bullets": parsed.get("bullets", []),
    }
    achievement.display_format = "narrative"
    achievement.importance_score = parsed.get("importance_score", achievement.importance_score)
    if parsed.get("tags"):
        achievement.tags = parsed["tags"]
    achievement.status = "analyzed"

    # Append generate message to chat
    chat.append({"role": "ai", "content": "✅ 成果已生成！你可以在详情页切换叙事体/要点体查看。"})

    # Merge final suggestions
    existing_suggestions = achievement.enrichment_suggestions or []
    new_suggestions = parsed.get("suggestions", [])
    existing_texts = {s.get("suggestion", "") for s in existing_suggestions}
    for s in new_suggestions:
        if s.get("suggestion", "") not in existing_texts:
            existing_suggestions.append(s)
    achievement.enrichment_suggestions = existing_suggestions

    await session.flush()

    return {
        "narrative": parsed.get("narrative", ""),
        "bullets": parsed.get("bullets", []),
        "tags": parsed.get("tags", []),
        "importance_score": parsed.get("importance_score", 0.5),
        "suggestions": existing_suggestions,
    }
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "from src.services.interactive_analysis_service import start_interactive_analysis, send_chat_message, generate_final_result; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/services/interactive_analysis_service.py
git commit -m "feat(service): add interactive analysis service for multi-turn achievement chat"
```

---

### Task 5: Create API endpoints

**Files:**
- Create: `backend/src/api/interactive_analysis.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: Create the API router**

```python
"""Interactive analysis endpoints — multi-turn conversational achievement enrichment."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id
from src.services import interactive_analysis_service

router = APIRouter(prefix="/achievements", tags=["interactive-analysis"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    reply: str
    questions: list[str]
    sufficiency: dict
    ready_to_generate: bool


class GenerateResponse(BaseModel):
    narrative: str
    bullets: list[str]
    tags: list[str]
    importance_score: float
    suggestions: list[dict]


@router.post(
    "/{achievement_id}/interactive/start",
    summary="Start interactive analysis session",
)
async def start_interactive(
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Start a new interactive analysis chat. AI reads existing content and asks first questions."""
    user_id = await get_current_user_id()
    result = await interactive_analysis_service.start_interactive_analysis(
        db, user_id, achievement_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result


@router.post(
    "/{achievement_id}/interactive/chat",
    summary="Send a message in interactive analysis",
)
async def send_chat(
    body: ChatMessageRequest,
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Send a user message and get AI's follow-up questions."""
    user_id = await get_current_user_id()
    result = await interactive_analysis_service.send_chat_message(
        db, user_id, achievement_id, body.message
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result


@router.post(
    "/{achievement_id}/interactive/generate",
    summary="Generate final polished content",
)
async def generate_final(
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    """Generate the final polished achievement from chat history."""
    user_id = await get_current_user_id()
    result = await interactive_analysis_service.generate_final_result(
        db, user_id, achievement_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result
```

- [ ] **Step 2: Register router in main.py**

Read `backend/src/main.py` and find where other routers are included. Add:

```python
from src.api.interactive_analysis import router as interactive_analysis_router
app.include_router(interactive_analysis_router, prefix="/api")
```

- [ ] **Step 3: Verify**

```bash
cd backend && python -c "from src.api.interactive_analysis import router; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/api/interactive_analysis.py backend/src/main.py
git commit -m "feat(api): add interactive analysis chat endpoints"
```

---

### Task 6: Update frontend types and API

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add fields to Achievement interface**

In `frontend/src/types/index.ts`, update the `Achievement` interface to add:

```typescript
export interface Achievement {
  // ... existing fields ...
  analysis_chat: Array<{ role: "ai" | "user"; content: string }> | null;
  enrichment_suggestions: Array<{ suggestion: string; category: string }> | null;
  polished_content: { narrative: string; bullets: string[] } | null;
  display_format: "raw" | "narrative" | "bullets";
}
```

Add new request/response types:

```typescript
export interface InteractiveChatResponse {
  reply: string;
  questions: string[];
  sufficiency: Record<string, number>;
  ready_to_generate: boolean;
}

export interface InteractiveGenerateResponse {
  narrative: string;
  bullets: string[];
  tags: string[];
  importance_score: number;
  suggestions: Array<{ suggestion: string; category: string }>;
}
```

- [ ] **Step 2: Add API methods**

In `frontend/src/lib/api.ts`, add to `achievementApi`:

```typescript
  interactiveStart: (id: string) =>
    apiClient.post(`/achievements/${id}/interactive/start`),
  interactiveChat: (id: string, message: string) =>
    apiClient.post(`/achievements/${id}/interactive/chat`, { message }),
  interactiveGenerate: (id: string) =>
    apiClient.post(`/achievements/${id}/interactive/generate`),
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): add interactive analysis types and API methods"
```

---

### Task 7: Create React hooks for interactive analysis

**Files:**
- Create: `frontend/src/hooks/useInteractiveAnalysis.ts`

- [ ] **Step 1: Create the hooks**

```typescript
import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { achievementApi } from "@/lib/api";
import type { InteractiveChatResponse } from "@/types";

export function useInteractiveAnalysis(achievementId: string | null) {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<Array<{ role: "ai" | "user"; content: string }>>([]);
  const [readyToGenerate, setReadyToGenerate] = useState(false);
  const [sufficiency, setSufficiency] = useState<Record<string, number>>({});

  const startMutation = useMutation({
    mutationFn: async () => {
      if (!achievementId) throw new Error("No achievement ID");
      const { data } = await achievementApi.interactiveStart(achievementId);
      return data as InteractiveChatResponse;
    },
    onSuccess: (data) => {
      setMessages([{ role: "ai", content: data.reply }]);
      setSufficiency(data.sufficiency);
      setReadyToGenerate(data.ready_to_generate);
    },
  });

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!achievementId) throw new Error("No achievement ID");
      const { data } = await achievementApi.interactiveChat(achievementId, message);
      return data as InteractiveChatResponse;
    },
    onSuccess: (data, message) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: message },
        { role: "ai", content: data.reply },
      ]);
      setSufficiency(data.sufficiency);
      setReadyToGenerate(data.ready_to_generate);
    },
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!achievementId) throw new Error("No achievement ID");
      const { data } = await achievementApi.interactiveGenerate(achievementId);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
  });

  const start = useCallback(() => startMutation.mutate(), [startMutation]);
  const sendMessage = useCallback(
    (msg: string) => chatMutation.mutate(msg),
    [chatMutation]
  );
  const generate = useCallback(() => generateMutation.mutate(), [generateMutation]);

  const reset = useCallback(() => {
    setMessages([]);
    setReadyToGenerate(false);
    setSufficiency({});
    startMutation.reset();
    chatMutation.reset();
    generateMutation.reset();
  }, [startMutation, chatMutation, generateMutation]);

  return {
    messages,
    readyToGenerate,
    sufficiency,
    isStarting: startMutation.isPending,
    isSending: chatMutation.isPending,
    isGenerating: generateMutation.isPending,
    start,
    sendMessage,
    generate,
    reset,
    isActive: messages.length > 0,
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useInteractiveAnalysis.ts
git commit -m "feat(hooks): add useInteractiveAnalysis hook for chat state management"
```

---

### Task 8: Create InteractiveAnalysisPanel component

**Files:**
- Create: `frontend/src/components/portfolio/InteractiveAnalysisPanel.tsx`

- [ ] **Step 1: Create the side panel component**

```tsx
import { useState, useRef, useEffect } from "react";
import { X, Loader2, Sparkles, Send, CheckCircle } from "lucide-react";
import { useInteractiveAnalysis } from "@/hooks/useInteractiveAnalysis";

interface InteractiveAnalysisPanelProps {
  achievementId: string;
  achievementTitle: string;
  onClose: () => void;
}

export function InteractiveAnalysisPanel({
  achievementId,
  achievementTitle,
  onClose,
}: InteractiveAnalysisPanelProps) {
  const {
    messages,
    readyToGenerate,
    sufficiency,
    isStarting,
    isSending,
    isGenerating,
    start,
    sendMessage,
    generate,
    reset,
    isActive,
  } = useInteractiveAnalysis(achievementId);

  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-start on mount
  useEffect(() => {
    if (!isActive) start();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || isSending) return;
    setInput("");
    sendMessage(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Sufficiency bar colors
  const barColor = (val: number) =>
    val >= 0.7 ? "bg-green-500" : val >= 0.4 ? "bg-yellow-500" : "bg-red-400";

  const DIMENSION_LABELS: Record<string, string> = {
    situation: "情境",
    task: "任务",
    action: "行动",
    result: "结果",
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[420px] flex flex-col bg-card border-l shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold">AI 互动剖析</h3>
          <p className="text-xs text-muted-foreground truncate">{achievementTitle}</p>
        </div>
        <button
          onClick={() => { reset(); onClose(); }}
          className="rounded p-1 hover:bg-muted transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Sufficiency indicators */}
      {Object.keys(sufficiency).length > 0 && (
        <div className="px-4 py-2 border-b bg-muted/30">
          <div className="grid grid-cols-4 gap-2">
            {Object.entries(sufficiency).map(([key, val]) => (
              <div key={key} className="text-center">
                <div className="text-xs text-muted-foreground mb-1">
                  {DIMENSION_LABELS[key] ?? key}
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${barColor(val)}`}
                    style={{ width: `${Math.round(val * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {isStarting && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在分析成果内容...
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            思考中...
          </div>
        )}
        {isGenerating && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在生成最终成果...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Ready to generate banner */}
      {readyToGenerate && !isGenerating && (
        <div className="px-4 py-2 border-t bg-green-50">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-xs text-green-700 flex-1">信息已充分，可以生成最终成果</span>
            <button
              onClick={generate}
              className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700"
            >
              <Sparkles className="h-3 w-3" />
              生成成果
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t px-4 py-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的回答..."
            rows={2}
            disabled={isSending || isGenerating || isStarting}
            className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isSending || isGenerating || isStarting}
            className="rounded-md bg-primary p-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        {!readyToGenerate && !isSending && !isStarting && (
          <button
            onClick={generate}
            className="mt-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            信息还不够？也可以现在就生成 →
          </button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/InteractiveAnalysisPanel.tsx
git commit -m "feat(ui): add InteractiveAnalysisPanel side panel component"
```

---

### Task 9: Wire up frontend — ProjectDetail and AchievementExpandable

**Files:**
- Modify: `frontend/src/pages/CareerPortfolio/ProjectDetail.tsx`
- Modify: `frontend/src/components/portfolio/AchievementExpandable.tsx`

- [ ] **Step 1: Add interactive analysis panel to ProjectDetail**

In `frontend/src/pages/CareerPortfolio/ProjectDetail.tsx`:

Add import:
```typescript
import { InteractiveAnalysisPanel } from "@/components/portfolio/InteractiveAnalysisPanel";
```

Add state (after existing modal states):
```typescript
const [analysisAchId, setAnalysisAchId] = useState<string | null>(null);
const [analysisAchTitle, setAnalysisAchTitle] = useState("");
```

Add handler (after existing callbacks):
```typescript
const handleInteractiveAnalysis = (achId: string, title: string) => {
  setAnalysisAchId(achId);
  setAnalysisAchTitle(title);
};
```

Pass it to AchievementExpandable:
```tsx
<AchievementExpandable
  achievement={ach}
  showRemove={true}
  workExperiences={workExperiences}
  projects={projects}
  onInteractiveAnalysis={handleInteractiveAnalysis}
/>
```

Add panel at bottom of JSX (before closing `</PageContainer>`):
```tsx
{analysisAchId && (
  <InteractiveAnalysisPanel
    achievementId={analysisAchId}
    achievementTitle={analysisAchTitle}
    onClose={() => { setAnalysisAchId(null); setAnalysisAchTitle(""); }}
  />
)}
```

- [ ] **Step 2: Add interactive analysis button to AchievementExpandable**

In `frontend/src/components/portfolio/AchievementExpandable.tsx`:

Add to props interface:
```typescript
onInteractiveAnalysis?: (id: string, title: string) => void;
```

Add to destructured props:
```typescript
onInteractiveAnalysis,
```

Add button in the action bar (after the delete button, inside the `{!editing && ...}` block):
```tsx
{onInteractiveAnalysis && (
  <button
    onClick={(e) => { e.stopPropagation(); onInteractiveAnalysis(achievement.id, achievement.title); }}
    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors"
  >
    <Sparkles className="h-3 w-3" />
    互动剖析
  </button>
)}
```

Add `Sparkles` to the lucide-react import.

- [ ] **Step 3: Show polished content in AchievementExpandable**

In the expanded content section, before the existing `{editing ? ... : ...}` block, add polished content display:

```tsx
{achievement.polished_content && achievement.display_format !== "raw" && (
  <div className="rounded-md border bg-muted/30 p-3 mb-2">
    {achievement.display_format === "narrative" ? (
      <p className="text-sm leading-relaxed whitespace-pre-wrap">
        {achievement.polished_content.narrative}
      </p>
    ) : (
      <ul className="text-sm space-y-1">
        {achievement.polished_content.bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
    )}
  </div>
)}
```

Show enrichment suggestions:
```tsx
{achievement.enrichment_suggestions && achievement.enrichment_suggestions.length > 0 && (
  <div className="rounded-md border border-dashed p-2 mb-2">
    <p className="text-xs font-medium text-muted-foreground mb-1">完善建议</p>
    {achievement.enrichment_suggestions.map((s, i) => (
      <p key={i} className="text-xs text-muted-foreground">💡 {s.suggestion}</p>
    ))}
  </div>
)}
```

- [ ] **Step 4: Add display format toggle**

In the action bar, add a format switcher (only when polished_content exists):

```tsx
{achievement.polished_content && (
  <div className="flex items-center gap-0.5 ml-1 rounded-md border p-0.5">
    {(["narrative", "bullets", "raw"] as const).map((fmt) => (
      <button
        key={fmt}
        onClick={(e) => {
          e.stopPropagation();
          updateAchievement.mutate({ id: achievement.id, data: { display_format: fmt } });
        }}
        className={`rounded px-1.5 py-0.5 text-xs transition-colors ${
          achievement.display_format === fmt
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:bg-muted"
        }`}
      >
        {fmt === "narrative" ? "叙事" : fmt === "bullets" ? "要点" : "原文"}
      </button>
    ))}
  </div>
)}
```

- [ ] **Step 5: Verify TypeScript**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/CareerPortfolio/ProjectDetail.tsx frontend/src/components/portfolio/AchievementExpandable.tsx
git commit -m "feat(ui): wire up interactive analysis panel and polished content display"
```

---

### Task 10: Handle display_format in backend update

**Files:**
- Modify: `backend/src/services/achievement_service.py`

- [ ] **Step 1: Handle display_format and new fields in update_achievement**

In `update_achievement` in `backend/src/services/achievement_service.py`, the `AchievementUpdate` schema already has `display_format`. The `_to_response` already maps the new fields. But we need to make sure `update_achievement` handles `display_format` via the generic `setattr` loop, since `AchievementUpdate` uses `model_dump(exclude_unset=True)`.

Check that the existing generic update loop covers it:
```python
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(exp, field, value)
```

This already works because `display_format` is a simple `str | None` field. Verify by checking the `AchievementUpdate` schema has `display_format: str | None = None`.

If it does, no code change needed — the generic loop handles it. Mark as verified.

- [ ] **Step 2: Commit (only if changes were needed)**

Only commit if actual code changes were made.

---

## Verification

1. **Backend API test:**
   ```bash
   # Get an achievement ID
   ACH_ID=$(curl -s http://localhost:8000/api/achievements | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

   # Start interactive analysis
   curl -s -X POST http://localhost:8000/api/achievements/$ACH_ID/interactive/start | python3 -m json.tool

   # Send a message
   curl -s -X POST http://localhost:8000/api/achievements/$ACH_ID/interactive/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "这个项目是XX团队的用户认证模块重构"}' | python3 -m json.tool

   # Generate final result
   curl -s -X POST http://localhost:8000/api/achievements/$ACH_ID/interactive/generate | python3 -m json.tool
   ```

2. **Frontend test:** Open ProjectDetail page, expand an achievement, click "互动剖析", verify side panel opens with chat

3. **Display format test:** After generating, toggle 叙事/要点/原文 in AchievementExpandable

4. **Suggestions display:** Verify enrichment_suggestions show in achievement detail
