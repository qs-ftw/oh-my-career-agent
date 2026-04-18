# Career-Ops Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen `CareerAgent` as a long-term career asset system by selectively reusing the best ideas from `career-ops`: candidate profile context, reusable interview stories, richer JD evaluation, suggestion-to-version apply flow, ATS-friendly PDF export, and real dashboard visibility.

**Architecture:** Keep the current Postgres + FastAPI + LangGraph + React modular monolith. Reuse `career-ops` only at the prompt contract, artifact design, and export-template level; do not copy its local-file storage model, tracker TSV flow, portal scanning, or auto-apply behavior. New capabilities must be stored as structured DB entities and exposed through the existing API and Web UI.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, Alembic, LangGraph, React 19, TypeScript, Vitest, Playwright for backend PDF rendering.

---

## Required Context

### Product Direction To Preserve

- `CareerAgent` is a **long-term career asset management system**, not a one-shot resume writer or spray-and-pray application tool.
- The PRD explicitly centers on:
  - multi-role long-term management
  - achievement accumulation
  - structured gap analysis
  - JD-specific tailoring
  - versioned and explainable updates
- The PRD explicitly excludes:
  - auto-apply
  - bulk apply
  - deep recruitment portal automation

### Current Local Baseline

Read these files before touching code:

- `prd.md`
- `backend/src/agent/graph.py`
- `backend/src/agent/state.py`
- `backend/src/services/role_service.py`
- `backend/src/services/achievement_service.py`
- `backend/src/services/jd_service.py`
- `backend/src/services/suggestion_service.py`
- `backend/src/services/resume_service.py`
- `backend/src/models/jd.py`
- `frontend/src/pages/JDTailor.tsx`
- `frontend/src/pages/ResumeDetail.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Suggestions.tsx`

### Current Gaps In This Repo

- `JD` flow is implemented, but its prompt contract is too thin and returns only resume + scores.
- `Suggestion` accept/reject only flips status; it does not create a new resume version.
- `Dashboard` is still placeholder-only.
- There is no canonical candidate profile layer.
- There is no cross-JD reusable story bank.
- There is no ATS-grade PDF export path.

### What To Reuse From `career-ops`

Reuse these ideas:

- `config/profile.yml` -> canonical candidate profile / narrative / proof-point context
- `modes/oferta.md` -> structured JD review protocol, not just raw tailoring
- `modes/_shared.md` -> scoring framing and “be honest / no fabrication” output rules
- `interview-prep/story-bank.md` -> reusable STAR story bank
- `templates/cv-template.html` -> ATS-friendly export structure and visual direction
- `generate-pdf.mjs` -> ATS normalization concerns and PDF rendering constraints
- `DATA_CONTRACT.md` / `verify-pipeline.mjs` -> the idea of clear system-vs-user boundaries and verification, but implemented with DB records and service checks

Do **not** reuse these parts:

- file-based persistence (`cv.md`, `applications.md`, TSV merge flow)
- portal scanning
- slash-command UX
- auto-pipeline around external job boards
- Go TUI dashboard
- any feature that drifts toward automated application submission

## Recommended Agent Split

This plan is intentionally split into mostly independent workstreams.

- Agent A: Task 1 `Candidate Profile Foundation`
- Agent B: Task 2 `Story Bank`
- Agent C: Task 3 `JD Review Upgrade`
- Agent D: Task 4 `Suggestion Apply + Resume Diff`
- Agent E: Task 5 `PDF Export`
- Agent F: Task 6 `Dashboard + UI Surfaces`

Recommended merge order:

1. Task 1
2. Task 2 and Task 3 in parallel on top of Task 1
3. Task 4 after Task 3 API contracts are stable
4. Task 5 after Task 3 and Task 4 backend contracts are stable
5. Task 6 last

## File Structure Map

### New Backend Units

- `backend/src/models/profile.py`
- `backend/src/models/story.py`
- `backend/src/schemas/profile.py`
- `backend/src/schemas/story.py`
- `backend/src/services/profile_service.py`
- `backend/src/services/story_service.py`
- `backend/src/services/resume_diff_service.py`
- `backend/src/services/pdf_export_service.py`
- `backend/src/services/dashboard_service.py`
- `backend/src/api/profile.py`
- `backend/src/api/stories.py`
- `backend/src/api/dashboard.py`
- `backend/src/prompts/jd_review.py`
- `backend/src/prompts/story_extraction.py`
- `backend/src/agent/nodes/jd_review.py`
- `backend/src/agent/nodes/story_extraction.py`
- `backend/src/templates/resume_export.html`

### New Frontend Units

- `frontend/src/hooks/useProfile.ts`
- `frontend/src/hooks/useStories.ts`
- `frontend/src/hooks/useDashboard.ts`
- `frontend/src/pages/Profile.tsx`
- `frontend/src/pages/StoryBank.tsx`

### Expected Migration Files

- `backend/alembic/versions/20260413_01_add_candidate_profile.py`
- `backend/alembic/versions/20260413_02_add_interview_stories.py`
- `backend/alembic/versions/20260413_03_extend_jd_review_artifacts.py`
- `backend/alembic/versions/20260413_04_extend_update_suggestions_apply_result.py`
- `backend/alembic/versions/20260413_05_add_pdf_export_fields.py`

### Existing Files That Will Change

- `backend/src/models/__init__.py`
- `backend/src/models/jd.py`
- `backend/src/models/agent.py`
- `backend/src/agent/graph.py`
- `backend/src/agent/state.py`
- `backend/src/services/role_service.py`
- `backend/src/services/achievement_service.py`
- `backend/src/services/jd_service.py`
- `backend/src/services/suggestion_service.py`
- `backend/src/services/resume_service.py`
- `backend/src/api/router.py`
- `backend/src/api/jd.py`
- `backend/src/api/resumes.py`
- `backend/src/api/suggestions.py`
- `backend/src/schemas/jd.py`
- `backend/src/schemas/suggestion.py`
- `backend/src/schemas/resume.py`
- `backend/pyproject.toml`
- `frontend/src/types/index.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/pages/JDTailor.tsx`
- `frontend/src/pages/ResumeDetail.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Suggestions.tsx`

## Global Acceptance Criteria

- Candidate profile exists as a canonical structured source of truth for tailoring.
- Story bank accumulates reusable interview stories linked to achievements and/or JD tasks.
- JD flow returns a structured review artifact, not only a tailored resume.
- Accepting a resume-related suggestion creates a new `ResumeVersion` and stores version provenance.
- PDF export is available for at least:
  - master resume
  - JD-tailored resume result
- Dashboard shows real counts and recent activity.
- No new feature introduces file-based job tracker logic, portal scanning, or auto-apply.

---

### Task 1: Candidate Profile Foundation

**Owner:** Agent A

**Files:**
- Create: `backend/src/models/profile.py`
- Create: `backend/src/schemas/profile.py`
- Create: `backend/src/services/profile_service.py`
- Create: `backend/src/api/profile.py`
- Create: `backend/tests/test_services/test_profile_service.py`
- Create: `backend/tests/test_api/test_profile_api.py`
- Modify: `backend/src/models/__init__.py`
- Modify: `backend/src/api/router.py`
- Modify: `backend/src/agent/state.py`
- Modify: `backend/src/services/role_service.py`
- Modify: `backend/src/services/jd_service.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/useProfile.ts`
- Create: `frontend/src/pages/Profile.tsx`
- Modify: `frontend/src/App.tsx`
- Migration: `backend/alembic/versions/20260413_01_add_candidate_profile.py`

- [ ] Add a `CandidateProfile` ORM model keyed by `workspace_id` + `user_id` with JSONB fields for `superpowers`, `proof_points`, `target_roles`, `preferences`, and `constraints`.

```python
class CandidateProfile(CommonBase):
    __tablename__ = "candidate_profiles"

    workspace_id = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    headline = mapped_column(String(256), nullable=False, default="")
    exit_story = mapped_column(Text, nullable=False, default="")
    superpowers_json = mapped_column(JSONB, nullable=False, default=list)
    proof_points_json = mapped_column(JSONB, nullable=False, default=list)
    compensation_json = mapped_column(JSONB, nullable=False, default=dict)
    location_json = mapped_column(JSONB, nullable=False, default=dict)
    preferences_json = mapped_column(JSONB, nullable=False, default=dict)
    constraints_json = mapped_column(JSONB, nullable=False, default=dict)
```

- [ ] Add service-level tests for create, get, and update behavior before implementing the service. The tests must assert that proof points round-trip as structured JSON and that one user gets one canonical profile.

```python
async def test_upsert_profile_persists_structured_proof_points(db_session):
    payload = CandidateProfileUpsert(
        headline="Agent engineer focused on long-term automation",
        exit_story="Built multiple AI workflows and production services.",
        superpowers=["LangGraph orchestration", "Backend systems"],
        proof_points=[{"name": "CareerAgent", "metric": "multi-role resume orchestration"}],
    )
    profile = await profile_service.upsert_profile(db_session, user_id, workspace_id, payload)
    assert profile.headline.startswith("Agent engineer")
    assert profile.proof_points[0]["name"] == "CareerAgent"
```

- [ ] Wire `CandidateProfile` into `CareerAgentState` and preload it in both `role_service.initialize_role_assets()` and `jd_service.tailor_jd()`. The downstream nodes must receive profile context under a stable key, not ad-hoc prompt concatenation.

- [ ] Add API endpoints:
  - `GET /api/profile`
  - `PUT /api/profile`
  - `GET /api/profile/completeness`

- [ ] Add a minimal `Profile` page in the frontend. This page only needs to edit core fields and show completeness. Do not add settings sprawl in this task.

- [ ] Run verification:
  - `cd backend && python -m pytest tests/test_services/test_profile_service.py -v`
  - `cd backend && python -m pytest tests/test_api/test_profile_api.py -v`
  - `cd frontend && npm run test`
  - `cd frontend && npm run lint`

- [ ] Commit:

```bash
git add backend/src/models/profile.py backend/src/schemas/profile.py backend/src/services/profile_service.py backend/src/api/profile.py backend/src/models/__init__.py backend/src/api/router.py backend/src/agent/state.py backend/src/services/role_service.py backend/src/services/jd_service.py backend/alembic/versions/20260413_01_add_candidate_profile.py backend/tests/test_services/test_profile_service.py backend/tests/test_api/test_profile_api.py frontend/src/types/index.ts frontend/src/lib/api.ts frontend/src/hooks/useProfile.ts frontend/src/pages/Profile.tsx frontend/src/App.tsx
git commit -m "feat: add candidate profile foundation"
```

### Task 2: Story Bank

**Owner:** Agent B

**Depends on:** Task 1 merged

**Files:**
- Create: `backend/src/models/story.py`
- Create: `backend/src/schemas/story.py`
- Create: `backend/src/services/story_service.py`
- Create: `backend/src/api/stories.py`
- Create: `backend/src/prompts/story_extraction.py`
- Create: `backend/src/agent/nodes/story_extraction.py`
- Create: `backend/tests/test_services/test_story_service.py`
- Create: `backend/tests/test_api/test_story_api.py`
- Modify: `backend/src/models/__init__.py`
- Modify: `backend/src/api/router.py`
- Modify: `backend/src/agent/state.py`
- Modify: `backend/src/services/achievement_service.py`
- Modify: `backend/src/services/jd_service.py`
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/hooks/useStories.ts`
- Create: `frontend/src/pages/StoryBank.tsx`
- Modify: `frontend/src/App.tsx`
- Migration: `backend/alembic/versions/20260413_02_add_interview_stories.py`

- [ ] Add an `InterviewStory` model with source linkage to `Achievement` and `JDResumeTask`. Keep the body structured, not plain markdown.

```python
class InterviewStory(CommonBase):
    __tablename__ = "interview_stories"

    workspace_id = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = mapped_column(String(256), nullable=False)
    theme = mapped_column(String(128), nullable=False, default="general")
    source_type = mapped_column(String(64), nullable=False)
    source_ref_id = mapped_column(UUID(as_uuid=True), nullable=True)
    story_json = mapped_column(JSONB, nullable=False, default=dict)
    best_for_json = mapped_column(JSONB, nullable=False, default=list)
    confidence_score = mapped_column(Float, nullable=False, default=0.0)
```

- [ ] Add tests that verify deduplication by `theme + title + source_ref_id` and ordering by confidence score.

- [ ] Implement `story_extraction` as a reusable node that can be called from:
  - achievement pipeline after analysis
  - JD review flow after interview-plan generation

- [ ] Extend `achievement_service.run_achievement_pipeline()` to persist `InterviewStory` records when the pipeline emits story candidates.

- [ ] Expose API endpoints:
  - `GET /api/stories`
  - `POST /api/stories/rebuild/{achievement_id}`
  - `PATCH /api/stories/{story_id}`

- [ ] Add a simple `StoryBank` page with filters for theme and source type. This page is read-heavy; keep editing minimal in this task.

- [ ] Run verification:
  - `cd backend && python -m pytest tests/test_services/test_story_service.py -v`
  - `cd backend && python -m pytest tests/test_api/test_story_api.py -v`
  - `cd frontend && npm run test`

- [ ] Commit:

```bash
git add backend/src/models/story.py backend/src/schemas/story.py backend/src/services/story_service.py backend/src/api/stories.py backend/src/prompts/story_extraction.py backend/src/agent/nodes/story_extraction.py backend/src/models/__init__.py backend/src/api/router.py backend/src/agent/state.py backend/src/services/achievement_service.py backend/src/services/jd_service.py backend/alembic/versions/20260413_02_add_interview_stories.py backend/tests/test_services/test_story_service.py backend/tests/test_api/test_story_api.py frontend/src/types/index.ts frontend/src/hooks/useStories.ts frontend/src/pages/StoryBank.tsx frontend/src/App.tsx
git commit -m "feat: add reusable interview story bank"
```

### Task 3: JD Review Upgrade

**Owner:** Agent C

**Depends on:** Task 1 merged

**Files:**
- Create: `backend/src/prompts/jd_review.py`
- Create: `backend/src/agent/nodes/jd_review.py`
- Create: `backend/tests/test_services/test_jd_review_service.py`
- Modify: `backend/src/agent/graph.py`
- Modify: `backend/src/agent/state.py`
- Modify: `backend/src/models/jd.py`
- Modify: `backend/src/schemas/jd.py`
- Modify: `backend/src/services/jd_service.py`
- Modify: `backend/src/api/jd.py`
- Modify: `backend/src/agent/nodes/jd_tailoring.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/hooks/useJD.ts`
- Modify: `frontend/src/pages/JDTailor.tsx`
- Migration: `backend/alembic/versions/20260413_03_extend_jd_review_artifacts.py`

- [ ] Replace the current thin `jd_tailoring` contract with a two-stage JD flow:
  - `jd_parsing`
  - `jd_review`
  - `jd_tailoring`

- [ ] The new `jd_review` node must emit a structured artifact inspired by `career-ops` `oferta` mode:
  - role summary
  - evidence matrix
  - gaps with blocker-vs-nice-to-have label
  - personalization plan
  - interview plan
  - recommendation summary

```python
class JDReviewArtifact(TypedDict):
    role_summary: dict[str, Any]
    evidence_matrix: list[dict[str, Any]]
    gap_analysis: list[dict[str, Any]]
    personalization_plan: list[dict[str, Any]]
    interview_plan: list[dict[str, Any]]
    recommendation_summary: dict[str, Any]
```

- [ ] Extend `JDSnapshot` / `JDResumeTask` persistence to store:
  - `review_report_json`
  - `evidence_matrix_json`
  - `interview_plan_json`
  - `decision_summary`

- [ ] Update `JDTailorResponse` to include the review artifact, not only scores.

- [ ] Update `frontend/src/pages/JDTailor.tsx` to render three zones:
  - parsed JD
  - decision/report
  - tailored resume

- [ ] Keep the existing recommendation enum:
  - `apply_now`
  - `tune_then_apply`
  - `fill_gap_first`
  - `not_recommended`

- [ ] Do **not** add URL scraping in this task. Inputs remain pasted JD text only.

- [ ] Run verification:
  - `cd backend && python -m pytest tests/test_services/test_jd_review_service.py -v`
  - `cd backend && python -m pytest tests/test_api/test_health.py -v`
  - `cd frontend && npm run test`
  - Manual smoke: create one JD in UI and confirm report + tailored resume render together

- [ ] Commit:

```bash
git add backend/src/prompts/jd_review.py backend/src/agent/nodes/jd_review.py backend/src/agent/graph.py backend/src/agent/state.py backend/src/models/jd.py backend/src/schemas/jd.py backend/src/services/jd_service.py backend/src/api/jd.py backend/src/agent/nodes/jd_tailoring.py backend/alembic/versions/20260413_03_extend_jd_review_artifacts.py backend/tests/test_services/test_jd_review_service.py frontend/src/types/index.ts frontend/src/hooks/useJD.ts frontend/src/pages/JDTailor.tsx
git commit -m "feat: upgrade jd flow with structured review artifacts"
```

### Task 4: Suggestion Apply + Resume Diff

**Owner:** Agent D

**Depends on:** Task 3 merged

**Files:**
- Create: `backend/src/services/resume_diff_service.py`
- Create: `backend/tests/test_services/test_suggestion_apply_service.py`
- Modify: `backend/src/models/agent.py`
- Modify: `backend/src/schemas/suggestion.py`
- Modify: `backend/src/services/suggestion_service.py`
- Modify: `backend/src/services/resume_service.py`
- Modify: `backend/src/api/suggestions.py`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/pages/Suggestions.tsx`
- Modify: `frontend/src/pages/ResumeDetail.tsx`
- Migration: `backend/alembic/versions/20260413_04_extend_update_suggestions_apply_result.py`

- [ ] Add apply metadata to `UpdateSuggestion` so that accepted suggestions can record what version they produced.

```python
applied_resume_version_id = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id"), nullable=True, default=None)
review_notes = mapped_column(Text, nullable=True, default=None)
apply_result_json = mapped_column(JSONB, nullable=True, default=None)
```

- [ ] Change `accept_suggestion()` behavior:
  - `resume_update` and `jd_tune` create a new `ResumeVersion`
  - `gap_update` updates the related `GapItem`
  - final status becomes `applied`, not merely `accepted`, if the change was written

- [ ] Add a pure helper in `resume_diff_service.py` that compares two `ResumeContent` payloads and emits section-level add/remove/update summaries. Test this helper directly.

```python
def summarize_resume_diff(previous: dict, current: dict) -> dict:
    return {
        "summary_changed": previous.get("summary") != current.get("summary"),
        "section_counts": {...},
        "notable_updates": [...],
    }
```

- [ ] Update `ResumeDetail` version history UI to show:
  - source type
  - source ref
  - summary note
  - diff summary

- [ ] Update `Suggestions` page so the user sees whether a suggestion is only reviewed or actually applied.

- [ ] Run verification:
  - `cd backend && python -m pytest tests/test_services/test_suggestion_apply_service.py -v`
  - `cd frontend && npm run test`
  - Manual smoke: accept one suggestion and confirm `current_version_no` increments

- [ ] Commit:

```bash
git add backend/src/services/resume_diff_service.py backend/src/models/agent.py backend/src/schemas/suggestion.py backend/src/services/suggestion_service.py backend/src/services/resume_service.py backend/src/api/suggestions.py backend/alembic/versions/20260413_04_extend_update_suggestions_apply_result.py backend/tests/test_services/test_suggestion_apply_service.py frontend/src/types/index.ts frontend/src/pages/Suggestions.tsx frontend/src/pages/ResumeDetail.tsx
git commit -m "feat: apply suggestions into resume versions with diffs"
```

### Task 5: PDF Export

**Owner:** Agent E

**Depends on:** Task 3 and Task 4 merged

**Files:**
- Create: `backend/src/services/pdf_export_service.py`
- Create: `backend/src/templates/resume_export.html`
- Create: `backend/tests/test_services/test_pdf_export_service.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/models/jd.py`
- Modify: `backend/src/services/jd_service.py`
- Modify: `backend/src/api/resumes.py`
- Modify: `backend/src/api/jd.py`
- Modify: `frontend/src/pages/ResumeDetail.tsx`
- Modify: `frontend/src/pages/JDTailor.tsx`
- Migration: `backend/alembic/versions/20260413_05_add_pdf_export_fields.py`

- [ ] Add `playwright` to backend dependencies and implement backend-owned PDF rendering. Do not add a second root Node workspace.

- [ ] Reuse the structure of `career-ops` `cv-template.html`, but convert it into a backend template fed by structured `ResumeContent`.

- [ ] Add ATS normalization before rendering:
  - replace em dash / en dash with `-`
  - replace smart quotes with ASCII quotes
  - strip zero-width characters
  - replace non-breaking spaces with plain spaces

```python
def normalize_text_for_ats(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u00a0", " ")
    )
```

- [ ] Expose export endpoints:
  - `POST /api/resumes/{resume_id}/export-pdf`
  - `POST /api/jd/tasks/{task_id}/export-pdf`

- [ ] Persist generated PDF metadata on `JDResumeTask` so JD detail/history can show whether an export already exists.

- [ ] Add download/export buttons to:
  - `ResumeDetail`
  - final step of `JDTailor`

- [ ] Run verification:
  - `cd backend && python -m pytest tests/test_services/test_pdf_export_service.py -v`
  - `cd backend && python -m pytest tests/test_api/test_health.py -v`
  - Manual smoke: export one master resume and one JD-tailored resume

- [ ] Commit:

```bash
git add backend/src/services/pdf_export_service.py backend/src/templates/resume_export.html backend/tests/test_services/test_pdf_export_service.py backend/pyproject.toml backend/src/models/jd.py backend/src/services/jd_service.py backend/src/api/resumes.py backend/src/api/jd.py backend/alembic/versions/20260413_05_add_pdf_export_fields.py frontend/src/pages/ResumeDetail.tsx frontend/src/pages/JDTailor.tsx
git commit -m "feat: add ats friendly pdf export for resumes and jd tasks"
```

### Task 6: Dashboard + UI Surfaces

**Owner:** Agent F

**Depends on:** Task 2, Task 3, Task 4, Task 5 merged

**Files:**
- Create: `backend/src/services/dashboard_service.py`
- Create: `backend/src/api/dashboard.py`
- Create: `frontend/src/hooks/useDashboard.ts`
- Modify: `backend/src/api/router.py`
- Modify: `frontend/src/pages/Dashboard.tsx`
- Modify: `frontend/src/pages/RoleDetail.tsx`
- Modify: `frontend/src/types/index.ts`

- [ ] Add a compact dashboard aggregation endpoint returning:
  - role count
  - active resume count
  - open high-priority gap count
  - recent achievement count
  - pending suggestion count
  - story count
  - latest JD decisions

- [ ] Replace hard-coded zeros in `Dashboard.tsx` with live data.

- [ ] Add two high-value widgets only:
  - `Recent Agent Activity`
  - `Recent JD Decisions`

- [ ] Update `RoleDetail` to show:
  - latest JD tailoring activity for the role
  - story count linked to this role’s achievements

- [ ] Do not build a new dashboard framework in this task. Keep it thin and data-driven.

- [ ] Run verification:
  - `cd backend && python -m pytest tests/test_api/test_health.py -v`
  - `cd frontend && npm run test`
  - `cd frontend && npm run lint`
  - Manual smoke: dashboard reflects non-zero data after seeded workflow

- [ ] Commit:

```bash
git add backend/src/services/dashboard_service.py backend/src/api/dashboard.py backend/src/api/router.py frontend/src/hooks/useDashboard.ts frontend/src/pages/Dashboard.tsx frontend/src/pages/RoleDetail.tsx frontend/src/types/index.ts
git commit -m "feat: replace placeholder dashboard with live career asset metrics"
```

## Integration Review Checklist

- [ ] `CandidateProfile` is loaded into role-init and JD flows.
- [ ] Story bank records are linked back to achievements and/or JD tasks.
- [ ] `JD` API now returns a review artifact plus tailored resume.
- [ ] Accepting a suggestion can materially change data, not only status.
- [ ] Resume versions preserve provenance and diff summaries.
- [ ] PDF export works for structured resumes without fabricating content.
- [ ] Dashboard shows real data from the database.
- [ ] No task introduced portal scan, auto-apply, markdown tracker, or CLI-only UX.

## Final Verification Commands

Run these after all tasks are merged:

```bash
make test-backend
make test-frontend
make lint
```

Manual smoke flow:

1. Create or update profile
2. Create a target role
3. Add and analyze one achievement
4. Run one JD tailoring flow
5. Accept one resume-related suggestion
6. Export PDF
7. Verify dashboard and story bank reflect the above actions

