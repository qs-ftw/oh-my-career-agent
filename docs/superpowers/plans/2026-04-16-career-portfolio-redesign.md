# CareerPortfolio 3-Level Drill-Down Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat single-page CareerPortfolio with a 3-level drill-down navigation (overview → company detail → project detail), with full CRUD at every level and orphaned achievement assignment.

**Architecture:** URL-driven routing with breadcrumb navigation. `CareerPortfolio.tsx` becomes a layout wrapper with `<Outlet />`. Three sub-pages live under `pages/CareerPortfolio/`. Backend adds `PATCH /achievements/:id` for assignment and inline editing. Frontend adds `useUpdateAchievement` hook.

**Tech Stack:** React Router v6 (already installed), TanStack React Query, existing REST API, Tailwind CSS

---

## File Structure

### New files:
| File | Purpose |
|------|---------|
| `frontend/src/pages/CareerPortfolio/Overview.tsx` | Total overview — company cards, standalone projects, orphaned achievements |
| `frontend/src/pages/CareerPortfolio/CompanyDetail.tsx` | Company info + project list + WE-level achievements |
| `frontend/src/pages/CareerPortfolio/ProjectDetail.tsx` | Project info + expandable achievement list |
| `frontend/src/components/portfolio/AchievementExpandable.tsx` | Inline expandable achievement row (used in ProjectDetail) |
| `frontend/src/components/portfolio/AchievementAssignSelector.tsx` | Dropdown to assign achievement to a project (used in Overview & CompanyDetail) |
| `frontend/src/components/portfolio/WorkExperienceModal.tsx` | Create/edit WE modal (extracted from current CareerPortfolio.tsx) |
| `frontend/src/components/portfolio/ProjectModal.tsx` | Create/edit project modal (extracted from current CareerPortfolio.tsx) |
| `backend/src/schemas/achievement.py` | Add `AchievementUpdate` schema (file already exists) |

### Modified files:
| File | Change |
|------|--------|
| `backend/src/services/achievement_service.py` | Add `update_achievement()` |
| `backend/src/api/achievements.py` | Add `PATCH /{achievement_id}` endpoint |
| `frontend/src/lib/api.ts` | Add `achievementApi.update()` |
| `frontend/src/hooks/useAchievements.ts` | Add `useUpdateAchievement` hook |
| `frontend/src/pages/CareerPortfolio.tsx` | Rewrite as layout wrapper with `<Outlet />` |
| `frontend/src/App.tsx` | Update route to use nested routes |

---

### Task 1: Backend — Add AchievementUpdate schema

**Files:**
- Modify: `backend/src/schemas/achievement.py`

- [ ] **Step 1: Add `AchievementUpdate` class**

Append to `backend/src/schemas/achievement.py` after the existing `AchievementAnalysisRequest` class:

```python
class AchievementUpdate(BaseModel):
    """Request body for updating an achievement. All fields optional."""
    title: str | None = None
    raw_content: str | None = None
    project_id: UUID | None = None
    work_experience_id: UUID | None = None
    tags: list[str] | None = None
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/schemas/achievement.py
git commit -m "feat(schema): add AchievementUpdate schema for PATCH endpoint"
```

---

### Task 2: Backend — Add update_achievement service function

**Files:**
- Modify: `backend/src/services/achievement_service.py`

- [ ] **Step 1: Add `update_achievement` function**

Add this function after `get_achievement` (around line 115). Add the import for `AchievementUpdate` at the top alongside the existing schema imports.

Import line to add (in the existing import block at line 19):
```python
from src.schemas.achievement import AchievementCreate, AchievementResponse, AchievementUpdate
```

New function:
```python
async def update_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    achievement_id: uuid.UUID,
    data: AchievementUpdate,
) -> AchievementResponse | None:
    """Update achievement fields. Returns None if not found or not owned."""
    stmt = (
        select(Achievement)
        .join(CareerProfile, Achievement.profile_id == CareerProfile.id)
        .where(
            Achievement.id == achievement_id,
            CareerProfile.user_id == user_id,
        )
    )
    result = await session.execute(stmt)
    achievement = result.scalar_one_or_none()
    if achievement is None:
        return None

    # Auto-derive work_experience_id from project when project_id is set
    if data.project_id is not None:
        from src.models.project import Project
        proj_stmt = select(Project).where(Project.id == data.project_id)
        proj_result = await session.execute(proj_stmt)
        project = proj_result.scalar_one_or_none()
        if project and project.work_experience_id:
            achievement.work_experience_id = project.work_experience_id
        elif data.work_experience_id is not None:
            achievement.work_experience_id = data.work_experience_id
    elif data.project_id is None and data.project_id is not None:
        # Explicitly set to null (client sent null)
        achievement.project_id = None

    update_fields = {
        "title": data.title,
        "raw_content": data.raw_content,
        "tags": data.tags,
    }
    for field, value in update_fields.items():
        if value is not None:
            setattr(achievement, field, value)

    # Handle project_id explicitly (can be set to None)
    if data.project_id is not None:
        achievement.project_id = data.project_id

    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement)
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/services/achievement_service.py
git commit -m "feat(service): add update_achievement function"
```

---

### Task 3: Backend — Add PATCH /achievements/:id endpoint

**Files:**
- Modify: `backend/src/api/achievements.py`

- [ ] **Step 1: Add the PATCH endpoint**

Add import at top (update line 12):
```python
from src.schemas.achievement import AchievementCreate, AchievementResponse, AchievementUpdate
```

Add this endpoint before the `analyze` endpoint (before line 64):

```python
@router.patch(
    "/{achievement_id}",
    response_model=AchievementResponse,
    summary="Update an achievement",
)
async def update_achievement(
    body: AchievementUpdate,
    achievement_id: uuid.UUID = Path(..., description="The achievement UUID"),
    db: AsyncSession = Depends(get_db),
) -> AchievementResponse:
    """Update achievement fields. Supports reassigning to a project."""
    user_id = await get_current_user_id()
    result = await achievement_service.update_achievement(db, user_id, achievement_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result
```

- [ ] **Step 2: Verify import**

Run: `cd backend && python -c "from src.api.achievements import router; print([r.path for r in router.routes])"`
Expected: routes include `/{achievement_id}` with PATCH method

- [ ] **Step 3: Commit**

```bash
git add backend/src/api/achievements.py
git commit -m "feat(api): add PATCH /achievements/:id endpoint"
```

---

### Task 4: Frontend — Add achievementApi.update and useUpdateAchievement hook

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/hooks/useAchievements.ts`

- [ ] **Step 1: Add update method to achievementApi in `api.ts`**

After the existing `analyze` line in `achievementApi` (line 59), add:

```typescript
  update: (id: string, data: unknown) =>
    apiClient.patch(`/achievements/${id}`, data),
```

- [ ] **Step 2: Add `useUpdateAchievement` hook in `useAchievements.ts`**

Append after the `useAnalyzeAchievement` function:

```typescript
export function useUpdateAchievement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await achievementApi.update(id, data);
      return res.data as Achievement;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/useAchievements.ts
git commit -m "feat(frontend): add useUpdateAchievement hook and API method"
```

---

### Task 5: Frontend — Extract WorkExperienceModal and ProjectModal to shared components

**Files:**
- Create: `frontend/src/components/portfolio/WorkExperienceModal.tsx`
- Create: `frontend/src/components/portfolio/ProjectModal.tsx`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p frontend/src/components/portfolio
```

- [ ] **Step 2: Create WorkExperienceModal.tsx**

Copy the `WorkExperienceModal` component from `frontend/src/pages/CareerPortfolio.tsx` (lines 578–722) into a new file. Add the necessary imports at the top:

```typescript
import { useState, type FormEvent } from "react";
import { X, Loader2 } from "lucide-react";
import { useWorkExperiences } from "@/hooks/useWorkExperiences";
import type { WorkExperience } from "@/types";

// ... paste the WEFormData interface and WorkExperienceModal component exactly as-is
```

Export the component: ensure the function is `export function WorkExperienceModal(...)`.

- [ ] **Step 3: Create ProjectModal.tsx**

Copy the `ProjectModal` component from `frontend/src/pages/CareerPortfolio.tsx` (lines 736–893) into a new file. Add imports:

```typescript
import { useState, type FormEvent } from "react";
import { X, Loader2 } from "lucide-react";
import { useWorkExperiences } from "@/hooks/useWorkExperiences";
import type { Project } from "@/types";

// ... paste the ProjectFormData interface and ProjectModal component exactly as-is
```

Export the component: ensure the function is `export function ProjectModal(...)`.

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/portfolio/WorkExperienceModal.tsx frontend/src/components/portfolio/ProjectModal.tsx
git commit -m "refactor: extract WorkExperienceModal and ProjectModal to shared components"
```

---

### Task 6: Frontend — Create AchievementExpandable component

**Files:**
- Create: `frontend/src/components/portfolio/AchievementExpandable.tsx`

- [ ] **Step 1: Create the component**

```typescript
import { useState } from "react";
import { ChevronDown, ChevronRight, Pencil, Trash2, Loader2 } from "lucide-react";
import { useAnalyzeAchievement, useUpdateAchievement } from "@/hooks/useAchievements";
import type { Achievement } from "@/types";

interface AchievementExpandableProps {
  achievement: Achievement;
  onRemove?: () => void;
  showRemove?: boolean;
}

export function AchievementExpandable({ achievement, onRemove, showRemove = false }: AchievementExpandableProps) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(achievement.title);
  const [editContent, setEditContent] = useState(achievement.raw_content ?? "");
  const updateAchievement = useUpdateAchievement();
  const analyzeAchievement = useAnalyzeAchievement();

  const hasParsed = achievement.status !== "raw";
  const parsedData = achievement.parsed_data as Record<string, unknown> | null;
  const summary = (parsedData?.summary as string) ?? null;

  const handleSave = () => {
    updateAchievement.mutate(
      { id: achievement.id, data: { title: editTitle, raw_content: editContent } },
      { onSuccess: () => setEditing(false) },
    );
  };

  const handleRemove = () => {
    updateAchievement.mutate(
      { id: achievement.id, data: { project_id: null } },
      { onSuccess: () => onRemove?.() },
    );
  };

  return (
    <div className="rounded-md border bg-muted/20">
      {/* Collapsed row */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        )}
        <span className="text-sm font-medium text-foreground truncate flex-1">
          {achievement.title}
        </span>
        {achievement.importance_score > 0 && (
          <span className="inline-flex rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">
            {achievement.importance_score}
          </span>
        )}
        <span className={`inline-flex rounded px-1.5 py-0.5 text-xs ${
          hasParsed ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"
        }`}>
          {hasParsed ? "已分析" : "未分析"}
        </span>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t px-3 py-2 space-y-2">
          {editing ? (
            <div className="space-y-2">
              <input
                className="w-full rounded-md border px-2 py-1.5 text-sm"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
              />
              <textarea
                className="w-full rounded-md border px-2 py-1.5 text-sm resize-none"
                rows={3}
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setEditing(false)}
                  className="rounded-md border px-3 py-1 text-xs hover:bg-muted transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleSave}
                  disabled={updateAchievement.isPending}
                  className="rounded-md bg-primary px-3 py-1 text-xs text-primary-foreground disabled:opacity-50"
                >
                  {updateAchievement.isPending ? "保存中..." : "保存"}
                </button>
              </div>
            </div>
          ) : (
            <>
              {hasParsed && summary && (
                <p className="text-xs text-muted-foreground">{summary}</p>
              )}
              {achievement.tags && achievement.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {achievement.tags.map((tag) => (
                    <span key={tag} className="inline-flex rounded bg-indigo-50 px-1.5 py-0.5 text-xs text-indigo-700">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              {achievement.raw_content && (
                <p className="text-xs text-muted-foreground/70 italic line-clamp-3">
                  {achievement.raw_content}
                </p>
              )}
            </>
          )}

          {/* Actions */}
          {!editing && (
            <div className="flex items-center gap-1 pt-1 border-t">
              <button
                onClick={() => setEditing(true)}
                className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="编辑"
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
              {!hasParsed && (
                <button
                  onClick={() => analyzeAchievement.mutate(achievement.id)}
                  disabled={analyzeAchievement.isPending}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
                  title="分析"
                >
                  {analyzeAchievement.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
                  分析
                </button>
              )}
              {showRemove && (
                <button
                  onClick={handleRemove}
                  disabled={updateAchievement.isPending}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors disabled:opacity-50"
                  title="从项目中移除"
                >
                  移除
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/AchievementExpandable.tsx
git commit -m "feat: add AchievementExpandable component with inline edit/expand"
```

---

### Task 7: Frontend — Create AchievementAssignSelector component

**Files:**
- Create: `frontend/src/components/portfolio/AchievementAssignSelector.tsx`

- [ ] **Step 1: Create the component**

```typescript
import { useState, useRef, useEffect } from "react";
import type { WorkExperience, Project } from "@/types";

interface AchievementAssignSelectorProps {
  workExperiences: WorkExperience[];
  projects: Project[];
  onSelect: (projectId: string, workExperienceId: string | null) => void;
  onClose: () => void;
}

export function AchievementAssignSelector({
  workExperiences,
  projects,
  onSelect,
  onClose,
}: AchievementAssignSelectorProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  // Group projects by work_experience_id
  const weMap = new Map<string, WorkExperience>();
  for (const we of workExperiences) weMap.set(we.id, we);

  const projectsByWE = new Map<string, Project[]>();
  const standalone: Project[] = [];
  for (const p of projects) {
    if (p.work_experience_id) {
      const list = projectsByWE.get(p.work_experience_id) ?? [];
      list.push(p);
      projectsByWE.set(p.work_experience_id, list);
    } else {
      standalone.push(p);
    }
  }

  const filteredWEs = workExperiences.filter((we) => {
    const ps = projectsByWE.get(we.id) ?? [];
    return ps.some((p) => p.name.toLowerCase().includes(search.toLowerCase()));
  });
  const filteredStandalone = standalone.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div ref={ref} className="absolute z-50 mt-1 w-64 rounded-md border bg-card shadow-lg">
      <div className="p-2 border-b">
        <input
          className="w-full rounded-md border px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-primary/50"
          placeholder="搜索项目..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />
      </div>
      <div className="max-h-48 overflow-y-auto p-1">
        {filteredWEs.map((we) => {
          const ps = (projectsByWE.get(we.id) ?? []).filter((p) =>
            p.name.toLowerCase().includes(search.toLowerCase()),
          );
          if (ps.length === 0) return null;
          return (
            <div key={we.id}>
              <div className="px-2 py-1 text-xs font-medium text-muted-foreground">
                {we.company_name}
              </div>
              {ps.map((p) => (
                <button
                  key={p.id}
                  className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-muted transition-colors"
                  onClick={() => onSelect(p.id, p.work_experience_id ?? null)}
                >
                  {p.name}
                </button>
              ))}
            </div>
          );
        })}
        {filteredStandalone.length > 0 && (
          <div>
            <div className="px-2 py-1 text-xs font-medium text-muted-foreground">独立项目</div>
            {filteredStandalone.map((p) => (
              <button
                key={p.id}
                className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-muted transition-colors"
                onClick={() => onSelect(p.id, null)}
              >
                {p.name}
              </button>
            ))}
          </div>
        )}
        {filteredWEs.length === 0 && filteredStandalone.length === 0 && (
          <p className="px-2 py-3 text-xs text-muted-foreground text-center">无匹配项目</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/AchievementAssignSelector.tsx
git commit -m "feat: add AchievementAssignSelector dropdown component"
```

---

### Task 8: Frontend — Rewrite CareerPortfolio.tsx as layout wrapper

**Files:**
- Modify: `frontend/src/pages/CareerPortfolio.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Replace CareerPortfolio.tsx with layout wrapper**

Replace the entire file content with:

```typescript
import { Outlet } from "react-router-dom";
import { Header } from "@/components/layout/Header";

export function CareerPortfolio() {
  return (
    <>
      <Header title="职业履历" description="按公司、项目、成果三层结构管理你的职业经历" />
      <Outlet />
    </>
  );
}
```

- [ ] **Step 2: Update App.tsx routes**

Replace the current `/portfolio` route with nested routes. Change line 39 from:

```tsx
<Route path="/portfolio" element={<CareerPortfolio />} />
```

to:

```tsx
<Route path="/portfolio" element={<CareerPortfolio />}>
  <Route index element={<Overview />} />
  <Route path=":weId" element={<CompanyDetail />} />
  <Route path=":weId/:projectId" element={<ProjectDetail />} />
</Route>
```

Add the new imports at top:

```tsx
import { Overview } from "@/pages/CareerPortfolio/Overview";
import { CompanyDetail } from "@/pages/CareerPortfolio/CompanyDetail";
import { ProjectDetail } from "@/pages/CareerPortfolio/ProjectDetail";
```

- [ ] **Step 3: Verify build (will fail — pages don't exist yet)**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -5`
Expected: errors about missing Overview, CompanyDetail, ProjectDetail — this is expected

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/CareerPortfolio.tsx frontend/src/App.tsx
git commit -m "refactor: CareerPortfolio becomes layout wrapper with nested routes"
```

---

### Task 9: Frontend — Create Overview page

**Files:**
- Create: `frontend/src/pages/CareerPortfolio/Overview.tsx`

- [ ] **Step 1: Create directory**

```bash
mkdir -p frontend/src/pages/CareerPortfolio
```

- [ ] **Step 2: Create Overview.tsx**

```typescript
import { useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { WorkExperienceModal } from "@/components/portfolio/WorkExperienceModal";
import { ProjectModal } from "@/components/portfolio/ProjectModal";
import { AchievementAssignSelector } from "@/components/portfolio/AchievementAssignSelector";
import {
  useWorkExperiences,
  useCreateWorkExperience,
  useUpdateWorkExperience,
  useDeleteWorkExperience,
} from "@/hooks/useWorkExperiences";
import {
  useProjects,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from "@/hooks/useProjects";
import { useAchievements, useUpdateAchievement } from "@/hooks/useAchievements";
import {
  Plus, Building2, FolderKanban, Trophy, Loader2, AlertTriangle,
  FileText, ChevronDown, ChevronRight, Pencil, Trash2, Calendar, MapPin,
} from "lucide-react";
import type { WorkExperience, Achievement } from "@/types";

function formatDate(date: string | null): string {
  if (!date) return "至今";
  return new Date(date).toLocaleDateString("zh-CN", { year: "numeric", month: "short" });
}

export function Overview() {
  const navigate = useNavigate();
  const { data: workExperiences, isLoading: loadingWE } = useWorkExperiences();
  const { data: projects, isLoading: loadingP } = useProjects();
  const { data: achievements, isLoading: loadingA } = useAchievements();

  const createWE = useCreateWorkExperience();
  const updateWE = useUpdateWorkExperience();
  const deleteWE = useDeleteWorkExperience();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const updateAchievement = useUpdateAchievement();

  const [showCreateWE, setShowCreateWE] = useState(false);
  const [editWE, setEditWE] = useState<WorkExperience | null>(null);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [editProject, setEditProject] = useState<WorkExperience | null>(null);
  const [expandedWEs, setExpandedWEs] = useState<Set<string>>(new Set());
  const [assigningAchId, setAssigningAchId] = useState<string | null>(null);

  const isLoading = loadingWE || loadingP || loadingA;

  const grouped = useMemo(() => {
    const wes = workExperiences ?? [];
    const ps = projects ?? [];
    const as = achievements ?? [];

    const projectsByWE = new Map<string, typeof ps>();
    const standaloneProjects: typeof ps = [];
    for (const p of ps) {
      if (p.work_experience_id) {
        const list = projectsByWE.get(p.work_experience_id) ?? [];
        list.push(p);
        projectsByWE.set(p.work_experience_id, list);
      } else {
        standaloneProjects.push(p);
      }
    }

    const standaloneAchievements = as.filter((a) => !a.project_id && !a.work_experience_id);

    return { wes, projectsByWE, standaloneProjects, standaloneAchievements };
  }, [workExperiences, projects, achievements]);

  // Auto-expand all WEs on first load
  useMemo(() => {
    if (grouped.wes.length > 0 && expandedWEs.size === 0) {
      setExpandedWEs(new Set(grouped.wes.map((w) => w.id)));
    }
  }, [grouped.wes]);

  const toggleWE = useCallback((id: string) => {
    setExpandedWEs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const handleAssign = (achId: string, projectId: string, weId: string | null) => {
    updateAchievement.mutate(
      { id: achId, data: { project_id: projectId, work_experience_id: weId } },
      { onSuccess: () => setAssigningAchId(null) },
    );
  };

  const weCount = grouped.wes.length;
  const projectCount = (projects ?? []).length;
  const achievementCount = (achievements ?? []).length;

  return (
    <>
      {/* Sticky toolbar */}
      <div className="sticky top-0 z-10 border-b bg-card">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{weCount} 家公司</span>
            <span className="inline-flex items-center gap-1"><FolderKanban className="h-3.5 w-3.5" />{projectCount} 个项目</span>
            <span className="inline-flex items-center gap-1"><Trophy className="h-3.5 w-3.5" />{achievementCount} 个成果</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowCreateProject(true)} className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">
              <Plus className="h-3.5 w-3.5" />新增项目
            </button>
            <button onClick={() => setShowCreateWE(true)} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
              <Plus className="h-4 w-4" />新增工作经历
            </button>
          </div>
        </div>
      </div>

      <PageContainer>
        <div className="space-y-4">
          {isLoading && (
            <div className="flex items-center justify-center rounded-lg border bg-card p-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">加载中...</span>
            </div>
          )}

          {!isLoading && grouped.wes.length === 0 && grouped.standaloneProjects.length === 0 && grouped.standaloneAchievements.length === 0 && (
            <div className="rounded-lg border bg-card p-8 text-center">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">暂无职业履历记录</p>
              <p className="mt-1 text-sm text-muted-foreground">点击「新增工作经历」开始构建你的职业档案。</p>
            </div>
          )}

          {!isLoading && grouped.wes.map((we) => {
            const isExpanded = expandedWEs.has(we.id);
            const weProjects = grouped.projectsByWE.get(we.id) ?? [];

            return (
              <div key={we.id} className="rounded-lg border bg-card overflow-hidden">
                <div className="flex items-start gap-3 p-4 cursor-pointer hover:bg-muted/30 transition-colors" onClick={() => toggleWE(we.id)}>
                  <div className="mt-0.5 shrink-0">
                    {isExpanded ? <ChevronDown className="h-5 w-5 text-muted-foreground" /> : <ChevronRight className="h-5 w-5 text-muted-foreground" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <a className="text-base font-semibold text-foreground hover:text-primary transition-colors" onClick={(e) => { e.stopPropagation(); navigate(`/portfolio/${we.id}`); }}>
                            {we.company_name}
                          </a>
                          {we.role_title && <span className="text-sm text-muted-foreground">{we.role_title}</span>}
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="inline-flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(we.start_date)} - {formatDate(we.end_date)}</span>
                          {we.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{we.location}</span>}
                          <span>{weProjects.length} 个项目</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
                        <button onClick={() => setEditWE(we)} className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors" title="编辑"><Pencil className="h-3.5 w-3.5" /></button>
                        <button onClick={() => { if (confirm(`确定删除 ${we.company_name} 的工作经历？`)) deleteWE.mutate(we.id); }} className="rounded-md p-1.5 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors" title="删除"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </div>
                  </div>
                </div>

                {isExpanded && (
                  <div className="border-t pl-8 pr-4 py-3 space-y-2">
                    {weProjects.map((p) => (
                      <div key={p.id} className="flex items-center gap-2 text-sm">
                        <FolderKanban className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                        <a className="text-foreground hover:text-primary transition-colors" onClick={() => navigate(`/portfolio/${we.id}/${p.id}`)}>{p.name}</a>
                        <div className="flex gap-1">
                          {p.tech_stack?.slice(0, 3).map((t) => (
                            <span key={t} className="rounded bg-blue-50 px-1 py-0.5 text-xs text-blue-700">{t}</span>
                          ))}
                        </div>
                        <div className="flex gap-1 shrink-0 ml-auto">
                          <button onClick={() => setEditProject(p as unknown as WorkExperience)} className="rounded-md p-1 text-muted-foreground hover:bg-muted transition-colors" title="编辑"><Pencil className="h-3 w-3" /></button>
                          <button onClick={() => { if (confirm(`确定删除项目 ${p.name}？`)) deleteProject.mutate(p.id); }} className="rounded-md p-1 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors" title="删除"><Trash2 className="h-3 w-3" /></button>
                        </div>
                      </div>
                    ))}
                    <button onClick={() => navigate(`/portfolio/${we.id}`)} className="text-xs text-primary hover:underline">查看全部 →</button>
                  </div>
                )}
              </div>
            );
          })}

          {/* Standalone projects */}
          {!isLoading && grouped.standaloneProjects.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-muted-foreground">独立项目</h3>
              {grouped.standaloneProjects.map((p) => (
                <div key={p.id} className="rounded-lg border bg-card p-3 flex items-center gap-2">
                  <FolderKanban className="h-4 w-4 text-blue-500 shrink-0" />
                  <span className="text-sm font-medium">{p.name}</span>
                  <div className="flex gap-1">
                    {p.tech_stack?.slice(0, 3).map((t) => (
                      <span key={t} className="rounded bg-blue-50 px-1 py-0.5 text-xs text-blue-700">{t}</span>
                    ))}
                  </div>
                  <div className="ml-auto flex gap-1">
                    <button onClick={() => setEditProject(p as unknown as WorkExperience)} className="rounded-md p-1 text-muted-foreground hover:bg-muted transition-colors" title="编辑"><Pencil className="h-3 w-3" /></button>
                    <button onClick={() => { if (confirm(`确定删除项目 ${p.name}？`)) deleteProject.mutate(p.id); }} className="rounded-md p-1 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors" title="删除"><Trash2 className="h-3 w-3" /></button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Orphaned achievements */}
          {!isLoading && grouped.standaloneAchievements.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-muted-foreground">
                未归档成果 ({grouped.standaloneAchievements.length})
              </h3>
              {grouped.standaloneAchievements.map((ach) => (
                <div key={ach.id} className="relative flex items-center gap-2 rounded-md border bg-card px-3 py-2">
                  <Trophy className="h-3.5 w-3.5 shrink-0 text-amber-500" />
                  <span className="text-sm font-medium flex-1 truncate">{ach.title}</span>
                  {ach.importance_score > 0 && (
                    <span className="rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-700">{ach.importance_score}</span>
                  )}
                  <span className={`rounded px-1.5 py-0.5 text-xs ${
                    ach.status !== "raw" ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"
                  }`}>
                    {ach.status !== "raw" ? "已分析" : "未分析"}
                  </span>
                  <button
                    onClick={() => setAssigningAchId(assigningAchId === ach.id ? null : ach.id)}
                    className="rounded-md bg-primary px-2 py-1 text-xs text-primary-foreground hover:bg-primary/90 transition-colors"
                  >
                    归档到项目
                  </button>
                  {assigningAchId === ach.id && (
                    <AchievementAssignSelector
                      workExperiences={workExperiences ?? []}
                      projects={projects ?? []}
                      onSelect={(projId, weId) => handleAssign(ach.id, projId, weId)}
                      onClose={() => setAssigningAchId(null)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </PageContainer>

      {/* Modals */}
      {showCreateWE && (
        <WorkExperienceModal title="新增工作经历" onSubmit={(data) => { createWE.mutate(data, { onSuccess: () => setShowCreateWE(false) }); }} onClose={() => setShowCreateWE(false)} isSubmitting={createWE.isPending} />
      )}
      {editWE && (
        <WorkExperienceModal title="编辑工作经历" initial={editWE} onSubmit={(data) => { updateWE.mutate({ id: editWE.id, data }, { onSuccess: () => setEditWE(null) }); }} onClose={() => setEditWE(null)} isSubmitting={updateWE.isPending} />
      )}
      {showCreateProject && (
        <ProjectModal title="新增项目" onSubmit={(data) => { createProject.mutate(data, { onSuccess: () => setShowCreateProject(false) }); }} onClose={() => setShowCreateProject(false)} isSubmitting={createProject.isPending} />
      )}
      {editProject && (
        <ProjectModal title="编辑项目" initial={editProject as unknown as import("@/types").Project} onSubmit={(data) => { updateProject.mutate({ id: editProject.id, data }, { onSuccess: () => setEditProject(null) }); }} onClose={() => setEditProject(null)} isSubmitting={updateProject.isPending} />
      )}
    </>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/CareerPortfolio/Overview.tsx
git commit -m "feat: add Overview page for CareerPortfolio"
```

---

### Task 10: Frontend — Create CompanyDetail page

**Files:**
- Create: `frontend/src/pages/CareerPortfolio/CompanyDetail.tsx`

- [ ] **Step 1: Create CompanyDetail.tsx**

```typescript
import { useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { WorkExperienceModal } from "@/components/portfolio/WorkExperienceModal";
import { ProjectModal } from "@/components/portfolio/ProjectModal";
import { AchievementExpandable } from "@/components/portfolio/AchievementExpandable";
import { AchievementAssignSelector } from "@/components/portfolio/AchievementAssignSelector";
import { useWorkExperiences, useUpdateWorkExperience, useDeleteWorkExperience } from "@/hooks/useWorkExperiences";
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject } from "@/hooks/useProjects";
import { useAchievements, useUpdateAchievement } from "@/hooks/useAchievements";
import { ChevronRight, Pencil, Trash2, Plus, FolderKanban, Calendar, MapPin, ExternalLink } from "lucide-react";

function formatDate(date: string | null): string {
  if (!date) return "至今";
  return new Date(date).toLocaleDateString("zh-CN", { year: "numeric", month: "short" });
}

export function CompanyDetail() {
  const { weId } = useParams<{ weId: string }>();
  const navigate = useNavigate();

  const { data: workExperiences } = useWorkExperiences();
  const { data: projects } = useProjects();
  const { data: achievements } = useAchievements();

  const updateWE = useUpdateWorkExperience();
  const deleteWE = useDeleteWorkExperience();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const updateAchievement = useUpdateAchievement();

  const [editWE, setEditWE] = useState<import("@/types").WorkExperience | null>(null);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [editProject, setEditProject] = useState<import("@/types").Project | null>(null);
  const [assigningAchId, setAssigningAchId] = useState<string | null>(null);

  const we = workExperiences?.find((w) => w.id === weId);

  const weProjects = useMemo(
    () => (projects ?? []).filter((p) => p.work_experience_id === weId),
    [projects, weId],
  );

  const weAchievements = useMemo(
    () => (achievements ?? []).filter((a) => a.work_experience_id === weId && !a.project_id),
    [achievements, weId],
  );

  if (!we) {
    return (
      <PageContainer>
        <div className="text-center py-12 text-muted-foreground">工作经历不存在</div>
      </PageContainer>
    );
  }

  const handleAssign = (achId: string, projectId: string, workExpId: string | null) => {
    updateAchievement.mutate(
      { id: achId, data: { project_id: projectId, work_experience_id: workExpId ?? weId } },
      { onSuccess: () => setAssigningAchId(null) },
    );
  };

  return (
    <>
      <PageContainer>
        <div className="space-y-6">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Link to="/portfolio" className="text-primary hover:underline">职业履历</Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="font-medium text-foreground">{we.company_name}</span>
          </nav>

          {/* Company info */}
          <div className="rounded-lg border bg-card p-5">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">{we.company_name}</h2>
                <p className="text-muted-foreground mt-1">{we.role_title}</p>
                <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(we.start_date)} - {formatDate(we.end_date)}</span>
                  {we.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{we.location}</span>}
                </div>
                {we.description && <p className="mt-3 text-sm text-muted-foreground">{we.description}</p>}
              </div>
              <div className="flex gap-1">
                <button onClick={() => setEditWE(we)} className="rounded-md p-2 text-muted-foreground hover:bg-muted transition-colors" title="编辑"><Pencil className="h-4 w-4" /></button>
                <button onClick={() => { if (confirm(`确定删除 ${we.company_name}？关联的项目和成果也会被删除。`)) { deleteWE.mutate(we.id, { onSuccess: () => navigate("/portfolio") }); } }} className="rounded-md p-2 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors" title="删除"><Trash2 className="h-4 w-4" /></button>
              </div>
            </div>
          </div>

          {/* Project list */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">项目 ({weProjects.length})</h3>
              <button onClick={() => setShowCreateProject(true)} className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
                <Plus className="h-3.5 w-3.5" />新增项目
              </button>
            </div>
            {weProjects.length === 0 && (
              <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
                暂无项目，点击「新增项目」开始添加
              </div>
            )}
            {weProjects.map((p) => {
              const pAchs = (achievements ?? []).filter((a) => a.project_id === p.id);
              return (
                <div key={p.id} className="rounded-lg border bg-card p-4 cursor-pointer hover:border-primary/30 transition-colors" onClick={() => navigate(`/portfolio/${weId}/${p.id}`)}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FolderKanban className="h-4 w-4 text-blue-500 shrink-0" />
                        <h4 className="font-medium">{p.name}</h4>
                      </div>
                      {p.description && <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{p.description}</p>}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {p.tech_stack?.map((t) => (
                          <span key={t} className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">{t}</span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 text-xs text-muted-foreground" onClick={(e) => e.stopPropagation()}>
                      <span>{pAchs.length} 成果</span>
                      <button onClick={() => setEditProject(p)} className="rounded-md p-1 text-muted-foreground hover:bg-muted transition-colors" title="编辑"><Pencil className="h-3 w-3" /></button>
                      <button onClick={() => { if (confirm(`确定删除项目 ${p.name}？`)) deleteProject.mutate(p.id); }} className="rounded-md p-1 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors" title="删除"><Trash2 className="h-3 w-3" /></button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* WE-level achievements (not in a project) */}
          {weAchievements.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">未归入项目的成果 ({weAchievements.length})</h3>
              {weAchievements.map((ach) => (
                <div key={ach.id} className="relative flex items-center gap-2 rounded-md border bg-card px-3 py-2">
                  <AchievementExpandable achievement={ach} />
                  <div className="shrink-0">
                    <button onClick={() => setAssigningAchId(assigningAchId === ach.id ? null : ach.id)} className="rounded-md bg-primary px-2 py-1 text-xs text-primary-foreground hover:bg-primary/90">
                      归档到项目
                    </button>
                    {assigningAchId === ach.id && (
                      <AchievementAssignSelector
                        workExperiences={workExperiences ?? []}
                        projects={weProjects}
                        onSelect={(projId, workExpId) => handleAssign(ach.id, projId, workExpId)}
                        onClose={() => setAssigningAchId(null)}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </PageContainer>

      {/* Modals */}
      {editWE && (
        <WorkExperienceModal title="编辑工作经历" initial={editWE} onSubmit={(data) => { updateWE.mutate({ id: editWE.id, data }, { onSuccess: () => setEditWE(null) }); }} onClose={() => setEditWE(null)} isSubmitting={updateWE.isPending} />
      )}
      {showCreateProject && (
        <ProjectModal title="新增项目" defaultWorkExperienceId={weId} onSubmit={(data) => { createProject.mutate(data, { onSuccess: () => setShowCreateProject(false) }); }} onClose={() => setShowCreateProject(false)} isSubmitting={createProject.isPending} />
      )}
      {editProject && (
        <ProjectModal title="编辑项目" initial={editProject} onSubmit={(data) => { updateProject.mutate({ id: editProject.id, data }, { onSuccess: () => setEditProject(null) }); }} onClose={() => setEditProject(null)} isSubmitting={updateProject.isPending} />
      )}
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/CareerPortfolio/CompanyDetail.tsx
git commit -m "feat: add CompanyDetail page for CareerPortfolio"
```

---

### Task 11: Frontend — Create ProjectDetail page

**Files:**
- Create: `frontend/src/pages/CareerPortfolio/ProjectDetail.tsx`

- [ ] **Step 1: Create ProjectDetail.tsx**

```typescript
import { useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { PageContainer } from "@/components/layout/PageContainer";
import { ProjectModal } from "@/components/portfolio/ProjectModal";
import { AchievementExpandable } from "@/components/portfolio/AchievementExpandable";
import { useWorkExperiences } from "@/hooks/useWorkExperiences";
import { useProjects, useUpdateProject, useDeleteProject } from "@/hooks/useProjects";
import { useAchievements, useCreateAchievement } from "@/hooks/useAchievements";
import { ChevronRight, Pencil, Trash2, Plus, Calendar, ExternalLink } from "lucide-react";

function formatDate(date: string | null): string {
  if (!date) return "至今";
  return new Date(date).toLocaleDateString("zh-CN", { year: "numeric", month: "short" });
}

export function ProjectDetail() {
  const { weId, projectId } = useParams<{ weId: string; projectId: string }>();
  const navigate = useNavigate();

  const { data: workExperiences } = useWorkExperiences();
  const { data: projects } = useProjects();
  const { data: achievements } = useAchievements();

  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const createAchievement = useCreateAchievement();

  const [editProject, setEditProject] = useState<import("@/types").Project | null>(null);
  const [showCreateAch, setShowCreateAch] = useState(false);
  const [achTitle, setAchTitle] = useState("");
  const [achContent, setAchContent] = useState("");

  const we = workExperiences?.find((w) => w.id === weId);
  const project = projects?.find((p) => p.id === projectId);

  const projectAchievements = useMemo(
    () => (achievements ?? []).filter((a) => a.project_id === projectId),
    [achievements, projectId],
  );

  if (!project) {
    return (
      <PageContainer>
        <div className="text-center py-12 text-muted-foreground">项目不存在</div>
      </PageContainer>
    );
  }

  const handleDeleteProject = () => {
    if (confirm(`确定删除项目 ${project.name}？`)) {
      deleteProject.mutate(project.id, { onSuccess: () => navigate(`/portfolio/${weId}`) });
    }
  };

  const handleCreateAch = () => {
    createAchievement.mutate(
      {
        title: achTitle,
        raw_content: achContent,
        project_id: projectId,
        work_experience_id: weId,
        source_type: "manual",
      },
      { onSuccess: () => { setShowCreateAch(false); setAchTitle(""); setAchContent(""); } },
    );
  };

  // Build breadcrumb
  const parentLabel = we ? we.company_name : "独立项目";

  return (
    <>
      <PageContainer>
        <div className="space-y-6">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Link to="/portfolio" className="text-primary hover:underline">职业履历</Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <Link to={`/portfolio/${weId}`} className="text-primary hover:underline">{parentLabel}</Link>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="font-medium text-foreground">{project.name}</span>
          </nav>

          {/* Project info */}
          <div className="rounded-lg border bg-card p-5">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-xl font-semibold">{project.name}</h2>
                {(project.start_date || project.end_date) && (
                  <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {formatDate(project.start_date)} - {formatDate(project.end_date)}
                  </div>
                )}
                {project.url && (
                  <a href={project.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline">
                    <ExternalLink className="h-3 w-3" />{project.url}
                  </a>
                )}
                {project.description && (
                  <p className="mt-3 text-sm text-muted-foreground whitespace-pre-wrap">{project.description}</p>
                )}
                {project.tech_stack && project.tech_stack.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {project.tech_stack.map((tech) => (
                      <span key={tech} className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs text-blue-700">{tech}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-1 shrink-0">
                <button onClick={() => setEditProject(project)} className="rounded-md p-2 text-muted-foreground hover:bg-muted transition-colors" title="编辑"><Pencil className="h-4 w-4" /></button>
                <button onClick={handleDeleteProject} className="rounded-md p-2 text-muted-foreground hover:bg-red-50 hover:text-red-500 transition-colors" title="删除"><Trash2 className="h-4 w-4" /></button>
              </div>
            </div>
          </div>

          {/* Achievement list */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">成果 ({projectAchievements.length})</h3>
              <button onClick={() => setShowCreateAch(true)} className="inline-flex items-center gap-1 text-sm text-primary hover:underline">
                <Plus className="h-3.5 w-3.5" />新增成果
              </button>
            </div>

            {projectAchievements.length === 0 && (
              <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
                暂无成果，点击「新增成果」开始添加
              </div>
            )}

            <div className="space-y-2">
              {projectAchievements.map((ach) => (
                <AchievementExpandable
                  key={ach.id}
                  achievement={ach}
                  showRemove={true}
                />
              ))}
            </div>
          </div>

          {/* Create achievement form */}
          {showCreateAch && (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <h4 className="text-sm font-medium">新增成果</h4>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                placeholder="成果标题"
                value={achTitle}
                onChange={(e) => setAchTitle(e.target.value)}
              />
              <textarea
                className="w-full rounded-md border px-3 py-2 text-sm resize-none"
                rows={3}
                placeholder="详细描述你的成果..."
                value={achContent}
                onChange={(e) => setAchContent(e.target.value)}
              />
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowCreateAch(false)} className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted transition-colors">取消</button>
                <button
                  onClick={handleCreateAch}
                  disabled={!achTitle.trim() || createAchievement.isPending}
                  className="rounded-md bg-primary px-4 py-1.5 text-sm text-primary-foreground disabled:opacity-50"
                >
                  {createAchievement.isPending ? "创建中..." : "创建"}
                </button>
              </div>
            </div>
          )}
        </div>
      </PageContainer>

      {/* Edit project modal */}
      {editProject && (
        <ProjectModal title="编辑项目" initial={editProject} onSubmit={(data) => { updateProject.mutate({ id: editProject.id, data }, { onSuccess: () => setEditProject(null) }); }} onClose={() => setEditProject(null)} isSubmitting={updateProject.isPending} />
      )}
    </>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/CareerPortfolio/ProjectDetail.tsx
git commit -m "feat: add ProjectDetail page with expandable achievements"
```

---

### Task 12: Fix type issues and verify full build

**Files:**
- Possibly fix: `frontend/src/pages/CareerPortfolio/Overview.tsx` — the `editProject` state type uses `WorkExperience` but should use `Project`

- [ ] **Step 1: Fix Overview.tsx types**

In Overview.tsx, the `editProject` state was typed as `WorkExperience` for convenience but should be typed as `Project | null`. Also the `ProjectModal` needs a `Project` initial value. Fix the state declaration:

Change line:
```typescript
const [editProject, setEditProject] = useState<WorkExperience | null>(null);
```
to:
```typescript
const [editProject, setEditProject] = useState<import("@/types").Project | null>(null);
```

And fix the casts on `setEditProject` calls — remove the `as unknown as WorkExperience` casts and change to direct Project type usage.

Fix the edit modal close to use the correct type:
```tsx
{editProject && (
  <ProjectModal title="编辑项目" initial={editProject} onSubmit={(data) => { updateProject.mutate({ id: editProject.id, data }, { onSuccess: () => setEditProject(null) }); }} onClose={() => setEditProject(null)} isSubmitting={updateProject.isPending} />
)}
```

Remove unused `AlertTriangle` import if present.

- [ ] **Step 2: Verify TypeScript and Vite build**

Run: `cd frontend && npx tsc --noEmit && npx vite build 2>&1 | tail -5`
Expected: no TypeScript errors, Vite build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/CareerPortfolio/
git commit -m "fix: correct types in Overview and verify full build"
```

---

## Verification

1. **Backend PATCH**: `curl -X PATCH http://localhost:8000/api/achievements/<id> -H "Content-Type: application/json" -d '{"title": "updated"}'` — returns updated achievement
2. **Achievement assignment**: `curl -X PATCH ... -d '{"project_id": "<uuid>"}'` — project_id and work_experience_id updated
3. **Frontend routing**: Navigate `/portfolio` → click company → `/portfolio/:weId` → click project → `/portfolio/:weId/:projectId` — breadcrumb updates, back button works
4. **Orphaned achievements**: On overview page, click "归档到项目" → select project → achievement disappears from orphaned list
5. **Expandable achievements**: On project detail, click achievement row → expands with summary/tags/content → can edit inline
6. **CRUD at every level**: Create/edit/delete works for WEs, projects, and achievements
7. **Build passes**: `npx tsc --noEmit && npx vite build` — zero errors
