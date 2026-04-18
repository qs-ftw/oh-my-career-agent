# Role Management Enhancement Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge JD customization into role management, add 3 creation modes (manual / JD paste / quick name), enhance JD parsing with description expansion, and allow resume name editing.

**Architecture:** Backend adds two preview-only endpoints (`/roles/analyze-jd`, `/roles/analyze-name`) that return pre-filled `RoleCreate` fields without creating anything. Frontend presents these as dialogs in the Roles page. Creation still uses existing `POST /roles`. JD Tailor standalone page is removed.

**Tech Stack:** FastAPI, SQLAlchemy, LangGraph, React 19, TanStack Query, TypeScript

---

## 1. Three Role Creation Modes

### Current State
- Single "新增岗位" button opens a modal with full form (name, type, description, skills, keywords, priority, source_jd)
- All fields must be manually filled

### New State
The "新增岗位" button becomes a dropdown with 3 options:

#### Mode 1: Manual Create (unchanged)
- Opens existing form modal
- User fills all fields manually
- Submit → `POST /roles` → create role + initialize assets

#### Mode 2: JD Paste Create
- Opens a new dialog with:
  - Left: textarea for pasting raw JD text
  - Right: preview panel showing parsed results (role_name, description, skills, keywords) — all editable
  - "解析" button triggers `POST /roles/analyze-jd`
  - Bottom: two action buttons:
    - "创建岗位" — submits preview data to `POST /roles` (only creates role)
    - "创建岗位并生成简历" — submits to `POST /roles` with flag to also run `initialize_role_assets`

#### Mode 3: Quick Name Create
- Opens a smaller dialog with:
  - Input field for role name only
  - "分析" button triggers `POST /roles/analyze-name`
  - After analysis: shows editable preview of description, skills, keywords
  - Bottom: same two action buttons as Mode 2

### API Design

**New endpoints (preview only, no side effects):**

```
POST /roles/analyze-jd
  Request:  { raw_jd: string }
  Response: {
    role_name: string,
    role_type: string,        // default "全职"
    description: string,      // expanded, concrete description
    keywords: string[],
    required_skills: string[],
    bonus_skills: string[]
  }

POST /roles/analyze-name
  Request:  { role_name: string }
  Response: {
    role_name: string,
    role_type: string,
    description: string,      // LLM-generated typical JD for this role
    keywords: string[],
    required_skills: string[],
    bonus_skills: string[]
  }
```

Both endpoints return data that the frontend can edit and then submit to existing `POST /roles`.

**Existing endpoint modified:**
- `POST /roles` — currently always runs `initialize_role_assets` after creation. Add optional `skip_init: bool = False` field to `RoleCreate`. When `skip_init=True`, only creates the role record without generating resume/gaps. Frontend sends `skip_init=True` for "创建岗位" button, `skip_init=False` (default) for "创建岗位并生成简历".

---

## 2. Enhanced JD Parsing

### Current JD Parsing Output
```
{ role_name, keywords, required_skills, bonus_items, style }
```

### Enhanced Output
The `jd_parsing` agent node is enhanced to also produce:

- **`description`**: LLM expands abstract JD requirements into concrete, well-structured description text (200-500 chars). Examples:
  - "熟悉前端框架" → "精通 React/Vue 至少一种，包含状态管理（Redux/Pinia）、组件设计模式、性能优化"
  - "有大数据经验" → "具备 Hadoop/Spark/Flink 等大数据处理框架的实际项目经验，能独立完成数据管道设计与调优"
- **`required_skills` expansion**: Each skill is concrete, not abstract. Instead of "前端开发", return ["React", "TypeScript", "CSS-in-JS"]

### Backend Changes

New file: `backend/src/services/role_analyze_service.py`
- `analyze_jd(session, user_id, workspace_id, raw_jd)` — calls jd_parsing node, returns preview dict
- `analyze_name(session, user_id, workspace_id, role_name)` — calls LLM with prompt to generate typical JD for the role name, returns preview dict

New file: `backend/src/api/role_analyze.py`
- Two POST endpoints wiring to the service above

Update: `backend/src/agent/nodes/jd_parsing.py`
- Add `description` to the output schema
- Update prompt to instruct LLM to generate expanded, concrete description

---

## 3. Match Score Display

### Current State
- Role detail page shows resume card with `match_score` and `completeness_score` as numbers
- JDTailor produces detailed match analysis (ability_match, resume_match, readiness scores)

### New State
- No new backend fields needed — match scores are already stored on `Resume.match_score` and `Resume.completeness_score`
- When user chooses "创建岗位并生成简历", the existing `initialize_role_assets` pipeline runs, producing the resume with match scores
- Frontend: enhance the resume card in `RoleDetail.tsx` to show match scores more prominently (e.g., colored progress bars or percentage badges)

---

## 4. Resume Name Editing

### Current State
- `ResumeDetail.tsx` displays `resume.resume_name` as static text in the header
- Backend `ResumeUpdate.resume_name` field exists and works
- `useUpdateResume` hook supports `resume_name` parameter

### New State
- Replace static header title with editable component:
  - Default: shows title as text with a small pencil icon
  - Click pencil → title becomes an input field
  - Enter/blur → saves via `useUpdateResume({ id, data: { resume_name } })`
  - Escape → cancels edit
- Same pattern used for editing other inline fields in the app

---

## 5. Remove JDTailor Standalone Page

### Files to Delete
- `frontend/src/pages/JDTailor.tsx`

### Files to Modify
- `frontend/src/App.tsx` — remove `/jd-tailor` route
- `frontend/src/components/layout/Sidebar.tsx` — remove "JD 定制" nav item (FileSearch icon)

### Files NOT Changed
- Backend JD endpoints (`/jd/parse`, `/jd/tailor`, `/jd/tasks/{task_id}`) remain — they are used internally by the new analyze-jd flow
- `frontend/src/hooks/useJD.ts` — keep for potential internal use, or remove if unused after refactor
- JD-related agent nodes and graphs remain unchanged

---

## Files Summary

### New Files
| File | Purpose |
|------|---------|
| `backend/src/api/role_analyze.py` | API endpoints for JD/name analysis preview |
| `backend/src/services/role_analyze_service.py` | Service layer for analysis logic |
| `frontend/src/components/CreateRoleFromJD.tsx` | JD paste creation dialog component |
| `frontend/src/components/CreateRoleQuick.tsx` | Quick name creation dialog component |

### Modified Files
| File | Change |
|------|--------|
| `backend/src/agent/nodes/jd_parsing.py` | Add `description` output field, enhance prompt |
| `backend/src/schemas/role.py` | Add `skip_init: bool = False` to `RoleCreate` |
| `backend/src/api/roles.py` | Conditionally skip `initialize_role_assets` when `skip_init=True` |
| `frontend/src/pages/Roles.tsx` | "新增岗位" button → dropdown with 3 options |
| `frontend/src/pages/RoleDetail.tsx` | Enhanced match score display on resume card |
| `frontend/src/pages/ResumeDetail.tsx` | Editable resume name in header |
| `frontend/src/App.tsx` | Remove JDTailor route |
| `frontend/src/components/layout/Sidebar.tsx` | Remove JD 定制 nav item |
| `frontend/src/lib/api.ts` | Add `roleApi.analyzeJd()`, `roleApi.analyzeName()` |
| `frontend/src/types/index.ts` | Add analysis request/response types |
| `frontend/src/hooks/useRoles.ts` | Add `useAnalyzeJd`, `useAnalyzeName` hooks |

### Deleted Files
| File | Reason |
|------|--------|
| `frontend/src/pages/JDTailor.tsx` | Functionality merged into role management |

---

## Verification Checklist

1. **Manual create**: Open role management → click dropdown → manual create → fill form → submit → role created with assets
2. **JD paste create**: Click dropdown → JD paste → paste JD text → click 解析 → preview shows role_name, description, skills → edit if needed → click "创建岗位并生成简历" → role + resume + gaps created
3. **JD paste create (no resume)**: Same but click "创建岗位" → only role created, no resume
4. **Quick name create**: Click dropdown → quick create → type "高级前端工程师" → click 分析 → preview auto-filled → submit
5. **Match scores visible**: Create role with resume → open role detail → resume card shows match_score prominently
6. **Resume name edit**: Open resume detail → click pencil icon next to name → type new name → save → name updated
7. **JDTailor removed**: Sidebar no longer shows "JD 定制", navigating to `/jd-tailor` shows 404 or redirect
8. **Existing roles unaffected**: Existing roles, resumes, gaps still display correctly
