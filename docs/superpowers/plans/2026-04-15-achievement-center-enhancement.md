# Achievement Center Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the achievement center with tab filtering, suggestion integration in detail drawer, and fix the accept-suggestion pipeline to properly update resume scores.

**Architecture:** Add `source_achievement_id` to `UpdateSuggestion` model for linking suggestions back to achievements. Fix backend accept logic to recalculate scores. Frontend gets sticky tab bar and suggestion cards in the detail drawer.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React 19, TanStack Query, TypeScript

---

### Task 1: Backend — Add `source_achievement_id` to UpdateSuggestion model

**Files:**
- Modify: `backend/src/models/agent.py:41-76`

- [ ] **Step 1: Add `source_achievement_id` column to UpdateSuggestion**

In `backend/src/models/agent.py`, add a new nullable column after `source_ref_id` (around line 62):

```python
    source_achievement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=True, default=None,
    )
```

The full column block should read:

```python
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    source_achievement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=True, default=None,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
```

- [ ] **Step 2: Create Alembic migration**

Create `backend/alembic/versions/20260415_01_add_source_achievement_id.py`:

```python
"""add source_achievement_id to update_suggestions

Revision ID: 20260415_01
Revises: da4d2ca574d9
Create Date: 2026-04-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260415_01'
down_revision: Union[str, None] = 'da4d2ca574d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('update_suggestions', sa.Column(
        'source_achievement_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
    ))
    op.create_foreign_key(
        'fk_update_suggestions_source_achievement_id',
        'update_suggestions', 'achievements',
        ['source_achievement_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_update_suggestions_source_achievement_id',
        'update_suggestions',
        type_='foreignkey',
    )
    op.drop_column('update_suggestions', 'source_achievement_id')
```

---

### Task 2: Backend — Set `source_achievement_id` when creating suggestions in achievement pipeline

**Files:**
- Modify: `backend/src/services/achievement_service.py:276-297`

- [ ] **Step 1: Add `source_achievement_id=achievement_id` to suggestion creation**

In `backend/src/services/achievement_service.py`, in the `run_achievement_pipeline` function, section `# 4c. Create update suggestions` (around line 277), add `source_achievement_id` to each suggestion:

```python
    # 4c. Create update suggestions
    for suggestion in pipeline_result.get("suggestions", []):
        sug = UpdateSuggestion(
            workspace_id=workspace_id,
            user_id=user_id,
            suggestion_type=suggestion.get("suggestion_type", "resume_update"),
            target_role_id=(
                uuid.UUID(suggestion["target_role_id"])
                if suggestion.get("target_role_id") else None
            ),
            resume_id=(
                uuid.UUID(suggestion["resume_id"])
                if suggestion.get("resume_id") else None
            ),
            source_type="achievement_pipeline",
            source_ref_id=achievement_id,
            source_achievement_id=achievement_id,
            title=suggestion.get("title", "Update suggestion"),
            content_json=suggestion.get("content"),
            impact_score_json={"score": suggestion.get("impact_score", 0.5)},
            risk_level=suggestion.get("risk_level", "low"),
            status="pending",
        )
        session.add(sug)
```

The only change is adding the line `source_achievement_id=achievement_id,` after `source_ref_id=achievement_id,`.

---

### Task 3: Backend — Add `achievement_id` filter to suggestions API

**Files:**
- Modify: `backend/src/services/suggestion_service.py:62-84`
- Modify: `backend/src/api/suggestions.py:18-42`

- [ ] **Step 1: Add `achievement_id` parameter to `list_suggestions` service**

In `backend/src/services/suggestion_service.py`, update the `list_suggestions` function signature (line 62) to accept `achievement_id`:

```python
async def list_suggestions(
    session: AsyncSession,
    user_id: uuid.UUID,
    suggestion_type: str | None = None,
    status: str | None = None,
    target_role_id: uuid.UUID | None = None,
    achievement_id: uuid.UUID | None = None,
) -> list[SuggestionResponse]:
    """Return suggestions for a user with optional filters."""
    stmt = (
        select(UpdateSuggestion)
        .where(UpdateSuggestion.user_id == user_id)
        .order_by(UpdateSuggestion.created_at.desc())
    )
    if suggestion_type is not None:
        stmt = stmt.where(UpdateSuggestion.suggestion_type == suggestion_type)
    if status is not None:
        stmt = stmt.where(UpdateSuggestion.status == status)
    if target_role_id is not None:
        stmt = stmt.where(UpdateSuggestion.target_role_id == target_role_id)
    if achievement_id is not None:
        stmt = stmt.where(UpdateSuggestion.source_achievement_id == achievement_id)

    result = await session.execute(stmt)
    suggestions = result.scalars().all()
    return [_to_response(s) for s in suggestions]
```

The changes are: add `achievement_id: uuid.UUID | None = None,` parameter, and add the filter block:
```python
    if achievement_id is not None:
        stmt = stmt.where(UpdateSuggestion.source_achievement_id == achievement_id)
```

- [ ] **Step 2: Add `achievement_id` query parameter to the API endpoint**

In `backend/src/api/suggestions.py`, update the `list_suggestions` endpoint (line 23):

```python
@router.get(
    "",
    response_model=list[SuggestionResponse],
    summary="List suggestions",
)
async def list_suggestions(
    suggestion_type: str | None = Query(
        default=None, description="Filter by type, e.g. resume_update, gap_update"
    ),
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by status: pending/accepted/rejected"
    ),
    target_role_id: uuid.UUID | None = Query(
        default=None, description="Filter by target role"
    ),
    achievement_id: uuid.UUID | None = Query(
        default=None, description="Filter by source achievement"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[SuggestionResponse]:
    """Return all suggestions, optionally filtered by type, status, role, or achievement."""
    user_id = await get_current_user_id()
    return await suggestion_service.list_suggestions(
        db, user_id,
        suggestion_type=suggestion_type,
        status=status_filter,
        target_role_id=target_role_id,
        achievement_id=achievement_id,
    )
```

The changes are: add `achievement_id` query parameter, and pass it to the service call.

---

### Task 4: Backend — Add `source_achievement_id` to SuggestionResponse schema

**Files:**
- Modify: `backend/src/schemas/suggestion.py:11-27`

- [ ] **Step 1: Add field to SuggestionResponse**

In `backend/src/schemas/suggestion.py`, add `source_achievement_id` after `resume_id`:

```python
class SuggestionResponse(BaseModel):
    """Full suggestion detail returned by the API."""

    id: UUID
    suggestion_type: str
    target_role_id: UUID | None = None
    resume_id: UUID | None = None
    source_achievement_id: UUID | None = None
    title: str
    content: str = ""
    impact_score: float = 0.0
    risk_level: str = "low"
    status: str = "pending"
    applied_resume_version_id: UUID | None = None
    apply_result: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Update `_to_response` in suggestion_service to include new field**

In `backend/src/services/suggestion_service.py`, update `_to_response` (around line 19) to include `source_achievement_id`:

```python
def _to_response(s: UpdateSuggestion) -> SuggestionResponse:
    """Convert an UpdateSuggestion ORM instance to SuggestionResponse."""
    content_str = ""
    if s.content_json:
        if isinstance(s.content_json, str):
            content_str = s.content_json
        elif isinstance(s.content_json, dict):
            content_str = s.content_json.get("text", json.dumps(s.content_json, ensure_ascii=False))
        else:
            content_str = json.dumps(s.content_json, ensure_ascii=False)

    impact_score = 0.0
    if s.impact_score_json:
        if isinstance(s.impact_score_json, (int, float)):
            impact_score = float(s.impact_score_json)
        elif isinstance(s.impact_score_json, dict):
            impact_score = float(s.impact_score_json.get("score", 0.0))

    apply_result = None
    if s.apply_result_json:
        apply_result = s.apply_result_json

    return SuggestionResponse(
        id=s.id,
        suggestion_type=s.suggestion_type,
        target_role_id=s.target_role_id,
        resume_id=s.resume_id,
        source_achievement_id=s.source_achievement_id,
        title=s.title,
        content=content_str,
        impact_score=impact_score,
        risk_level=s.risk_level,
        status=s.status,
        applied_resume_version_id=s.applied_resume_version_id,
        apply_result=apply_result,
        created_at=s.created_at,
    )
```

The change is adding `source_achievement_id=s.source_achievement_id,` in the return statement.

---

### Task 5: Backend — Fix accept-suggestion pipeline to recalculate scores

**Files:**
- Modify: `backend/src/services/suggestion_service.py:87-194`

- [ ] **Step 1: Import score calculation and role lookup in accept_suggestion**

In `backend/src/services/suggestion_service.py`, add imports at the top of the `accept_suggestion` function (or at module level). The model imports are already inline, so add these inside the `if suggestion.suggestion_type in ("resume_update", "jd_tune") and suggestion.resume_id:` block, right after `from src.services.resume_diff_service import summarize_resume_diff`:

After creating the new version and flushing (after line 169 `await session.refresh(new_version)`), add score recalculation:

```python
            # Recalculate scores
            from src.services.resume_service import _calc_completeness, _calc_match_score

            completeness = _calc_completeness(new_content)

            # Look up role's required_skills for match score
            match_score = 0.0
            if suggestion.target_role_id:
                role_stmt = select(TargetRole).where(TargetRole.id == suggestion.target_role_id)
                role_result = await session.execute(role_stmt)
                role = role_result.scalar_one_or_none()
                if role and role.required_skills_json:
                    role_skills = role.required_skills_json if isinstance(role.required_skills_json, list) else []
                    match_score = _calc_match_score(new_content, role_skills)

            new_version.completeness_score = completeness
            new_version.match_score = match_score

            # Update parent Resume record scores
            resume.completeness_score = completeness
            resume.match_score = match_score
```

Add the import for TargetRole at the top of the function block (near line 119):

```python
        from src.models.resume import Resume, ResumeVersion
        from src.models.target_role import TargetRole
        from src.services.resume_diff_service import summarize_resume_diff
```

The full section after `if resume:` should look like:

```python
        if resume:
            # Get current version content
            ver_stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == resume.id)
                .order_by(ResumeVersion.version_no.desc())
                .limit(1)
            )
            ver_result = await session.execute(ver_stmt)
            current_version = ver_result.scalar_one_or_none()

            previous_content = current_version.content_json if current_version and current_version.content_json else {}
            if not isinstance(previous_content, dict):
                previous_content = {}

            # Apply the suggestion content on top of previous content
            suggested_content = suggestion.content_json or {}
            if isinstance(suggested_content, dict):
                # Merge: suggested content overrides matching keys
                new_content = {**previous_content, **suggested_content}
            else:
                new_content = previous_content

            # Calculate diff
            diff = summarize_resume_diff(previous_content, new_content)

            next_version_no = (current_version.version_no + 1) if current_version else 1
            new_version = ResumeVersion(
                resume_id=resume.id,
                version_no=next_version_no,
                content_json=new_content,
                generated_by="agent",
                source_type="suggestion_apply",
                source_ref_id=suggestion.id,
                summary_note=suggestion.title,
                completeness_score=0.0,  # placeholder, recalculated below
                match_score=0.0,          # placeholder, recalculated below
            )
            session.add(new_version)
            await session.flush()
            await session.refresh(new_version)

            # Recalculate scores
            from src.services.resume_service import _calc_completeness, _calc_match_score

            completeness = _calc_completeness(new_content)

            match_score = 0.0
            if suggestion.target_role_id:
                role_stmt = select(TargetRole).where(TargetRole.id == suggestion.target_role_id)
                role_result = await session.execute(role_stmt)
                role = role_result.scalar_one_or_none()
                if role and role.required_skills_json:
                    role_skills = role.required_skills_json if isinstance(role.required_skills_json, list) else []
                    match_score = _calc_match_score(new_content, role_skills)

            new_version.completeness_score = completeness
            new_version.match_score = match_score

            # Update parent Resume record scores
            resume.completeness_score = completeness
            resume.match_score = match_score

            # Update resume's current version
            resume.current_version_no = next_version_no
            resume.updated_at = datetime.now(UTC)

            applied_version_id = new_version.id
            apply_result = {"diff": diff, "new_version_no": next_version_no}

            suggestion.status = "applied"
            suggestion.applied_resume_version_id = applied_version_id
            suggestion.apply_result_json = apply_result
```

Note: the `from src.models.target_role import TargetRole` import should also be added alongside the other inline imports at the top of the `if suggestion.suggestion_type in ...` block.

---

### Task 6: Frontend — Update TypeScript types for suggestion

**Files:**
- Modify: `frontend/src/types/index.ts:226-240`

- [ ] **Step 1: Add `source_achievement_id` to UpdateSuggestion interface**

In `frontend/src/types/index.ts`, update the `UpdateSuggestion` interface:

```typescript
export interface UpdateSuggestion {
  id: string;
  suggestion_type: "resume_update" | "gap_update" | "jd_tune";
  target_role_id: string;
  resume_id?: string;
  source_achievement_id?: string;
  title: string;
  content: Record<string, unknown>;
  impact_score: number;
  risk_level: "low" | "medium" | "high";
  status: "pending" | "accepted" | "rejected" | "applied";
  applied_resume_version_id?: string;
  apply_result?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
```

The changes: added `source_achievement_id?: string;` and changed `impact_score` from `Record<string, unknown>` to `number` (the backend returns a float, not a dict — this was a type mismatch).

---

### Task 7: Frontend — Fix useAcceptSuggestion and useRejectSuggestion cache invalidation

**Files:**
- Modify: `frontend/src/hooks/useSuggestions.ts:15-39`

- [ ] **Step 1: Expand cache invalidation in useAcceptSuggestion**

In `frontend/src/hooks/useSuggestions.ts`, update `useAcceptSuggestion`:

```typescript
export function useAcceptSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await suggestionApi.accept(id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      queryClient.invalidateQueries({ queryKey: ["gaps"] });
      queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
  });
}
```

- [ ] **Step 2: Expand cache invalidation in useRejectSuggestion**

Update `useRejectSuggestion` to also invalidate suggestions broadly:

```typescript
export function useRejectSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await suggestionApi.reject(id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suggestions"] });
    },
  });
}
```

(Reject doesn't change scores, so no need to invalidate resumes/gaps/roles.)

---

### Task 8: Frontend — Add useSuggestionsForAchievement hook

**Files:**
- Modify: `frontend/src/hooks/useAchievements.ts`

- [ ] **Step 1: Add hook to fetch suggestions for a specific achievement**

In `frontend/src/hooks/useAchievements.ts`, add:

```typescript
export function useSuggestionsForAchievement(achievementId: string | null) {
  return useQuery<UpdateSuggestion[]>({
    queryKey: ["suggestions", { achievement_id: achievementId }],
    queryFn: async () => {
      const { data } = await suggestionApi.list({ achievement_id: achievementId! });
      return data;
    },
    enabled: !!achievementId,
  });
}
```

Also add the import for `UpdateSuggestion` at the top:

```typescript
import type { Achievement, AchievementCreateRequest, UpdateSuggestion } from "@/types";
```

And add `useQuery` to the `@tanstack/react-query` import (it's already there via `useQuery`).

---

### Task 9: Frontend — Replace tag filter with sticky tab bar

**Files:**
- Modify: `frontend/src/pages/Achievements.tsx`

- [ ] **Step 1: Add imports and tab state**

At the top of `Achievements.tsx`, update imports:

```typescript
import { useState, useMemo, type FormEvent } from "react";
import { Header } from "@/components/layout/Header";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  useAchievements,
  useCreateAchievement,
  useAnalyzeAchievement,
} from "@/hooks/useAchievements";
import { useSuggestions } from "@/hooks/useSuggestions";
import {
  Plus,
  Tag,
  Sparkles,
  Eye,
  Loader2,
  AlertTriangle,
  FileText,
  X,
  CheckCircle2,
  Clock,
  CircleDot,
  Layers,
} from "lucide-react";
import type { Achievement, AchievementCreateRequest } from "@/types";
```

- [ ] **Step 2: Replace the toolbar and tag filter with sticky tab bar**

Replace the entire `Achievements` component body. The key changes are:
1. Replace `filterTag` state with `activeTab` state
2. Fetch pending suggestions to build "待处理" set
3. Replace tag filter chips with tab bar
4. Make the toolbar sticky

Replace the full `Achievements` function:

```typescript
export function Achievements() {
  const { data, isLoading, isError } = useAchievements();
  const createAchievement = useCreateAchievement();
  const analyzeAchievement = useAnalyzeAchievement();

  // Fetch pending suggestions to determine which achievements have pending suggestions
  const { data: pendingSuggestions } = useSuggestions({ status: "pending" });

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | "unanalyzed" | "pending" | "done">("all");

  const achievements = data ?? [];
  const selectedAchievement = selectedId
    ? achievements.find((a) => a.id === selectedId) ?? null
    : null;

  // Build a Set of achievement IDs that have pending suggestions
  const pendingAchievementIds = useMemo(() => {
    const ids = new Set<string>();
    if (pendingSuggestions) {
      for (const s of pendingSuggestions) {
        if (s.source_achievement_id) {
          ids.add(s.source_achievement_id);
        }
      }
    }
    return ids;
  }, [pendingSuggestions]);

  // Tab counts
  const tabCounts = useMemo(() => {
    const unanalyzed = achievements.filter((a) => !a.parsed_summary).length;
    const pending = achievements.filter(
      (a) => a.parsed_summary && pendingAchievementIds.has(a.id)
    ).length;
    const done = achievements.filter(
      (a) => a.parsed_summary && !pendingAchievementIds.has(a.id)
    ).length;
    return { all: achievements.length, unanalyzed, pending, done };
  }, [achievements, pendingAchievementIds]);

  // Filter achievements by active tab
  const filteredAchievements = useMemo(() => {
    switch (activeTab) {
      case "unanalyzed":
        return achievements.filter((a) => !a.parsed_summary);
      case "pending":
        return achievements.filter(
          (a) => a.parsed_summary && pendingAchievementIds.has(a.id)
        );
      case "done":
        return achievements.filter(
          (a) => a.parsed_summary && !pendingAchievementIds.has(a.id)
        );
      default:
        return achievements;
    }
  }, [achievements, activeTab, pendingAchievementIds]);

  const tabs = [
    { key: "all" as const, label: "全部", icon: Layers },
    { key: "unanalyzed" as const, label: "未分析", icon: CircleDot },
    { key: "pending" as const, label: "待处理", icon: Clock },
    { key: "done" as const, label: "已完成", icon: CheckCircle2 },
  ];

  return (
    <>
      <Header title="成果中心" description="管理所有沉淀下来的成果资产" />
      {/* Sticky toolbar */}
      <div className="sticky top-0 z-10 bg-card border-b">
        <PageContainer>
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                  <span className={`ml-0.5 rounded-full px-1.5 py-0.5 text-xs ${
                    activeTab === tab.key
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}>
                    {tabCounts[tab.key]}
                  </span>
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              新增成果
            </button>
          </div>
        </PageContainer>
      </div>
      <PageContainer>
        {/* Content */}
        <div className="mt-4">
          {isLoading && (
            <div className="flex items-center justify-center rounded-lg border bg-card p-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">加载中...</span>
            </div>
          )}

          {isError && (
            <div className="flex items-center justify-center rounded-lg border border-red-200 bg-red-50 p-12">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="ml-2 text-red-600">加载失败，请稍后重试</span>
            </div>
          )}

          {!isLoading && !isError && filteredAchievements.length === 0 && (
            <div className="rounded-lg border bg-card p-8 text-center">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">
                {activeTab !== "all"
                  ? `没有${tabs.find((t) => t.key === activeTab)?.label ?? ""}的成果`
                  : "暂无成果记录"}
              </p>
              {activeTab === "all" && (
                <p className="mt-1 text-sm text-muted-foreground">
                  点击「新增成果」开始录入你的工作成果。
                </p>
              )}
            </div>
          )}

          {!isLoading && !isError && filteredAchievements.length > 0 && (
            <div className="space-y-4">
              {filteredAchievements.map((achievement) => (
                <AchievementCard
                  key={achievement.id}
                  achievement={achievement}
                  onAnalyze={() =>
                    analyzeAchievement.mutate(achievement.id)
                  }
                  isAnalyzing={
                    analyzeAchievement.isPending &&
                    analyzeAchievement.variables === achievement.id
                  }
                  onViewDetail={() => setSelectedId(achievement.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <CreateAchievementModal
            onClose={() => setShowCreateModal(false)}
            onSubmit={(data) => {
              createAchievement.mutate(data, {
                onSuccess: () => {
                  setShowCreateModal(false);
                },
              });
            }}
            isSubmitting={createAchievement.isPending}
          />
        )}

        {/* Detail Drawer */}
        {selectedAchievement && (
          <DetailDrawer
            achievement={selectedAchievement}
            onClose={() => setSelectedId(null)}
            onAnalyze={() =>
              analyzeAchievement.mutate(selectedAchievement.id)
            }
            isAnalyzing={
              analyzeAchievement.isPending &&
              analyzeAchievement.variables === selectedAchievement.id
            }
          />
        )}
      </PageContainer>
    </>
  );
}
```

---

### Task 10: Frontend — Add suggestion cards to DetailDrawer

**Files:**
- Modify: `frontend/src/pages/Achievements.tsx` (DetailDrawer component)

- [ ] **Step 1: Update DetailDrawer to show suggestions**

Replace the entire `DetailDrawer` component:

```typescript
// ── DetailDrawer (slide-in panel) ──────────────────────

function DetailDrawer({
  achievement,
  onClose,
  onAnalyze,
  isAnalyzing,
}: {
  achievement: Achievement;
  onClose: () => void;
  onAnalyze: () => void;
  isAnalyzing: boolean;
}) {
  const hasParsed = !!achievement.parsed_summary;

  // Fetch suggestions for this achievement
  const { data: suggestions } = useSuggestions({
    achievement_id: achievement.id,
  });

  const acceptSuggestion = useAcceptSuggestion();
  const rejectSuggestion = useRejectSuggestion();

  const pendingCount = suggestions?.filter((s) => s.status === "pending").length ?? 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={onClose}
      />
      {/* Panel */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl overflow-y-auto bg-card shadow-xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-card px-6 py-4">
          <h3 className="text-lg font-semibold truncate pr-4">
            {achievement.title}
          </h3>
          <button
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors shrink-0"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Meta */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {new Date(achievement.created_at).toLocaleDateString("zh-CN")}
            </span>
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {SOURCE_TYPE_LABELS[achievement.source_type] ?? achievement.source_type}
            </span>
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
              重要度 {achievement.importance_score}
            </span>
            {achievement.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
              >
                <Tag className="mr-1 h-3 w-3" />
                {tag}
              </span>
            ))}
          </div>

          {/* Raw Content */}
          <section>
            <h4 className="text-sm font-semibold text-foreground">原始内容</h4>
            <p className="mt-2 whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm text-foreground">
              {achievement.raw_content}
            </p>
          </section>

          {/* Parsed sections (only if analyzed) */}
          {hasParsed && (
            <>
              {/* Summary */}
              <section>
                <h4 className="text-sm font-semibold text-foreground">解析摘要</h4>
                <p className="mt-2 text-sm text-muted-foreground">
                  {achievement.parsed_summary}
                </p>
              </section>

              {/* Technical Points */}
              {achievement.technical_points && achievement.technical_points.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">技术要点</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.technical_points.map((point, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground"
                      >
                        {String(point.description ?? point.content ?? JSON.stringify(point))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Challenges */}
              {achievement.challenges && achievement.challenges.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">挑战</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.challenges.map((c, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-orange-50 px-3 py-2 text-sm text-orange-800"
                      >
                        {String(c.description ?? c.content ?? JSON.stringify(c))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Solutions */}
              {achievement.solutions && achievement.solutions.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">解决方案</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.solutions.map((s, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-green-50 px-3 py-2 text-sm text-green-800"
                      >
                        {String(s.description ?? s.content ?? JSON.stringify(s))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Metrics */}
              {achievement.metrics && achievement.metrics.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">量化指标</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.metrics.map((m, i) => (
                      <li
                        key={i}
                        className="rounded-md border bg-blue-50 px-3 py-2 text-sm text-blue-800"
                      >
                        {String(m.description ?? m.content ?? JSON.stringify(m))}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Interview Points */}
              {achievement.interview_points && achievement.interview_points.length > 0 && (
                <section>
                  <h4 className="text-sm font-semibold text-foreground">面试要点</h4>
                  <ul className="mt-2 space-y-1.5">
                    {achievement.interview_points.map((point, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 rounded-md border bg-purple-50 px-3 py-2 text-sm text-purple-800"
                      >
                        <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Update Suggestions */}
              {suggestions && suggestions.length > 0 && (
                <section>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    更新建议
                    <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      {suggestions.length}
                      {pendingCount > 0 && ` (${pendingCount} 待处理)`}
                    </span>
                  </h4>
                  <div className="mt-3 space-y-2">
                    {suggestions.map((sug) => (
                      <SuggestionCard
                        key={sug.id}
                        suggestion={sug}
                        onAccept={(id) => acceptSuggestion.mutate(id)}
                        onReject={(id) => rejectSuggestion.mutate(id)}
                        isAccepting={acceptSuggestion.isPending && acceptSuggestion.variables === sug.id}
                        isRejecting={rejectSuggestion.isPending && rejectSuggestion.variables === sug.id}
                      />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}

          {/* Un-analyzed prompt */}
          {!hasParsed && (
            <section className="rounded-lg border border-dashed p-6 text-center">
              <FileText className="mx-auto h-10 w-10 text-muted-foreground/40" />
              <p className="mt-3 text-sm text-muted-foreground">
                该成果尚未分析
              </p>
              <button
                onClick={onAnalyze}
                disabled={isAnalyzing}
                className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {isAnalyzing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                开始分析
              </button>
            </section>
          )}
        </div>
      </div>
    </>
  );
}
```

Also add the required imports at the top of the file. Add to the existing imports:

```typescript
import { useSuggestions } from "@/hooks/useSuggestions";
import { useAcceptSuggestion, useRejectSuggestion } from "@/hooks/useSuggestions";
```

Combine them:

```typescript
import { useSuggestions, useAcceptSuggestion, useRejectSuggestion } from "@/hooks/useSuggestions";
```

- [ ] **Step 2: Add SuggestionCard component**

Add this component after the `DetailDrawer` component in the same file:

```typescript
// ── SuggestionCard ─────────────────────────────────────

const SUGGESTION_TYPE_LABELS: Record<string, string> = {
  resume_update: "简历更新",
  gap_update: "Gap 更新",
  jd_tune: "JD 调整",
};

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

const SUGGESTION_STATUS_STYLES: Record<string, { label: string; color: string }> = {
  pending: { label: "待处理", color: "bg-yellow-100 text-yellow-700" },
  accepted: { label: "已采纳", color: "bg-green-100 text-green-700" },
  applied: { label: "已应用", color: "bg-green-100 text-green-700" },
  rejected: { label: "已拒绝", color: "bg-gray-100 text-gray-500" },
};

function SuggestionCard({
  suggestion,
  onAccept,
  onReject,
  isAccepting,
  isRejecting,
}: {
  suggestion: UpdateSuggestion;
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
  isAccepting: boolean;
  isRejecting: boolean;
}) {
  const statusInfo = SUGGESTION_STATUS_STYLES[suggestion.status] ?? {
    label: suggestion.status,
    color: "bg-gray-100 text-gray-500",
  };
  const isPending = suggestion.status === "pending";

  return (
    <div className="rounded-md border p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground truncate">
              {suggestion.title}
            </span>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700">
              {SUGGESTION_TYPE_LABELS[suggestion.suggestion_type] ?? suggestion.suggestion_type}
            </span>
            <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${RISK_COLORS[suggestion.risk_level] ?? RISK_COLORS.low}`}>
              {suggestion.risk_level === "low" ? "低风险" : suggestion.risk_level === "medium" ? "中风险" : "高风险"}
            </span>
            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-muted text-muted-foreground">
              影响度 {suggestion.impact_score.toFixed(1)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {isPending ? (
            <>
              <button
                onClick={() => onReject(suggestion.id)}
                disabled={isRejecting}
                className="rounded-md border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted disabled:opacity-50 transition-colors"
              >
                {isRejecting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "拒绝"}
              </button>
              <button
                onClick={() => onAccept(suggestion.id)}
                disabled={isAccepting}
                className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {isAccepting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "采纳"}
              </button>
            </>
          ) : (
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusInfo.color}`}>
              {statusInfo.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
```

Make sure to add `UpdateSuggestion` to the type import at the top of the file:

```typescript
import type { Achievement, AchievementCreateRequest, UpdateSuggestion } from "@/types";
```

---

## Verification Checklist

1. **Migration runs**: `cd backend && alembic upgrade head` — no errors
2. **Backend starts**: `uvicorn src.main:app --reload` — no import errors
3. **Tab filtering**: Open achievements → each tab filters correctly → counts accurate
4. **Sticky toolbar**: Scroll down → tab bar + button stay visible at top
5. **Detail drawer suggestions**: Analyze an achievement → open detail → see suggestion cards with accept/reject
6. **Accept from drawer**: Click "采纳" → suggestion status updates → resume gets new version → match/completeness scores update
7. **Score recalculation**: Before accept match=40%, after accept match should be > 40% (actual numbers vary)
8. **Tab "待处理" count**: After accepting all suggestions from an achievement, it moves from "待处理" to "已完成"
9. **Standalone suggestions page**: Still works, shows all suggestions globally
