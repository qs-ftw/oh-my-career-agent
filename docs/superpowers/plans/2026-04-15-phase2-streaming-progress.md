# Phase 2: 流式进度（SSE + 打字机效果）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the silent-wait analysis flow with an SSE-powered modal that shows real-time pipeline progress with LLM token streaming.

**Architecture:** Backend adds a new SSE endpoint that wraps the LangGraph pipeline's `astream_events` API, emitting structured events (node_start, token, node_complete, pipeline_complete). Frontend adds a `usePipelineStream` hook using `fetch` + `ReadableStream` and a `PipelineProgressModal` component with typewriter effect.

**Tech Stack:** sse-starlette, LangGraph astream_events v2, fetch ReadableStream, React state

---

### Task 1: Add sse-starlette dependency

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add dependency**

Add `sse-starlette>=2.0.0` to the dependencies list in `pyproject.toml`.

- [ ] **Step 2: Install**

Run: `cd backend && pip install sse-starlette`

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add sse-starlette dependency"
```

---

### Task 2: Create Pipeline Stream Service

**Files:**
- Create: `backend/src/services/pipeline_stream_service.py`

This service wraps a LangGraph graph's `astream_events` into SSE events.

```python
"""Pipeline streaming service — wraps LangGraph astream_events into SSE events."""

from __future__ import annotations

import json
import time
import logging
from collections.abc import AsyncGenerator

from langgraph.pregel import Pregel

logger = logging.getLogger(__name__)

# Map internal node names to user-friendly Chinese labels
_NODE_LABELS: dict[str, str] = {
    "achievement_analysis": "正在解析成果...",
    "role_matching": "正在匹配目标岗位...",
    "resume_update": "正在生成简历更新建议...",
    "gap_evaluation": "正在评估技能差距...",
    "explain": "正在生成分析总结...",
    "jd_parsing": "正在解析职位描述...",
    "jd_review": "正在深度分析JD...",
    "jd_tailoring": "正在定制简历...",
    "capability_modeling": "正在构建能力模型...",
    "resume_init": "正在生成初始简历...",
}

# Events we care about from astream_events v2
_CHAIN_START = "on_chain_start"
_CHAIN_END = "on_chain_end"
_LLM_STREAM = "on_llm_new_token"


async def stream_pipeline(
    graph: Pregel,
    input_data: dict,
    *,
    node_labels: dict[str, str] | None = None,
) -> AsyncGenerator[str, None]:
    """Run a LangGraph pipeline and yield SSE-formatted events.

    Yields strings in SSE format:
        event: <type>\ndata: <json>\n\n
    """
    labels = {**_NODE_LABELS, **(node_labels or {})}
    node_start_times: dict[str, float] = {}
    current_node: str | None = None

    try:
        async for event in graph.astream_events(
            input_data,
            version="v2",
            include_names=[
                "achievement_analysis", "role_matching", "resume_update",
                "gap_evaluation", "explain", "jd_parsing", "jd_review",
                "jd_tailoring", "capability_modeling", "resume_init",
            ],
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


def _sse(event_type: str, data: dict) -> str:
    """Format an SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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
    return "完成"
```

- [ ] **Step 1: Create the file with the code above**
- [ ] **Step 2: Commit**

```bash
git add backend/src/services/pipeline_stream_service.py
git commit -m "feat(services): add pipeline stream service for SSE event generation"
```

---

### Task 3: Create SSE API endpoint for achievement analysis

**Files:**
- Create: `backend/src/api/pipeline_stream.py`

```python
"""SSE streaming endpoints for long-running AI pipelines."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.models.achievement import Achievement
from src.models.profile import CareerProfile
from src.models.target_role import RoleCapabilityModel, TargetRole
from src.agent.graph import achievement_graph
from src.services.pipeline_stream_service import stream_pipeline

router = APIRouter(tags=["streaming"])


@router.get(
    "/achievements/{achievement_id}/stream-analysis",
    summary="Stream achievement analysis via SSE",
)
async def stream_achievement_analysis(
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """SSE endpoint that streams the achievement analysis pipeline.

    Event types: node_start, token, node_complete, pipeline_complete, pipeline_error
    """
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()

    async def event_generator():
        # Load achievement
        stmt = (
            select(Achievement)
            .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
            .where(Achievement.id == achievement_id, CareerProfile.user_id == user_id)
        )
        result = await db.execute(stmt)
        achievement = result.scalar_one_or_none()

        if achievement is None:
            yield f"event: pipeline_error\ndata: {json.dumps({'error': 'Achievement not found'})}\n\n"
            return

        # Load target roles
        from src.services.achievement_service import _build_target_roles_data
        target_roles_data = await _build_target_roles_data(db, user_id)

        agent_input = {
            "user_id": str(user_id),
            "workspace_id": str(workspace_id),
            "achievement_id": str(achievement_id),
            "achievement_raw": achievement.raw_content or "",
            "target_roles": target_roles_data,
            "achievement_parsed": None,
            "role_matches": [],
            "suggestions": [],
            "gap_updates": [],
            "agent_logs": [],
        }

        async for sse_event in stream_pipeline(achievement_graph, agent_input):
            yield sse_event

    import json
    return EventSourceResponse(event_generator())
```

**Important**: The `_build_target_roles_data` helper needs to be extracted from `run_achievement_pipeline` in `achievement_service.py`. In `achievement_service.py`, extract the "Load active target roles" block (lines ~135-222) into a standalone async function `_build_target_roles_data(session, user_id)` that returns `list[dict]`.

- [ ] **Step 1: Extract `_build_target_roles_data` from achievement_service.py**
- [ ] **Step 2: Create the SSE endpoint file**
- [ ] **Step 3: Register the new router in `backend/src/api/router.py`**
- [ ] **Step 4: Commit**

```bash
git add backend/src/api/pipeline_stream.py backend/src/api/router.py backend/src/services/achievement_service.py
git commit -m "feat(api): add SSE streaming endpoint for achievement analysis"
```

---

### Task 4: Frontend — usePipelineStream hook

**Files:**
- Create: `frontend/src/hooks/usePipelineStream.ts`

```typescript
import { useState, useCallback, useRef } from "react";

export interface PipelineStep {
  node: string;
  label: string;
  status: "pending" | "running" | "completed";
  tokens: string;
  duration_ms?: number;
  summary?: string;
}

export function usePipelineStream() {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const start = useCallback(async (url: string) => {
    setError(null);
    setSteps([]);
    setIsStreaming(true);
    abortRef.current = new AbortController();

    try {
      const response = await fetch(url, { signal: abortRef.current.signal });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep the last incomplete line in buffer
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));
            handleEvent(eventType, data, setSteps);
            eventType = "";
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message);
      }
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { steps, isStreaming, error, start, cancel };
}

function handleEvent(
  type: string,
  data: Record<string, unknown>,
  setSteps: React.Dispatch<React.SetStateAction<PipelineStep[]>>,
) {
  if (type === "node_start") {
    setSteps((prev) => [
      ...prev,
      {
        node: data.node as string,
        label: data.label as string,
        status: "running",
        tokens: "",
      },
    ]);
  } else if (type === "token") {
    setSteps((prev) =>
      prev.map((s) =>
        s.node === data.node && s.status === "running"
          ? { ...s, tokens: s.tokens + (data.text as string) }
          : s
      )
    );
  } else if (type === "node_complete") {
    setSteps((prev) =>
      prev.map((s) =>
        s.node === data.node
          ? {
              ...s,
              status: "completed",
              duration_ms: data.duration_ms as number,
              summary: data.summary as string,
            }
          : s
      )
    );
  }
}
```

- [ ] **Step 1: Create the file**
- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/usePipelineStream.ts
git commit -m "feat(frontend): add usePipelineStream hook for SSE consumption"
```

---

### Task 5: Frontend — PipelineProgressModal component

**Files:**
- Create: `frontend/src/components/PipelineProgressModal.tsx`

A modal/dialog that:
- Shows each pipeline step as a row with icon (✅/🔄/⏳) + label + duration
- Current step shows LLM tokens with typewriter effect in a scrollable area
- Completed steps show summary (collapsed)
- Cancel button to abort the stream
- Auto-closes on pipeline_complete (after 1s delay)

```tsx
import { useEffect, useRef } from "react";
import type { PipelineStep } from "@/hooks/usePipelineStream";
import { Loader2, CheckCircle, Clock, X } from "lucide-react";

interface Props {
  steps: PipelineStep[];
  isStreaming: boolean;
  error: string | null;
  onCancel: () => void;
}

export function PipelineProgressModal({ steps, isStreaming, error, onCancel }: Props) {
  const tokenEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    tokenEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps]);

  if (steps.length === 0 && !isStreaming) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border bg-card p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">AI 分析中</h3>
          <button onClick={onCancel} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3">
          {steps.map((step) => (
            <div key={step.node} className="rounded-md border p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {step.status === "completed" ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : step.status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="text-sm font-medium">{step.label}</span>
                </div>
                {step.status === "completed" && step.duration_ms != null && (
                  <span className="text-xs text-muted-foreground">
                    {(step.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>

              {step.status === "running" && step.tokens && (
                <div className="mt-2 max-h-32 overflow-y-auto rounded bg-muted/50 p-2">
                  <p className="whitespace-pre-wrap text-xs text-muted-foreground">
                    {step.tokens}
                  </p>
                  <div ref={tokenEndRef} />
                </div>
              )}

              {step.status === "completed" && step.summary && (
                <p className="mt-1 text-xs text-muted-foreground">{step.summary}</p>
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            onClick={onCancel}
            className="rounded-md border px-4 py-1.5 text-sm hover:bg-accent"
          >
            {isStreaming ? "取消分析" : "关闭"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 1: Create the file**
- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PipelineProgressModal.tsx
git commit -m "feat(frontend): add PipelineProgressModal component"
```

---

### Task 6: Wire up Achievements page to use streaming modal

**Files:**
- Modify: `frontend/src/pages/Achievements.tsx`

Update the "分析" button to:
1. Import `usePipelineStream` and `PipelineProgressModal`
2. On click, call `start('/api/achievements/${id}/stream-analysis')` instead of the mutation
3. After streaming completes, invalidate the achievement queries to refresh data
4. Show the modal during streaming

Key changes:
- Replace `useAnalyzeAchievement` mutation with `usePipelineStream` hook
- Add `<PipelineProgressModal>` to the page render
- The old `handleAnalyze` callback changes to use `stream.start(url)`

- [ ] **Step 1: Update Achievements.tsx**
- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Achievements.tsx
git commit -m "feat(frontend): wire achievement analysis to SSE streaming modal"
```

---

## Verification

1. **Backend SSE**: `curl -N http://localhost:8000/api/achievements/{id}/stream-analysis` — should see SSE events
2. **Frontend modal**: Click analyze on an achievement — modal appears with progress
3. **Typewriter effect**: LLM tokens stream in real-time in the modal
4. **Cancel**: Click cancel — stream stops, modal closes
5. **Completion**: Pipeline finishes — modal shows all steps completed, data refreshes
