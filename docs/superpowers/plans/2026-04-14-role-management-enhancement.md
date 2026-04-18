# Role Management Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 3 role creation modes (manual / JD paste / quick name), enhance JD parsing with description expansion, allow resume name editing, and remove the standalone JDTailor page.

**Architecture:** Two new preview-only backend endpoints feed structured data to two new frontend dialogs. Creation reuses existing `POST /roles`. JD Tailor page removed, its backend kept for internal use.

**Tech Stack:** FastAPI, LangChain, React 19, TanStack Query, TypeScript

---

### Task 1: Backend — Add `skip_init` to RoleCreate schema and API

**Files:**
- Modify: `backend/src/schemas/role.py:12-14`
- Modify: `backend/src/api/roles.py:18-43`

- [ ] **Step 1: Add `skip_init` field to `RoleCreate`**

In `backend/src/schemas/role.py`, add a field after `source_jd`:

```python
class RoleCreate(BaseModel):
    """Request body for creating a new target role."""

    role_name: str = Field(..., min_length=1, max_length=200, description="Target role name")
    role_type: str = Field(..., max_length=100, description="Role category, e.g. Backend Engineer")
    description: str = Field(default="", max_length=2000, description="Role description")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    required_skills: list[str] = Field(default_factory=list, description="Required skills")
    bonus_skills: list[str] = Field(default_factory=list, description="Nice-to-have skills")
    priority: int = Field(default=0, ge=0, le=10, description="Priority rank (0=lowest)")
    source_jd: str | None = Field(
        default=None, description="Original JD text if role derived from JD"
    )
    skip_init: bool = Field(default=False, description="Skip resume/gap generation if True")
```

- [ ] **Step 2: Conditionally skip `initialize_role_assets` in `create_role` endpoint**

In `backend/src/api/roles.py`, change the `create_role` function (lines 24-43):

```python
@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new target role",
)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """Create a new target role and auto-initialize resume + gaps via agent."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    role = await role_service.create_role(db, user_id, workspace_id, body)

    # Run agent pipeline to generate capability model, resume skeleton, initial gaps
    if not body.skip_init:
        try:
            await role_service.initialize_role_assets(
                db, user_id, workspace_id, role.id, body
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Agent init failed for role {role.id}: {e}")

    return role
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/schemas/role.py backend/src/api/roles.py
git commit -m "feat(roles): add skip_init flag to skip resume generation on create"
```

---

### Task 2: Backend — Create role analysis service

**Files:**
- Create: `backend/src/services/role_analyze_service.py`

- [ ] **Step 1: Create the analysis service**

Create `backend/src/services/role_analyze_service.py`:

```python
"""Service for JD/name analysis preview — no side effects."""

from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_JD_ANALYZE_PROMPT = """\
You are an expert job description parser for software engineering roles.

Given the raw job description text, extract AND EXPAND structured information as JSON:
{
  "role_name": "Position title",
  "description": "A well-structured 200-500 character description of the role. Expand abstract requirements into concrete ones. E.g. instead of 'familiar with frontend frameworks', write 'proficient in React or Vue, including state management (Redux/Pinia), component design patterns, and performance optimization'. Instead of 'big data experience', write 'hands-on experience with Hadoop/Spark/Flink for large-scale data processing'. Be specific, concrete, and well-organized.",
  "required_skills": ["list of SPECIFIC, concrete required skills. E.g. instead of 'frontend development', list ['React', 'TypeScript', 'CSS-in-JS']. Instead of 'backend', list ['Python', 'FastAPI', 'PostgreSQL']. Each skill should be a distinct technology or tool."],
  "bonus_skills": ["list of nice-to-have skills, also specific and concrete"],
  "keywords": ["important keywords and phrases from the JD"]
}

Rules:
- required_skills and bonus_skills must be CONCRETE technologies, frameworks, or tools — not abstract categories
- description must EXPAND vague JD language into specific, concrete requirements
- Include both explicit and implicit requirements
- Return ONLY the JSON object, no other text
"""

_NAME_ANALYZE_PROMPT = """\
You are an expert career advisor who understands the software industry deeply.

Given a job title, generate a comprehensive analysis of what this role typically requires. Return JSON:
{
  "role_name": "The exact job title provided",
  "description": "A well-structured 200-500 character description of typical responsibilities, requirements, and expectations for this role. Be specific about technologies, methodologies, and skills commonly required.",
  "required_skills": ["list of 8-12 SPECIFIC, concrete skills typically required. Each should be a distinct technology, framework, or tool (e.g. 'React', 'TypeScript', 'System Design')."],
  "bonus_skills": ["list of 4-6 nice-to-have skills that make candidates stand out"],
  "keywords": ["8-12 important keywords and phrases commonly associated with this role"]
}

Rules:
- Skills must be CONCRETE technologies, frameworks, or tools — not abstract categories
- Description should reflect industry-standard expectations for this role level
- Consider the current technology landscape (2025-2026)
- Return ONLY the JSON object, no other text
"""


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
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
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
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/services/role_analyze_service.py
git commit -m "feat(roles): add role analysis service for JD and name preview"
```

---

### Task 3: Backend — Create role analysis API endpoints

**Files:**
- Create: `backend/src/api/role_analyze.py`
- Modify: `backend/src/api/router.py`

- [ ] **Step 1: Create the API file**

Create `backend/src/api/role_analyze.py`:

```python
"""Role analysis endpoints — preview only, no side effects."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.services import role_analyze_service

router = APIRouter(prefix="/roles", tags=["roles"])


class AnalyzeJDRequest(BaseModel):
    raw_jd: str = Field(..., min_length=10, description="Raw job description text")


class AnalyzeNameRequest(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=200, description="Target role name")


class RoleAnalysisResponse(BaseModel):
    role_name: str
    role_type: str
    description: str
    required_skills: list[str]
    bonus_skills: list[str]
    keywords: list[str]


@router.post(
    "/analyze-jd",
    response_model=RoleAnalysisResponse,
    summary="Analyze JD text (preview only)",
)
async def analyze_jd(body: AnalyzeJDRequest) -> RoleAnalysisResponse:
    """Parse a JD and return structured role data without creating anything."""
    result = await role_analyze_service.analyze_jd(body.raw_jd)
    return RoleAnalysisResponse(**result)


@router.post(
    "/analyze-name",
    response_model=RoleAnalysisResponse,
    summary="Analyze role name (preview only)",
)
async def analyze_name(body: AnalyzeNameRequest) -> RoleAnalysisResponse:
    """Generate typical JD data from a role name without creating anything."""
    result = await role_analyze_service.analyze_name(body.role_name)
    return RoleAnalysisResponse(**result)
```

- [ ] **Step 2: Register the router**

In `backend/src/api/router.py`, add the import and router registration. Change line 3 to add the import, and add `api_router.include_router(role_analyze.router)` BEFORE the existing roles router (so `/roles/analyze-jd` matches before `/roles/{role_id}`):

```python
"""Main API router — aggregates all sub-routers under /api."""

from fastapi import APIRouter

from src.api import achievements, dashboard, gaps, jd, profile, resumes, role_analyze, roles, stories, suggestions

api_router = APIRouter()

# Register role_analyze BEFORE roles so /roles/analyze-jd matches before /roles/{role_id}
api_router.include_router(role_analyze.router)
api_router.include_router(roles.router)
api_router.include_router(resumes.router)
api_router.include_router(achievements.router)
api_router.include_router(gaps.router)
api_router.include_router(jd.router)
api_router.include_router(suggestions.router)
api_router.include_router(profile.router)
api_router.include_router(stories.router)
api_router.include_router(dashboard.router)


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Lightweight health-check endpoint for load balancers and CI."""
    return {"status": "ok"}
```

- [ ] **Step 3: Verify backend starts**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/backend && python -c "from src.api.router import api_router; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/src/api/role_analyze.py backend/src/api/router.py
git commit -m "feat(roles): add analyze-jd and analyze-name API endpoints"
```

---

### Task 4: Frontend — Add analysis types and API hooks

**Files:**
- Modify: `frontend/src/types/index.ts:42-68`
- Modify: `frontend/src/lib/api.ts` — add to roleApi section
- Modify: `frontend/src/hooks/useRoles.ts`

- [ ] **Step 1: Add analysis types**

In `frontend/src/types/index.ts`, add after the `RoleCreateRequest` interface (after line 68):

```typescript
export interface RoleAnalysisResponse {
  role_name: string;
  role_type: string;
  description: string;
  required_skills: string[];
  bonus_skills: string[];
  keywords: string[];
}
```

Also add `skip_init?: boolean` to `RoleCreateRequest`:

```typescript
export interface RoleCreateRequest {
  role_name: string;
  role_type: string;
  description?: string;
  keywords?: string[];
  required_skills?: string[];
  bonus_skills?: string[];
  priority?: number;
  source_jd?: string;
  skip_init?: boolean;
}
```

- [ ] **Step 2: Add API methods**

In `frontend/src/lib/api.ts`, add to the `roleApi` object:

```typescript
export const roleApi = {
  list: () => apiClient.get("/roles"),
  get: (id: string) => apiClient.get(`/roles/${id}`),
  create: (data: unknown) => apiClient.post("/roles", data),
  update: (id: string, data: unknown) => apiClient.patch(`/roles/${id}`, data),
  delete: (id: string) => apiClient.delete(`/roles/${id}`),
  init: (id: string) => apiClient.post(`/roles/${id}/init`),
  analyzeJd: (raw_jd: string) => apiClient.post("/roles/analyze-jd", { raw_jd }),
  analyzeName: (role_name: string) => apiClient.post("/roles/analyze-name", { role_name }),
};
```

- [ ] **Step 3: Add analysis hooks**

In `frontend/src/hooks/useRoles.ts`, add at the bottom:

```typescript
export function useAnalyzeJd() {
  return useMutation({
    mutationFn: async (raw_jd: string) => {
      const res = await roleApi.analyzeJd(raw_jd);
      return res.data as RoleAnalysisResponse;
    },
  });
}

export function useAnalyzeName() {
  return useMutation({
    mutationFn: async (role_name: string) => {
      const res = await roleApi.analyzeName(role_name);
      return res.data as RoleAnalysisResponse;
    },
  });
}
```

Also add the import for `RoleAnalysisResponse` at the top of the file:

```typescript
import type { TargetRole, RoleCreateRequest, RoleAnalysisResponse } from "@/types";
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts frontend/src/hooks/useRoles.ts
git commit -m "feat(frontend): add role analysis types, API methods, and hooks"
```

---

### Task 5: Frontend — Create JD paste creation dialog

**Files:**
- Create: `frontend/src/components/CreateRoleFromJD.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/CreateRoleFromJD.tsx`:

```tsx
import { useState } from "react";
import { Loader2, X, FileSearch, Sparkles, CheckCircle } from "lucide-react";
import { useAnalyzeJd, useCreateRole } from "@/hooks/useRoles";
import type { RoleAnalysisResponse, RoleCreateRequest } from "@/types";

interface Props {
  onClose: () => void;
}

export function CreateRoleFromJD({ onClose }: Props) {
  const analyzeJd = useAnalyzeJd();
  const createRole = useCreateRole();

  const [rawJd, setRawJd] = useState("");
  const [preview, setPreview] = useState<RoleAnalysisResponse | null>(null);
  const [editData, setEditData] = useState<RoleAnalysisResponse | null>(null);

  const handleAnalyze = () => {
    if (!rawJd.trim()) return;
    analyzeJd.mutate(rawJd.trim(), {
      onSuccess: (data) => {
        setPreview(data);
        setEditData(data);
      },
    });
  };

  const handleCreate = (skipInit: boolean) => {
    if (!editData) return;
    const payload: RoleCreateRequest = {
      role_name: editData.role_name,
      role_type: editData.role_type || "全职",
      description: editData.description,
      required_skills: editData.required_skills,
      bonus_skills: editData.bonus_skills,
      keywords: editData.keywords,
      source_jd: rawJd,
      skip_init: skipInit,
    };
    createRole.mutate(payload, { onSuccess: onClose });
  };

  const updateField = (field: keyof RoleAnalysisResponse, value: string | string[]) => {
    if (!editData) return;
    setEditData({ ...editData, [field]: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-lg bg-card shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h3 className="text-lg font-semibold">粘贴 JD 创建岗位</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!preview ? (
            /* Step 1: Paste JD */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium">粘贴职位描述</label>
                <textarea
                  value={rawJd}
                  onChange={(e) => setRawJd(e.target.value)}
                  rows={12}
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                  placeholder="将完整的 JD 文本粘贴到这里..."
                />
                <p className="mt-1 text-xs text-muted-foreground">{rawJd.length} 字</p>
              </div>
              <button
                onClick={handleAnalyze}
                disabled={!rawJd.trim() || analyzeJd.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {analyzeJd.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    解析中...
                  </>
                ) : (
                  <>
                    <FileSearch className="h-4 w-4" />
                    解析 JD
                  </>
                )}
              </button>
              {analyzeJd.isError && (
                <p className="text-sm text-red-500">解析失败，请重试</p>
              )}
            </div>
          ) : (
            /* Step 2: Preview & Edit */
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                解析完成，可编辑后提交
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium">岗位名称</label>
                  <input
                    type="text"
                    value={editData!.role_name}
                    onChange={(e) => updateField("role_name", e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium">岗位类型</label>
                  <input
                    type="text"
                    value={editData!.role_type}
                    onChange={(e) => updateField("role_type", e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">岗位描述</label>
                <textarea
                  value={editData!.description}
                  onChange={(e) => updateField("description", e.target.value)}
                  rows={5}
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium">核心技能</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.required_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                    >
                      {skill}
                      <button
                        onClick={() => {
                          const updated = editData!.required_skills.filter((_, i) => i !== idx);
                          updateField("required_skills", updated);
                        }}
                        className="text-blue-400 hover:text-blue-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">加分技能</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.bonus_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-green-50 px-2 py-0.5 text-xs text-green-700"
                    >
                      {skill}
                      <button
                        onClick={() => {
                          const updated = editData!.bonus_skills.filter((_, i) => i !== idx);
                          updateField("bonus_skills", updated);
                        }}
                        className="text-green-400 hover:text-green-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">关键词</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      className="rounded-md bg-purple-50 px-2 py-0.5 text-xs text-purple-700"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Re-analyze */}
              <button
                onClick={() => { setPreview(null); setEditData(null); }}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                重新粘贴 JD
              </button>
            </div>
          )}
        </div>

        {/* Footer with action buttons */}
        {preview && (
          <div className="flex justify-end gap-3 border-t px-6 py-4">
            <button
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              取消
            </button>
            <button
              onClick={() => handleCreate(true)}
              disabled={createRole.isPending}
              className="rounded-md border border-primary px-4 py-2 text-sm font-medium text-primary hover:bg-primary/5 disabled:opacity-50"
            >
              仅创建岗位
            </button>
            <button
              onClick={() => handleCreate(false)}
              disabled={createRole.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createRole.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <Sparkles className="h-3.5 w-3.5" />
              创建并生成简历
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/CreateRoleFromJD.tsx
git commit -m "feat(frontend): add JD paste role creation dialog"
```

---

### Task 6: Frontend — Create quick name creation dialog

**Files:**
- Create: `frontend/src/components/CreateRoleQuick.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/CreateRoleQuick.tsx`:

```tsx
import { useState } from "react";
import { Loader2, X, Zap, Sparkles, CheckCircle } from "lucide-react";
import { useAnalyzeName, useCreateRole } from "@/hooks/useRoles";
import type { RoleAnalysisResponse, RoleCreateRequest } from "@/types";

interface Props {
  onClose: () => void;
}

export function CreateRoleQuick({ onClose }: Props) {
  const analyzeName = useAnalyzeName();
  const createRole = useCreateRole();

  const [roleName, setRoleName] = useState("");
  const [preview, setPreview] = useState<RoleAnalysisResponse | null>(null);
  const [editData, setEditData] = useState<RoleAnalysisResponse | null>(null);

  const handleAnalyze = () => {
    if (!roleName.trim()) return;
    analyzeName.mutate(roleName.trim(), {
      onSuccess: (data) => {
        setPreview(data);
        setEditData(data);
      },
    });
  };

  const handleCreate = (skipInit: boolean) => {
    if (!editData) return;
    const payload: RoleCreateRequest = {
      role_name: editData.role_name,
      role_type: editData.role_type || "全职",
      description: editData.description,
      required_skills: editData.required_skills,
      bonus_skills: editData.bonus_skills,
      keywords: editData.keywords,
      skip_init: skipInit,
    };
    createRole.mutate(payload, { onSuccess: onClose });
  };

  const updateField = (field: keyof RoleAnalysisResponse, value: string | string[]) => {
    if (!editData) return;
    setEditData({ ...editData, [field]: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-lg bg-card shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h3 className="text-lg font-semibold">快捷创建岗位</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!preview ? (
            /* Step 1: Enter role name */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium">岗位名称</label>
                <input
                  type="text"
                  value={roleName}
                  onChange={(e) => setRoleName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="例如：高级前端工程师"
                  autoFocus
                />
              </div>
              <button
                onClick={handleAnalyze}
                disabled={!roleName.trim() || analyzeName.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {analyzeName.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    分析岗位
                  </>
                )}
              </button>
              {analyzeName.isError && (
                <p className="text-sm text-red-500">分析失败，请重试</p>
              )}
            </div>
          ) : (
            /* Step 2: Preview & Edit */
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                分析完成，可编辑后提交
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium">岗位名称</label>
                  <input
                    type="text"
                    value={editData!.role_name}
                    onChange={(e) => updateField("role_name", e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium">岗位类型</label>
                  <input
                    type="text"
                    value={editData!.role_type}
                    onChange={(e) => updateField("role_type", e.target.value)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">岗位描述</label>
                <textarea
                  value={editData!.description}
                  onChange={(e) => updateField("description", e.target.value)}
                  rows={5}
                  className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium">核心技能</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.required_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                    >
                      {skill}
                      <button
                        onClick={() => {
                          const updated = editData!.required_skills.filter((_, i) => i !== idx);
                          updateField("required_skills", updated);
                        }}
                        className="text-blue-400 hover:text-blue-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">加分技能</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.bonus_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-green-50 px-2 py-0.5 text-xs text-green-700"
                    >
                      {skill}
                      <button
                        onClick={() => {
                          const updated = editData!.bonus_skills.filter((_, i) => i !== idx);
                          updateField("bonus_skills", updated);
                        }}
                        className="text-green-400 hover:text-green-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium">关键词</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {editData!.keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      className="rounded-md bg-purple-50 px-2 py-0.5 text-xs text-purple-700"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Re-analyze */}
              <button
                onClick={() => { setPreview(null); setEditData(null); }}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                重新输入岗位名称
              </button>
            </div>
          )}
        </div>

        {/* Footer with action buttons */}
        {preview && (
          <div className="flex justify-end gap-3 border-t px-6 py-4">
            <button
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              取消
            </button>
            <button
              onClick={() => handleCreate(true)}
              disabled={createRole.isPending}
              className="rounded-md border border-primary px-4 py-2 text-sm font-medium text-primary hover:bg-primary/5 disabled:opacity-50"
            >
              仅创建岗位
            </button>
            <button
              onClick={() => handleCreate(false)}
              disabled={createRole.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createRole.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <Sparkles className="h-3.5 w-3.5" />
              创建并生成简历
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/CreateRoleQuick.tsx
git commit -m "feat(frontend): add quick name role creation dialog"
```

---

### Task 7: Frontend — Update Roles.tsx to use dropdown with 3 creation modes

**Files:**
- Modify: `frontend/src/pages/Roles.tsx`

- [ ] **Step 1: Add imports and state for dropdown + new dialogs**

At the top of `Roles.tsx`, add imports for the new components and replace the button with a dropdown. Update the imports to:

```tsx
import { useState, useRef, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  useRoles,
  useCreateRole,
  useDeleteRole,
  useUpdateRole,
  usePauseRole,
  useRole,
} from "@/hooks/useRoles";
import {
  Plus,
  Trash2,
  Eye,
  Loader2,
  Briefcase,
  X,
  AlertTriangle,
  Pause,
  Play,
  Pencil,
  Save,
  ChevronDown,
  FileSearch,
  Zap,
} from "lucide-react";
import type { RoleCreateRequest } from "@/types";
import { CreateRoleFromJD } from "@/components/CreateRoleFromJD";
import { CreateRoleQuick } from "@/components/CreateRoleQuick";
```

- [ ] **Step 2: Add dropdown state and replace the button**

In the `Roles` component, add state variables after `const [editRoleId, setEditRoleId]`:

```tsx
  const [showDropdown, setShowDropdown] = useState(false);
  const [showJDModal, setShowJDModal] = useState(false);
  const [showQuickModal, setShowQuickModal] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    if (showDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showDropdown]);
```

Replace the "新增岗位" button with a dropdown:

```tsx
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增岗位
              <ChevronDown className="h-3.5 w-3.5" />
            </button>
            {showDropdown && (
              <div className="absolute right-0 top-full z-10 mt-1 w-48 rounded-md border bg-card shadow-lg">
                <button
                  onClick={() => { setShowDropdown(false); setShowCreateModal(true); }}
                  className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  手动创建
                </button>
                <button
                  onClick={() => { setShowDropdown(false); setShowJDModal(true); }}
                  className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors"
                >
                  <FileSearch className="h-4 w-4" />
                  粘贴 JD 创建
                </button>
                <button
                  onClick={() => { setShowDropdown(false); setShowQuickModal(true); }}
                  className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors"
                >
                  <Zap className="h-4 w-4" />
                  快捷创建
                </button>
              </div>
            )}
          </div>
```

- [ ] **Step 3: Add the new modal components**

Before the closing `</PageContainer>`, add the JD and Quick modals (after the existing delete confirmation dialog):

```tsx
        {/* JD Paste Modal */}
        {showJDModal && (
          <CreateRoleFromJD onClose={() => setShowJDModal(false)} />
        )}

        {/* Quick Create Modal */}
        {showQuickModal && (
          <CreateRoleQuick onClose={() => setShowQuickModal(false)} />
        )}
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Roles.tsx
git commit -m "feat(frontend): replace role create button with 3-mode dropdown"
```

---

### Task 8: Frontend — Remove JDTailor page and nav entry

**Files:**
- Delete: `frontend/src/pages/JDTailor.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Remove JDTailor route from App.tsx**

In `frontend/src/App.tsx`, remove the import and route:
- Remove line `import { JDTailor } from "@/pages/JDTailor";`
- Remove line `<Route path="/jd-tailor" element={<JDTailor />} />`

- [ ] **Step 2: Remove JD 定制 nav item from Sidebar.tsx**

In `frontend/src/components/layout/Sidebar.tsx`:
- Remove the import `FileSearch` from lucide-react imports
- Remove the nav item `{ to: "/jd-tailor", label: "JD 定制", icon: FileSearch },`

- [ ] **Step 3: Delete the JDTailor page file**

```bash
rm frontend/src/pages/JDTailor.tsx
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add -A frontend/src/pages/JDTailor.tsx frontend/src/App.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "refactor: remove standalone JDTailor page (merged into role management)"
```

---

### Task 9: Frontend — Add editable resume name in ResumeDetail

**Files:**
- Modify: `frontend/src/pages/ResumeDetail.tsx`

- [ ] **Step 1: Add editable title state**

Near the top of the `ResumeDetail` component function body, after the existing `useState` declarations, add:

```tsx
  const [editingName, setEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
```

- [ ] **Step 2: Replace the static header with editable version**

Replace line `<Header title={resume.resume_name} description="查看、编辑简历内容" />` with:

```tsx
      <Header
        title={
          editingName ? (
            <input
              type="text"
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  updateResume.mutate(
                    { id: resume.id, data: { resume_name: nameDraft } },
                    { onSuccess: () => setEditingName(false) }
                  );
                }
                if (e.key === "Escape") setEditingName(false);
              }}
              onBlur={() => {
                if (nameDraft.trim() && nameDraft !== resume.resume_name) {
                  updateResume.mutate(
                    { id: resume.id, data: { resume_name: nameDraft } },
                    { onSuccess: () => setEditingName(false) }
                  );
                } else {
                  setEditingName(false);
                }
              }}
              autoFocus
              className="rounded border bg-background px-2 py-0.5 text-2xl font-bold outline-none focus:ring-2 focus:ring-primary/50"
            />
          ) : (
            <span className="inline-flex items-center gap-2">
              {resume.resume_name}
              <button
                onClick={() => { setNameDraft(resume.resume_name); setEditingName(true); }}
                className="text-muted-foreground hover:text-foreground"
              >
                <Pencil className="h-4 w-4" />
              </button>
            </span>
          )
        }
        description="查看、编辑简历内容"
      />
```

Also update the breadcrumb to show the current name:

Replace `<span className="text-foreground font-medium">{resume.resume_name}</span>` with:

```tsx
          <span className="text-foreground font-medium">{editingName ? nameDraft : resume.resume_name}</span>
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ResumeDetail.tsx
git commit -m "feat(resume): add editable resume name in detail page header"
```

---

### Task 10: Frontend — Enhance match score display in RoleDetail

**Files:**
- Modify: `frontend/src/pages/RoleDetail.tsx`

- [ ] **Step 1: Find and enhance the resume card match score display**

In `frontend/src/pages/RoleDetail.tsx`, find the resume card section that displays `match_score` and `completeness_score`. Enhance it to show colored progress bars instead of plain numbers.

Look for the section showing match_score and completeness_score numbers and replace with:

```tsx
              {/* Match Score */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">匹配度</span>
                  <span className={`font-bold ${(resume.match_score ?? 0) >= 70 ? "text-green-600" : (resume.match_score ?? 0) >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                    {(resume.match_score ?? 0).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full transition-all ${(resume.match_score ?? 0) >= 70 ? "bg-green-500" : (resume.match_score ?? 0) >= 40 ? "bg-yellow-500" : "bg-red-500"}`}
                    style={{ width: `${Math.min(resume.match_score ?? 0, 100)}%` }}
                  />
                </div>
              </div>

              {/* Completeness */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">完整度</span>
                  <span className={`font-bold ${(resume.completeness_score ?? 0) >= 70 ? "text-green-600" : (resume.completeness_score ?? 0) >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                    {(resume.completeness_score ?? 0).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full transition-all ${(resume.completeness_score ?? 0) >= 70 ? "bg-green-500" : (resume.completeness_score ?? 0) >= 40 ? "bg-yellow-500" : "bg-red-500"}`}
                    style={{ width: `${Math.min(resume.completeness_score ?? 0, 100)}%` }}
                  />
                </div>
              </div>
```

Note: The exact location depends on the current RoleDetail.tsx structure. Search for where `match_score` and `completeness_score` are currently displayed as plain numbers and replace that section.

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/RoleDetail.tsx
git commit -m "feat(roles): enhance match score display with colored progress bars"
```

---

### Task 11: Verify full stack and test manually

- [ ] **Step 1: Verify backend starts and endpoints are registered**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/backend && python -c "from src.api.router import api_router; routes = [r.path for r in api_router.routes]; assert '/roles/analyze-jd' in routes; assert '/roles/analyze-name' in routes; print('Routes OK')"`
Expected: `Routes OK`

- [ ] **Step 2: Verify frontend builds**

Run: `cd /Users/gaoqiangsheng/work/playground/CareerAgent/frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Final commit if any fixups needed**
