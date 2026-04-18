"""SSE streaming endpoints for long-running AI pipelines."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.models.achievement import Achievement
from src.models.profile import CareerProfile
from src.agent.graph import achievement_graph, jd_tailoring_graph
from src.services.pipeline_stream_service import stream_pipeline
from src.services.achievement_service import _build_target_roles_data, persist_pipeline_results

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


@router.get(
    "/achievements/{achievement_id}/stream-analysis",
    summary="Stream achievement analysis via SSE",
)
async def stream_achievement_analysis(
    achievement_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
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
            yield ServerSentEvent(event="pipeline_error", data=json.dumps({"error": "Achievement not found"}))
            return

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

        # Stream events and capture final pipeline state
        result_container: dict = {}
        async for sse_event in stream_pipeline(
            achievement_graph, agent_input, result_container=result_container
        ):
            yield sse_event

        # Persist results after streaming completes
        pipeline_result = result_container.get("output", agent_input)
        pipeline_error = pipeline_result.get("pipeline_error")
        try:
            await persist_pipeline_results(
                session=db,
                user_id=user_id,
                workspace_id=workspace_id,
                achievement_id=achievement_id,
                pipeline_result=pipeline_result,
                target_roles_data=target_roles_data,
                pipeline_error=pipeline_error,
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to persist pipeline results for {achievement_id}: {e}")
            await db.rollback()

    return EventSourceResponse(event_generator())


@router.get(
    "/jd/tailor-stream",
    summary="Stream JD tailoring via SSE",
)
async def stream_jd_tailoring(
    raw_jd: str = Query(..., description="Raw JD text"),
    mode: str = Query("generate_new", description="generate_new or tune_existing"),
    base_resume_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """SSE endpoint that streams the 4-step JD tailoring pipeline."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()

    async def event_generator():
        from src.services.career_markdown_service import export_markdown
        from src.services.profile_service import get_profile_context
        from src.models.resume import ResumeVersion
        from src.models.jd import JDResumeTask, JDSnapshot

        # 1. Create JD snapshot
        snapshot = JDSnapshot(
            workspace_id=workspace_id,
            user_id=user_id,
            source_type="manual",
            raw_jd=raw_jd,
        )
        db.add(snapshot)
        await db.flush()

        # 2. Create task record
        task = JDResumeTask(
            workspace_id=workspace_id,
            user_id=user_id,
            jd_snapshot_id=snapshot.id,
            mode=mode,
            base_resume_id=base_resume_id,
            status="running",
        )
        db.add(task)
        await db.flush()

        # 3. Load career markdown
        profile_stmt = select(CareerProfile).where(
            CareerProfile.user_id == user_id,
            CareerProfile.workspace_id == workspace_id,
        )
        profile_result = await db.execute(profile_stmt)
        career_profile = profile_result.scalar_one_or_none()
        career_markdown = ""
        if career_profile:
            career_markdown = await export_markdown(db, career_profile.id)

        profile_ctx = await get_profile_context(db, user_id, workspace_id)

        # 4. Load base resume if tuning
        base_resume_content = None
        if mode == "tune_existing" and base_resume_id:
            ver_stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == base_resume_id)
                .order_by(ResumeVersion.version_no.desc())
                .limit(1)
            )
            ver_result = await db.execute(ver_stmt)
            version = ver_result.scalar_one_or_none()
            if version and version.content_json:
                base_resume_content = (
                    version.content_json
                    if isinstance(version.content_json, dict) else {}
                )

        # 5. Build agent input
        agent_input = {
            "user_id": str(user_id),
            "workspace_id": str(workspace_id),
            "candidate_profile": profile_ctx or None,
            "jd_raw": raw_jd,
            "jd_mode": mode,
            "base_resume_id": str(base_resume_id) if base_resume_id else None,
            "career_assets": {"cv_markdown": career_markdown},
            "base_resume_content": base_resume_content,
            "skip_review": True,
            "jd_parsed": None,
            "jd_keywords": None,
            "selected_content": None,
            "keyword_coverage": None,
            "resume_patches": [],
            "resume_draft": None,
            "match_scores": None,
            "suggestions": [],
            "gap_updates": [],
            "agent_logs": [],
            "career_markdown": career_markdown,
        }

        # 6. Stream pipeline events
        result_container: dict = {}
        async for sse_event in stream_pipeline(
            jd_tailoring_graph, agent_input, result_container=result_container
        ):
            yield sse_event

        # 7. Persist results after streaming completes
        pipeline_result = result_container.get("output", agent_input)

        # Derive match_scores from keyword coverage
        keyword_coverage = pipeline_result.get("keyword_coverage") or {}
        coverage_score = keyword_coverage.get("coverage_score", 0.0)
        recommendation = (
            "apply_now" if coverage_score >= 0.8
            else "tune_then_apply" if coverage_score >= 0.6
            else "fill_gap_first" if coverage_score >= 0.4
            else "not_recommended"
        )
        match_scores = {
            "ability_match_score": coverage_score,
            "resume_match_score": coverage_score * 0.95,
            "readiness_score": coverage_score * 0.9,
            "recommendation": recommendation,
            "missing_items": keyword_coverage.get("uncovered_keywords", []),
            "optimization_notes": [
                p.get("suggestion", "") for p in pipeline_result.get("resume_patches", [])
            ],
        }

        resume_draft = pipeline_result.get("resume_draft") or {}
        review_artifact = pipeline_result.get("jd_review_artifact")

        task.ability_match_score = match_scores.get("ability_match_score", 0.0)
        task.resume_match_score = match_scores.get("resume_match_score", 0.0)
        task.readiness_score = match_scores.get("readiness_score", 0.0)
        task.recommendation = match_scores.get("recommendation", "not_recommended")
        task.missing_items_json = match_scores.get("missing_items", [])
        task.optimization_notes_json = match_scores.get("optimization_notes", [])
        task.status = "completed"

        if review_artifact:
            task.review_report_json = review_artifact
            task.evidence_matrix_json = review_artifact.get("evidence_matrix", [])
            task.interview_plan_json = review_artifact.get("interview_plan", [])
            rec = review_artifact.get("recommendation_summary", {})
            task.decision_summary = rec.get("reasoning", "")

        jd_parsed = pipeline_result.get("jd_parsed") or {}
        if jd_parsed:
            snapshot.parsed_role_name = jd_parsed.get("role_name", "")
            snapshot.parsed_keywords_json = jd_parsed.get("keywords", [])
            snapshot.parsed_required_skills_json = jd_parsed.get("required_skills", [])
            snapshot.parsed_bonus_items_json = jd_parsed.get("bonus_items", [])
            snapshot.parsed_style_json = jd_parsed.get("style", {})

        try:
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to persist JD pipeline results for task {task.id}: {e}")
            await db.rollback()

    return EventSourceResponse(event_generator())
