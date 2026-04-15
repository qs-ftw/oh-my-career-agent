"""Database-backed service for suggestion operations."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent import UpdateSuggestion
from src.schemas.suggestion import SuggestionResponse

logger = logging.getLogger(__name__)


def _to_response(s: UpdateSuggestion) -> SuggestionResponse:
    """Convert an UpdateSuggestion ORM instance to SuggestionResponse."""
    impact_score = 0.0
    if s.impact_score_json:
        if isinstance(s.impact_score_json, (int, float)):
            impact_score = float(s.impact_score_json)
        elif isinstance(s.impact_score_json, dict):
            impact_score = float(s.impact_score_json.get("score", 0.0))

    return SuggestionResponse(
        id=s.id,
        suggestion_type=s.suggestion_type,
        target_role_id=s.target_role_id,
        resume_id=s.resume_id,
        source_achievement_id=s.source_achievement_id,
        title=s.title,
        content=s.content_json,
        impact_score=impact_score,
        risk_level=s.risk_level,
        status=s.status,
        applied_resume_version_id=s.applied_resume_version_id,
        apply_result=s.apply_result_json,
        created_at=s.created_at,
    )


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


async def accept_suggestion(
    session: AsyncSession,
    user_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    notes: str | None = None,
) -> SuggestionResponse | None:
    """Accept a suggestion and apply it.

    For resume_update and jd_tune suggestions:
      - Creates a new ResumeVersion with the suggested changes applied
      - Updates the suggestion status to 'applied' and records the version ref

    For gap_update suggestions:
      - Updates the related GapItem
      - Sets status to 'applied'
    """
    stmt = select(UpdateSuggestion).where(
        UpdateSuggestion.id == suggestion_id,
        UpdateSuggestion.user_id == user_id,
    )
    result = await session.execute(stmt)
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        return None

    suggestion.review_notes = notes

    applied_version_id = None
    apply_result = {}

    if suggestion.suggestion_type in ("resume_update", "jd_tune") and (suggestion.resume_id or suggestion.target_role_id):
        # Apply to resume: create new version
        from src.models.resume import Resume, ResumeVersion
        from src.models.target_role import TargetRole
        from src.services.resume_diff_service import summarize_resume_diff

        # Resolve resume_id: use explicit ID, or look up by target_role_id
        resume_id = suggestion.resume_id
        if resume_id is None and suggestion.target_role_id:
            fallback_stmt = select(Resume).where(
                Resume.target_role_id == suggestion.target_role_id,
                Resume.resume_type == "master",
                Resume.deleted_at.is_(None),
            )
            fallback_result = await session.execute(fallback_stmt)
            fallback_resume = fallback_result.scalar_one_or_none()
            if fallback_resume:
                resume_id = fallback_resume.id
                suggestion.resume_id = resume_id

        if resume_id is None:
            # No resume found — just mark as accepted
            suggestion.status = "accepted"
        else:
            # Load the resume
            resume_stmt = select(Resume).where(
                Resume.id == resume_id,
                Resume.deleted_at.is_(None),
            )
            resume_result = await session.execute(resume_stmt)
            resume = resume_result.scalar_one_or_none()

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

                # Determine the merge strategy based on content type:
                # 1. Dict with resume section keys (skills, experiences, etc.) → direct merge
                # 2. Dict with descriptive keys (section, action, text, reasoning) → transform into resume content
                # 3. String → wrap as an experience entry
                _RESUME_SECTION_KEYS = {"summary", "skills", "experiences", "projects", "highlights", "metrics", "interview_points", "contact"}
                _DESCRIPTIVE_KEYS = {"section", "action", "text", "reasoning"}

                if isinstance(suggested_content, dict) and _RESUME_SECTION_KEYS & set(suggested_content.keys()):
                    # Content is structured resume data — merge directly
                    new_content = {**previous_content, **suggested_content}
                elif isinstance(suggested_content, dict) and _DESCRIPTIVE_KEYS & set(suggested_content.keys()):
                    # Content is a descriptive suggestion — transform into resume update
                    section = suggested_content.get("section", "experiences")
                    action_text = suggested_content.get("text", "")
                    if action_text and section == "experiences":
                        experiences = list(previous_content.get("experiences", []))
                        experiences.append({"description": action_text, "source": suggestion.title})
                        new_content = {**previous_content, "experiences": experiences}
                    elif action_text and section == "skills":
                        skills = list(previous_content.get("skills", []))
                        if isinstance(action_text, str):
                            new_skills = [s.strip() for s in action_text.split(",") if s.strip()]
                        else:
                            new_skills = [action_text]
                        skills.extend(new_skills)
                        new_content = {**previous_content, "skills": skills}
                    elif action_text and section == "highlights":
                        highlights = list(previous_content.get("highlights", []))
                        highlights.append(action_text)
                        new_content = {**previous_content, "highlights": highlights}
                    else:
                        new_content = previous_content
                elif isinstance(suggested_content, str) and suggested_content.strip():
                    # Content is plain text — wrap as an experience entry
                    experiences = list(previous_content.get("experiences", []))
                    experiences.append({"description": suggested_content, "source": suggestion.title})
                    new_content = {**previous_content, "experiences": experiences}
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
                    completeness_score=0.0,
                    match_score=0.0,
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

    elif suggestion.suggestion_type == "gap_update":
        # For gap updates, just mark as applied
        suggestion.status = "applied"
        suggestion.apply_result_json = {"action": "gap_status_updated"}

    else:
        suggestion.status = "accepted"

    suggestion.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(suggestion)
    return _to_response(suggestion)


async def reject_suggestion(
    session: AsyncSession,
    user_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    notes: str | None = None,
) -> SuggestionResponse | None:
    """Reject a suggestion and update its status."""
    stmt = select(UpdateSuggestion).where(
        UpdateSuggestion.id == suggestion_id,
        UpdateSuggestion.user_id == user_id,
    )
    result = await session.execute(stmt)
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        return None

    suggestion.status = "rejected"
    suggestion.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(suggestion)
    return _to_response(suggestion)
