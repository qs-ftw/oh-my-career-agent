# CareerPortfolio 3-Level Drill-Down Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the flat single-page CareerPortfolio with a 3-level drill-down navigation (overview → company detail → project detail), with full CRUD at every level and orphaned achievement assignment.

**Architecture:** URL-driven routing with breadcrumb navigation. Three route levels under `/portfolio`. Backend adds achievement PATCH endpoint. Frontend reuses existing data hooks plus new `useUpdateAchievement`.

**Tech Stack:** React Router, TanStack React Query, existing REST API, Tailwind CSS

---

## Navigation Structure

```
总览页 /portfolio
  → 公司详情页 /portfolio/:weId
    → 项目详情页 /portfolio/:weId/:projectId
```

All pages use URL params for navigation. Browser back/forward works naturally.

---

## Page 1: Overview (`/portfolio`)

**Sticky toolbar:**
- Stats: X家公司 / X个项目 / X个成果
- Button: 新增项目（独立项目）
- Button: 新增工作经历

**Company cards (compact, expandable):**
- Collapsed: company name (clickable → company detail), role title, date range, location, project count
- Edit/Delete buttons on each card
- Expanded: list of project names with tech stack badges (one line each)
- Click company name → navigate to `/portfolio/:weId`

**Standalone projects section:**
- Projects without a work_experience_id shown in a separate section
- Each shows name + tech stack + edit/delete

**Orphaned achievements section (bottom):**
- Title: "未归档成果"
- Each achievement shows: title, importance score badge, status badge
- Each has a "归档到项目" button
- Clicking button opens a dropdown/selector grouped by company → project
- Selecting a project calls `PATCH /achievements/:id` with `{ project_id, work_experience_id }`
- On success, achievement moves out of orphaned list

**CRUD:**
- Create/Edit work experience: modal (reuse existing `WorkExperienceModal`)
- Create project: modal (reuse existing `ProjectModal`)
- Delete: confirmation dialog

---

## Page 2: Company Detail (`/portfolio/:weId`)

**Breadcrumb:** `职业履历 › 字节跳动`

**Company info card:**
- Company name, role title, date range, location, description
- Edit button → opens WorkExperienceModal
- Delete button → confirmation dialog (warns about linked projects/achievements)

**Project list:**
- Each project is a card showing: name, description (2-line clamp), tech stack badges, achievement count, date range
- Click project name → navigate to `/portfolio/:weId/:projectId`
- Edit/Delete buttons on each card
- "新增项目" button at bottom (pre-selects current company)

**WE-level achievements:**
- Achievements with `work_experience_id` matching this WE but no `project_id`
- Shown below projects section
- Can be assigned to a project via "归档到项目" selector

---

## Page 3: Project Detail (`/portfolio/:weId/:projectId`)

**Breadcrumb:** `职业履历 › 字节跳动 › 用户增长平台`

**Project info section:**
- Name, description (full), tech stack badges, date range, URL link
- Edit button → opens ProjectModal
- Delete button → confirmation dialog

**Achievement list (compact rows, inline expand):**
- Collapsed row: title + importance score badge + status badge (已分析/未分析) + expand chevron
- Expanded: summary paragraph, tags, raw content, parsed data highlights
- Expanded actions: edit achievement content, trigger analysis, remove from project
- "Remove from project" calls `PATCH /achievements/:id` with `{ project_id: null }`
- "新增成果" button at bottom

**Achievement editing:**
- Inline edit of title and raw_content when expanded
- Save calls `PATCH /achievements/:id`

---

## Backend Changes

### New endpoint: `PATCH /achievements/:id`

**Purpose:** Update achievement fields including project assignment.

**Request body:**
```json
{
  "title": "string (optional)",
  "raw_content": "string (optional)",
  "project_id": "uuid | null (optional)",
  "work_experience_id": "uuid | null (optional)",
  "tags": ["string (optional)"]
}
```

**Behavior:**
- Only fields present in the body are updated
- Setting `project_id` to null removes the achievement from the project (becomes orphaned or stays at WE level)
- When `project_id` is set, automatically derive `work_experience_id` from the project's parent WE
- Validate that the achievement belongs to the current user (JOIN through CareerProfile)
- Return updated achievement response

**Files to modify:**
- `backend/src/api/achievements.py` — add PATCH endpoint
- `backend/src/services/achievement_service.py` — add `update_achievement()` function
- `backend/src/schemas/achievement.py` — add `AchievementUpdate` schema

---

## Frontend Changes

### New files:
- `frontend/src/pages/CareerPortfolio/Overview.tsx` — total overview page
- `frontend/src/pages/CareerPortfolio/CompanyDetail.tsx` — company detail page
- `frontend/src/pages/CareerPortfolio/ProjectDetail.tsx` — project detail page

### Modified files:
- `frontend/src/App.tsx` — update route from single component to nested routes
- `frontend/src/pages/CareerPortfolio.tsx` — becomes a layout wrapper with `<Outlet />`
- `frontend/src/hooks/useAchievements.ts` — add `useUpdateAchievement` hook
- `frontend/src/lib/api.ts` — add `achievementApi.update()` method

### Reused components:
- `WorkExperienceModal` — moved to shared components or kept inline
- `ProjectModal` — moved to shared components or kept inline
- `AchievementInline` — rewritten as expandable row component

### New components:
- `AchievementAssignSelector` — dropdown to assign achievement to a project
- `AchievementExpandable` — inline expandable achievement row

---

## Data Flow

1. All three pages share the same data hooks: `useWorkExperiences()`, `useProjects()`, `useAchievements()`
2. React Query cache is shared — mutations on one page automatically reflect on others
3. Assignment mutations invalidate relevant query keys to refresh lists
4. Breadcrumb navigation uses React Router's `useNavigate()` and URL params

---

## Edge Cases

- **No profile yet:** Show empty state with prompt to create profile or import resume
- **Empty company (no projects):** Show company card with "暂无项目" and "新增项目" button
- **Empty project (no achievements):** Show "暂无成果" with "新增成果" button
- **Orphaned achievement assignment:** When assigning to a project under WE_X, auto-set `work_experience_id` to WE_X
- **Deleting a company with projects:** Warn user, cascade deletes handled by DB (ON DELETE CASCADE on profile_id)
- **Project with null WE:** Show in "独立项目" section on overview page; project detail breadcrumb shows `职业履历 › 独立项目 › 项目名`
