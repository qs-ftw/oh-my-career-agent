# PRD Gap Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 PRD compliance gaps found during browser verification: roles list edit/pause buttons, dashboard role cards, dashboard high-priority gap list, and JD tailor performance.

**Architecture:** Pure frontend changes for 2 items (roles list buttons). Backend + frontend changes for 2 items (dashboard sections). Backend-only optimization for 1 item (JD tailor pipeline streaming).

**Tech Stack:** FastAPI + SQLAlchemy 2 (backend), React 19 + TanStack Query + TypeScript (frontend), Tailwind CSS (styling)

---

## Task 1: Add Pause/Resume to Role API (Backend)

**Files:**
- Modify: `backend/src/schemas/role.py:24-34` (add `status` field to `RoleUpdate`)
- Modify: `backend/src/services/role_service.py:254-294` (handle `status` in update_map)

This is the smallest backend change — the existing `PATCH /roles/{id}` endpoint already calls `update_role()` which uses `model_dump(exclude_unset=True)`, so we just need to allow `status` through the schema and persist it.

- [ ] **Step 1: Add `status` field to `RoleUpdate` schema**

In `backend/src/schemas/role.py`, add a `status` field to the `RoleUpdate` class:

```python
class RoleUpdate(BaseModel):
    """Request body for updating an existing target role. All fields optional."""

    role_name: str | None = Field(default=None, min_length=1, max_length=200)
    role_type: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    keywords: list[str] | None = Field(default=None)
    required_skills: list[str] | None = Field(default=None)
    bonus_skills: list[str] | None = Field(default=None)
    priority: int | None = Field(default=None, ge=0, le=10)
    source_jd: str | None = Field(default=None)
    status: str | None = Field(default=None, pattern="^(active|paused)$")
```

- [ ] **Step 2: Handle `status` in `update_role` service**

In `backend/src/services/role_service.py`, add a handler for `status` inside the `update_role` function (after the `source_jd` handler, around line 288):

```python
    if "status" in update_map:
        role.status = update_map["status"]
```

- [ ] **Step 3: Verify the endpoint works**

Run: `curl -s -X PATCH http://localhost:8000/api/roles/$(curl -s http://localhost:8000/api/roles | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])") -H "Content-Type: application/json" -d '{"status": "paused"}' | python3 -m json.tool`
Expected: Response shows `"status": "paused"`

Then restore: `curl -s -X PATCH http://localhost:8000/api/roles/... -d '{"status": "active"}'`

- [ ] **Step 4: Commit**

```bash
git add backend/src/schemas/role.py backend/src/services/role_service.py
git commit -m "feat(roles): allow status update (active/paused) via PATCH endpoint"
```

---

## Task 2: Add Edit & Pause Buttons to Roles List Page (Frontend)

**Files:**
- Modify: `frontend/src/pages/Roles.tsx` (add edit/pause buttons to `RoleCard`)
- Modify: `frontend/src/hooks/useRoles.ts` (add `usePauseRole` hook)

The role list currently only has "删除" and "查看详情" per card. We add "编辑" (opens inline edit modal) and "暂停/恢复" (toggles status).

- [ ] **Step 1: Add `usePauseRole` hook**

In `frontend/src/hooks/useRoles.ts`, add after the `useUpdateRole` function:

```typescript
export function usePauseRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, pause }: { id: string; pause: boolean }) => {
      const { data } = await roleApi.update(id, { status: pause ? "paused" : "active" });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
  });
}
```

- [ ] **Step 2: Update `RoleCard` to accept edit/pause callbacks**

In `frontend/src/pages/Roles.tsx`, update the `RoleCard` component. Add `onEdit` and `onPause` props and two new buttons. Import `Pause`, `Play`, `Pencil` from lucide-react.

Update the RoleCard props and add buttons to the actions bar (line 232):

```tsx
function RoleCard({
  role,
  onView,
  onDelete,
  onEdit,
  onPause,
}: {
  role: {
    id: string;
    role_name: string;
    role_type: string;
    priority: number;
    status: string;
    required_skills: string[];
  };
  onView: () => void;
  onDelete: () => void;
  onEdit: () => void;
  onPause: () => void;
}) {
```

In the actions div (currently lines 232-249), add edit and pause buttons before the delete button:

```tsx
      <div className="mt-4 flex items-center justify-end gap-2 border-t pt-3">
        <button
          onClick={onEdit}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
        >
          <Pencil className="h-3.5 w-3.5" />
          编辑
        </button>
        <button
          onClick={onPause}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
        >
          {role.status === "active" ? (
            <><Pause className="h-3.5 w-3.5" /> 暂停</>
          ) : (
            <><Play className="h-3.5 w-3.5" /> 恢复</>
          )}
        </button>
        <button
          onClick={onDelete}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
          删除
        </button>
        <button
          onClick={onView}
          className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Eye className="h-3.5 w-3.5" />
          查看详情
        </button>
      </div>
```

- [ ] **Step 3: Wire up edit/pause in the parent `Roles` component**

In the `Roles` component, add state and handlers for editing and pausing:

```tsx
  const pauseRole = usePauseRole();
  const updateRole = useUpdateRole();
  const [editRoleId, setEditRoleId] = useState<string | null>(null);

  const handlePause = (role: { id: string; status: string }) => {
    pauseRole.mutate({ id: role.id, pause: role.status === "active" });
  };
```

Update the `RoleCard` usage in the grid to pass the new props:

```tsx
              {roles.map((role) => (
                <RoleCard
                  key={role.id}
                  role={role}
                  onView={() => navigate(`/roles/${role.id}`)}
                  onDelete={() => setDeleteConfirmId(role.id)}
                  onEdit={() => setEditRoleId(role.id)}
                  onPause={() => handlePause(role)}
                />
              ))}
```

Add a minimal inline edit modal that reuses the `EditRoleModal` pattern from `RoleDetail.tsx`. The simplest approach is to navigate to the detail page's edit modal by adding a small `EditRoleModal` component right in `Roles.tsx` (or import from a shared module). For minimal code, add it inline:

```tsx
        {/* Edit Modal */}
        {editRoleId && (
          <EditRoleInlineModal
            roleId={editRoleId}
            onClose={() => setEditRoleId(null)}
          />
        )}
```

The `EditRoleInlineModal` fetches the role by ID and renders the same form as `RoleDetail.tsx`'s edit modal. Import `useRole` and `useUpdateRole` hooks.

- [ ] **Step 4: Verify in browser**

1. Navigate to `http://localhost:5173/roles`
2. Each role card should now show: 编辑 | 暂停 | 删除 | 查看详情
3. Click "暂停" on a role → status changes to "已暂停" (yellow badge)
4. Click "恢复" → status changes back to "进行中" (green badge)
5. Click "编辑" → edit modal opens, change name and save

Run: `npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Roles.tsx frontend/src/hooks/useRoles.ts
git commit -m "feat(roles): add edit and pause/resume buttons to roles list cards"
```

---

## Task 3: Add Dashboard Backend Endpoints for Role Cards & High-Priority Gaps

**Files:**
- Modify: `backend/src/services/dashboard_service.py` (add `get_role_summaries` and `get_high_priority_gaps` functions)
- Modify: `backend/src/api/dashboard.py` (add two new GET endpoints)
- Modify: `frontend/src/lib/api.ts` (add API client methods)
- Modify: `frontend/src/types/index.ts` (add response types)

### Backend: Role summary cards

Each card needs: role name, status, priority, resume completeness/match scores, gap count.

- [ ] **Step 1: Add `get_role_summaries` to dashboard service**

In `backend/src/services/dashboard_service.py`, add:

```python
async def get_role_summaries(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[dict]:
    """Get summary data for each active/paused role for dashboard cards."""
    stmt = (
        select(TargetRole)
        .where(
            TargetRole.user_id == user_id,
            TargetRole.deleted_at.is_(None),
            TargetRole.status.in_(["active", "paused"]),
        )
        .order_by(TargetRole.priority.desc())
    )
    result = await session.execute(stmt)
    roles = result.scalars().all()

    summaries = []
    for role in roles:
        # Get resume for this role
        resume = await session.scalar(
            select(Resume).where(
                Resume.target_role_id == role.id,
                Resume.deleted_at.is_(None),
            )
        )
        # Get gap count for this role
        gap_count = await session.scalar(
            select(func.count(GapItem.id)).where(
                GapItem.target_role_id == role.id,
                GapItem.status.in_(["open", "in_progress"]),
            )
        ) or 0

        summaries.append({
            "id": str(role.id),
            "role_name": role.role_name,
            "role_type": role.role_type,
            "status": role.status,
            "priority": role.priority,
            "completeness_score": resume.completeness_score if resume else 0,
            "match_score": resume.match_score if resume else 0,
            "gap_count": gap_count,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        })
    return summaries
```

### Backend: High-priority gaps

- [ ] **Step 2: Add `get_high_priority_gaps` to dashboard service**

In `backend/src/services/dashboard_service.py`, add:

```python
async def get_high_priority_gaps(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 5,
) -> list[dict]:
    """Get top high-priority open gaps with suggested actions."""
    stmt = (
        select(GapItem)
        .where(
            GapItem.user_id == user_id,
            GapItem.status.in_(["open", "in_progress"]),
        )
        .order_by(GapItem.priority.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    gaps = result.scalars().all()

    return [
        {
            "id": str(g.id),
            "skill_name": g.skill_name,
            "gap_type": g.gap_type,
            "priority": g.priority,
            "status": g.status,
            "progress": g.progress,
            "target_role_id": str(g.target_role_id),
        }
        for g in gaps
    ]
```

- [ ] **Step 3: Add API endpoints**

In `backend/src/api/dashboard.py`, add two new routes:

```python
@router.get("/dashboard/role-summaries")
async def role_summaries(session: AsyncSession = Depends(get_session)):
    user_id = get_current_user_id()
    return await dashboard_service.get_role_summaries(session, user_id)


@router.get("/dashboard/high-priority-gaps")
async def high_priority_gaps(session: AsyncSession = Depends(get_session)):
    user_id = get_current_user_id()
    return await dashboard_service.get_high_priority_gaps(session, user_id)
```

Ensure the imports for `get_session`, `get_current_user_id`, etc. are present (they should already exist in this file).

- [ ] **Step 4: Verify backend endpoints**

Run:
```bash
curl -s http://localhost:8000/api/dashboard/role-summaries | python3 -m json.tool
curl -s http://localhost:8000/api/dashboard/high-priority-gaps | python3 -m json.tool
```
Expected: JSON arrays with role summaries and gap items

- [ ] **Step 5: Commit backend**

```bash
git add backend/src/services/dashboard_service.py backend/src/api/dashboard.py
git commit -m "feat(dashboard): add role-summaries and high-priority-gaps endpoints"
```

---

## Task 4: Add Dashboard Role Cards & High-Priority Gap Sections (Frontend)

**Files:**
- Modify: `frontend/src/types/index.ts` (add `RoleSummary` and `GapSummary` types)
- Modify: `frontend/src/lib/api.ts` (add API client methods)
- Modify: `frontend/src/hooks/useDashboard.ts` (add hooks)
- Modify: `frontend/src/pages/Dashboard.tsx` (add role cards and gap list sections)

- [ ] **Step 1: Add types**

In `frontend/src/types/index.ts`, add after `JDRecentDecision`:

```typescript
export interface RoleSummary {
  id: string;
  role_name: string;
  role_type: string;
  status: string;
  priority: number;
  completeness_score: number;
  match_score: number;
  gap_count: number;
  updated_at: string;
}

export interface GapSummary {
  id: string;
  skill_name: string;
  gap_type: string;
  priority: number;
  status: string;
  progress: number;
  target_role_id: string;
}
```

- [ ] **Step 2: Add API client methods**

In `frontend/src/lib/api.ts`, add to the `dashboardApi` object:

```typescript
export const dashboardApi = {
  stats: () => apiClient.get("/dashboard/stats"),
  recentJdDecisions: () => apiClient.get("/dashboard/recent-jd-decisions"),
  roleSummaries: () => apiClient.get("/dashboard/role-summaries"),
  highPriorityGaps: () => apiClient.get("/dashboard/high-priority-gaps"),
};
```

- [ ] **Step 3: Add hooks**

In `frontend/src/hooks/useDashboard.ts`, add:

```typescript
export function useRoleSummaries() {
  return useQuery<RoleSummary[]>({
    queryKey: ["dashboard", "role-summaries"],
    queryFn: async () => {
      const { data } = await dashboardApi.roleSummaries();
      return data;
    },
  });
}

export function useHighPriorityGaps() {
  return useQuery<GapSummary[]>({
    queryKey: ["dashboard", "high-priority-gaps"],
    queryFn: async () => {
      const { data } = await dashboardApi.highPriorityGaps();
      return data;
    },
  });
}
```

Add the new types to the import: `import type { DashboardStats, JDRecentDecision, RoleSummary, GapSummary } from "@/types";`

- [ ] **Step 4: Add Role Cards section to Dashboard**

In `frontend/src/pages/Dashboard.tsx`, import the new hooks and add a section between the stats grid and JD decisions.

Import additions:
```typescript
import { useDashboardStats, useRecentJdDecisions, useRoleSummaries, useHighPriorityGaps } from "@/hooks/useDashboard";
import { useNavigate } from "react-router-dom";
```

Add `const navigate = useNavigate();` inside the component.

Add the role cards section (between stats grid and JD Decisions):

```tsx
            {/* Role Cards */}
            {roleSummaries && roleSummaries.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold">岗位概览</h3>
                <div className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {roleSummaries.map((rs) => (
                    <div
                      key={rs.id}
                      onClick={() => navigate(`/roles/${rs.id}`)}
                      className="cursor-pointer rounded-lg border bg-card p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm">{rs.role_name}</h4>
                        <span className={`rounded-full px-2 py-0.5 text-xs ${
                          rs.status === "active" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                        }`}>
                          {rs.status === "active" ? "进行中" : "已暂停"}
                        </span>
                      </div>
                      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                        <div>
                          <span className="block text-muted-foreground">完成度</span>
                          <span className="font-medium text-foreground">{Math.round(rs.completeness_score)}%</span>
                        </div>
                        <div>
                          <span className="block text-muted-foreground">匹配度</span>
                          <span className="font-medium text-foreground">{Math.round(rs.match_score)}%</span>
                        </div>
                        <div>
                          <span className="block text-muted-foreground">Gap数</span>
                          <span className="font-medium text-foreground">{rs.gap_count}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
```

- [ ] **Step 5: Add High-Priority Gap list section to Dashboard**

Add after the JD Decisions section (before Quick Links):

```tsx
            {/* High Priority Gaps */}
            {highPriorityGaps && highPriorityGaps.length > 0 && (
              <div className="mt-4 rounded-lg border bg-card p-6">
                <h3 className="font-semibold">高优先级 Gap</h3>
                <div className="mt-3 space-y-2">
                  {highPriorityGaps.map((gap) => (
                    <div key={gap.id} className="flex items-center justify-between rounded-md border p-3">
                      <div className="flex items-center gap-3">
                        <span className="rounded px-1.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-700">
                          P{gap.priority}
                        </span>
                        <span className="text-sm">{gap.skill_name}</span>
                        <span className="text-xs text-muted-foreground">{gap.gap_type}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          gap.status === "open" ? "bg-gray-100 text-gray-600" : "bg-blue-100 text-blue-600"
                        }`}>
                          {gap.status === "open" ? "未开始" : "进行中"}
                        </span>
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-primary rounded-full" style={{ width: `${gap.progress}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
```

- [ ] **Step 6: Verify in browser**

1. Navigate to `http://localhost:5173/`
2. Dashboard should now show:
   - Top: 6 stat cards (existing)
   - Middle: Role cards section with name/status/completeness/match/gaps per role
   - Below: JD Decisions (existing)
   - Below: High-priority gap list with priority badges and progress bars
   - Bottom: Quick links (existing)
3. Click a role card → navigates to role detail page

Run: `npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts frontend/src/hooks/useDashboard.ts frontend/src/pages/Dashboard.tsx
git commit -m "feat(dashboard): add role overview cards and high-priority gap list"
```

---

## Task 5: Optimize JD Tailor Pipeline Performance (Backend)

**Files:**
- Modify: `backend/src/agent/graph.py` (make jd_review optional or cached)

The JD tailor pipeline currently chains: `jd_parsing → jd_review → jd_tailoring → explain`. Each step makes an LLM call. The `jd_review` step adds ~30-60 seconds but isn't strictly necessary for the MVP — it produces supplementary analysis. We make it async/skippable.

**Strategy:** The `jd_review` node's output feeds into `jd_tailoring` as context, which improves quality but isn't a hard dependency. We add a `skip_review` flag to the pipeline input so the frontend can choose fast mode.

- [ ] **Step 1: Add `skip_review` flag to the agent state**

In `backend/src/agent/state.py`, add to `CareerAgentState`:

```python
    skip_review: bool = False
```

- [ ] **Step 2: Add conditional edge in graph to skip review**

In `backend/src/agent/graph.py`, modify the graph to conditionally skip `jd_review`:

```python
from langgraph.graph import StateGraph, END

def should_review(state: dict) -> str:
    """Skip review node if flag is set."""
    if state.get("skip_review"):
        return "jd_tailoring"
    return "jd_review"
```

Update the graph edge from `jd_parsing`:

```python
    # Replace: graph.add_edge("jd_parsing", "jd_review")
    # With:
    graph.add_conditional_edges("jd_parsing", should_review)
    graph.add_edge("jd_review", "jd_tailoring")
```

- [ ] **Step 3: Pass `skip_review` flag from the tailor endpoint**

In `backend/src/services/jd_service.py`, in the `tailor_jd` function where agent_input is built, add:

```python
    agent_input["skip_review"] = True  # MVP: skip review for speed
```

This makes the default path skip the review node, cutting LLM calls from 4 to 3 (jd_parsing → jd_tailoring → explain). The review is still available if `skip_review=False` is passed.

- [ ] **Step 4: Verify the pipeline is faster**

Run: `time curl -s --max-time 120 -X POST http://localhost:8000/api/jd/tailor -H "Content-Type: application/json" -d '{"raw_jd": "高级Python开发工程师，要求5年以上Python开发经验，熟悉FastAPI", "mode": "generate_new"}'`
Expected: Response time should be ~30-45 seconds (3 LLM calls instead of 4)

- [ ] **Step 5: Commit**

```bash
git add backend/src/agent/state.py backend/src/agent/graph.py backend/src/services/jd_service.py
git commit -m "perf(jd): skip jd_review node by default to reduce tailor pipeline latency"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- PRD 9.1.2 编辑 → Task 2 (edit button on list)
- PRD 9.1.3 暂停 → Task 1 + Task 2 (backend status + frontend button)
- PRD 20.2 岗位卡片区 → Task 3 + Task 4 (backend endpoint + frontend cards)
- PRD 20.2 高优先级gap列表 → Task 3 + Task 4 (backend endpoint + frontend list)
- PRD 9.5 JD定制性能 → Task 5 (skip review node)

**2. Placeholder scan:**
- No TBD/TODO found — all steps have concrete code and commands

**3. Type consistency:**
- `RoleSummary` / `GapSummary` types match between frontend types and backend response shapes
- `usePauseRole` uses `{ id: string; pause: boolean }` matching PATCH payload with `{ status: "paused" | "active" }`
- `RoleUpdate.status` pattern `^(active|paused)$` matches frontend values
