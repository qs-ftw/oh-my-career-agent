# Achievement Center Enhancement Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the achievement center with tab filtering, suggestion integration in detail drawer, and fix the accept-suggestion pipeline to properly update resume scores.

**Architecture:** Add `source_achievement_id` to UpdateSuggestion model for linking suggestions back to achievements. Fix backend accept logic to recalculate scores. Frontend gets sticky tab bar and suggestion cards in the detail drawer.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React 19, TanStack Query, TypeScript

---

## 1. Sticky Tab Bar with Filtering

### Current State
- Tag filter chips + "新增成果" button scroll away with page content
- No status-based filtering

### New State
Replace tag filter chips with a sticky tab bar:

| Tab | Filter Logic |
|-----|-------------|
| 全部 | All achievements |
| 未分析 | `importance_score === 0` (no parsed_summary) |
| 待处理 | Analyzed AND has pending suggestions linked to this achievement |
| 已完成 | Analyzed AND no pending suggestions |

The tab bar + "新增成果" button use `sticky top-0 z-10 bg-card border-b` so they stay visible when scrolling.

**Frontend filtering**: "全部" and "未分析" can be filtered client-side from the achievements list. "待处理" and "已完成" require knowing which achievements have pending suggestions — fetch via `GET /suggestions?status=pending` and group by `source_achievement_id` to build a Set.

### Files to Modify
- `frontend/src/pages/Achievements.tsx` — replace tag filter with tab bar, add sticky positioning

---

## 2. Achievement Detail Drawer: Add Update Suggestions

### Current State
- Detail drawer shows parsed_summary (which is a copy of raw content) + technical details
- No visibility into what suggestions were generated from this achievement
- Accept/reject only available on standalone Suggestions page

### New State
After the analysis result sections, add an "更新建议" section in the detail drawer:

- Section title: "更新建议" with count badge
- Each suggestion card shows:
  - Target role name (resolved from target_role_id — needs role list or lookup)
  - Suggestion title
  - Suggestion type badge (resume_update / gap_update)
  - Risk level badge (low/medium/high)
  - Impact score
  - Status badge: pending (yellow), accepted (green), rejected (gray)
  - For pending: "采纳" and "拒绝" buttons
  - For accepted/rejected: just the status badge

When a suggestion is accepted/rejected from the drawer:
- Update the suggestion status
- Refresh the achievement detail
- Refresh suggestions list
- Refresh resumes and gaps (so scores update)

### Backend Changes

**New field**: Add `source_achievement_id` (nullable UUID, FK to achievements) to `UpdateSuggestion` model.

**New query param**: `GET /suggestions` accepts `achievement_id` filter — returns suggestions where `source_achievement_id = <id>`.

**Pipeline update**: In `achievement_service.run_achievement_pipeline()`, when creating suggestions, set `source_achievement_id` to the current achievement's ID.

### Files
- Modify: `backend/src/models/agent.py` — add `source_achievement_id` column
- Modify: `backend/src/services/achievement_service.py` — set source_achievement_id when creating suggestions
- Modify: `backend/src/services/suggestion_service.py` — add achievement_id filter to list query
- Modify: `backend/src/api/suggestions.py` — accept achievement_id query param
- New migration: add `source_achievement_id` column to `update_suggestions` table
- Modify: `frontend/src/pages/Achievements.tsx` — add suggestions section to DetailDrawer
- Modify: `frontend/src/hooks/useSuggestions.ts` — support achievement_id filter
- Modify: `frontend/src/hooks/useAchievements.ts` — add query for suggestions-by-achievement

---

## 3. Fix Accept-Suggestion Pipeline

### Current Bugs
1. Backend `accept_suggestion` creates new ResumeVersion with `completeness_score=0.0` and `match_score=0.0` — scores not recalculated
2. Backend doesn't update parent `Resume` record's `completeness_score` and `match_score`
3. Frontend `useAcceptSuggestion` only invalidates `["suggestions"]` — doesn't refresh resumes, gaps, or roles

### Fix
**Backend** (`suggestion_service.py`):
- After creating the new ResumeVersion, import `_calc_completeness` and `_calc_match_score` from `resume_service`
- Look up the role's `required_skills` to pass to `_calc_match_score`
- Set both scores on the new ResumeVersion
- Update the parent Resume record's `completeness_score` and `match_score`

**Frontend** (`useSuggestions.ts`):
- `useAcceptSuggestion` onSuccess: invalidate `["suggestions"]`, `["resumes"]`, `["gaps"]`, `["roles"]`

### Files
- Modify: `backend/src/services/suggestion_service.py` — recalculate scores after accept
- Modify: `frontend/src/hooks/useSuggestions.ts` — add cache invalidation for resumes/gaps/roles

---

## 4. Standalone Suggestions Page

The standalone Suggestions page is kept as a global view of all suggestions across all achievements. No changes needed — it continues to work as-is.

---

## Files Summary

### New Files
| File | Purpose |
|------|---------|
| `alembic/versions/xxx_add_source_achievement_id_to_suggestions.py` | Migration for new column |

### Modified Files
| File | Change |
|------|--------|
| `backend/src/models/agent.py` | Add `source_achievement_id` column to UpdateSuggestion |
| `backend/src/services/achievement_service.py` | Set source_achievement_id when creating suggestions |
| `backend/src/services/suggestion_service.py` | Recalculate scores on accept; add achievement_id filter |
| `backend/src/api/suggestions.py` | Accept achievement_id query param |
| `frontend/src/pages/Achievements.tsx` | Tab bar, sticky toolbar, suggestions in detail drawer |
| `frontend/src/hooks/useSuggestions.ts` | Support achievement_id filter, fix cache invalidation |
| `frontend/src/hooks/useAchievements.ts` | Add useSuggestionsForAchievement hook |

---

## Verification Checklist

1. **Tab filtering**: Open achievements → each tab filters correctly → counts accurate
2. **Sticky toolbar**: Scroll down → tab bar + button stay visible at top
3. **Detail drawer suggestions**: Analyze an achievement → open detail → see suggestion cards with accept/reject
4. **Accept from drawer**: Click "采纳" → suggestion status updates → resume gets new version → match/completeness scores update
5. **Score recalculation**: Before accept match=40%, after accept match=55% (actual numbers vary)
6. **Tab "待处理" count**: After accepting all suggestions from an achievement, it moves from "待处理" to "已完成"
7. **Standalone suggestions page**: Still works, shows all suggestions globally
