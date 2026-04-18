"""Database-backed service for resume CRUD operations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.resume import Resume, ResumeVersion
from src.schemas.resume import ResumeContent, ResumeResponse, ResumeUpdate


def _to_response(resume: Resume, version: ResumeVersion | None = None) -> ResumeResponse:
    """Convert a Resume ORM instance (+ optional version) into a ResumeResponse."""
    content = ResumeContent(
        summary="",
        skills=[],
        experiences=[],
        projects=[],
        highlights=[],
        metrics=[],
        interview_points=[],
    )
    if version and version.content_json:
        raw = version.content_json
        content = ResumeContent(**raw)

    return ResumeResponse(
        id=resume.id,
        target_role_id=resume.target_role_id,
        resume_name=resume.resume_name,
        resume_type=resume.resume_type,
        current_version_no=resume.current_version_no,
        status=resume.status,
        completeness_score=resume.completeness_score or 0.0,
        match_score=resume.match_score or 0.0,
        content=content,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


def _latest_version_stmt(resume_id: uuid.UUID) -> select:
    """Build a query that returns the latest ResumeVersion for a resume."""
    return (
        select(ResumeVersion)
        .where(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_no.desc())
        .limit(1)
    )


async def list_resumes(
    session: AsyncSession,
    user_id: uuid.UUID,
    target_role_id: uuid.UUID | None = None,
) -> list[ResumeResponse]:
    """Return all non-deleted resumes for *user_id*, optionally filtered by target role."""
    stmt = (
        select(Resume)
        .where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
        .order_by(Resume.created_at.desc())
    )
    if target_role_id is not None:
        stmt = stmt.where(Resume.target_role_id == target_role_id)

    result = await session.execute(stmt)
    resumes = result.scalars().all()

    responses: list[ResumeResponse] = []
    for resume in resumes:
        ver_result = await session.execute(_latest_version_stmt(resume.id))
        version = ver_result.scalar_one_or_none()
        responses.append(_to_response(resume, version))

    return responses


async def get_resume(
    session: AsyncSession,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
) -> ResumeResponse | None:
    """Return a single resume (with latest version content) or None."""
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        return None

    ver_result = await session.execute(_latest_version_stmt(resume.id))
    version = ver_result.scalar_one_or_none()
    return _to_response(resume, version)


async def delete_resume(
    session: AsyncSession,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
) -> None:
    """Soft-delete a resume."""
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Resume not found")
    resume.deleted_at = datetime.now(UTC)
    await session.flush()


async def update_resume(
    session: AsyncSession,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    data: ResumeUpdate,
) -> ResumeResponse | None:
    """Update a resume.  If content changed, a new ResumeVersion is created."""
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        return None

    update_map = data.model_dump(exclude_unset=True)

    # Update simple fields.
    if "resume_name" in update_map and update_map["resume_name"] is not None:
        resume.resume_name = update_map["resume_name"]

    # If content is provided, create a new version.
    if "content" in update_map and update_map["content"] is not None:
        # Use exclude_unset to get ONLY the fields the client actually sent.
        # Without this, Pydantic fills in defaults (empty strings/lists) for
        # omitted fields, and the merge would overwrite existing data with blanks.
        content_payload = data.content.model_dump(exclude_unset=True)

        # Fetch the current latest version to determine the next version number.
        ver_result = await session.execute(_latest_version_stmt(resume.id))
        latest_version = ver_result.scalar_one_or_none()
        next_version_no = (latest_version.version_no + 1) if latest_version else 1

        # Deep-merge with existing version content so partial updates don't lose data
        if latest_version and latest_version.content_json:
            existing = latest_version.content_json
            merged = {**existing, **content_payload}
            # Recursively merge nested dicts (like contact)
            for key in merged:
                if (
                    key in existing
                    and key in content_payload
                    and isinstance(existing[key], dict)
                    and isinstance(content_payload[key], dict)
                ):
                    merged[key] = {**existing[key], **content_payload[key]}
            content_payload = merged

        new_version = ResumeVersion(
            resume_id=resume.id,
            version_no=next_version_no,
            content_json=content_payload if isinstance(content_payload, dict) else content_payload,
            generated_by="user",
            source_type="manual_edit",
            completeness_score=0.0,
            match_score=0.0,
        )
        session.add(new_version)

        resume.current_version_no = next_version_no

    # Touch updated_at.
    resume.updated_at = datetime.now(UTC)

    await session.flush()
    await session.refresh(resume)

    # Return with latest version.
    ver_result = await session.execute(_latest_version_stmt(resume.id))
    version = ver_result.scalar_one_or_none()
    return _to_response(resume, version)


async def list_versions(
    session: AsyncSession,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
) -> list[dict]:
    """Return all versions for a resume, newest first."""
    # First, verify that the resume belongs to the user and is not deleted.
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        return []

    ver_stmt = (
        select(ResumeVersion)
        .where(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_no.desc())
    )
    ver_result = await session.execute(ver_stmt)
    versions = ver_result.scalars().all()

    return [
        {
            "id": str(v.id),
            "version_no": v.version_no,
            "generated_by": v.generated_by,
            "source_type": v.source_type,
            "summary_note": v.summary_note,
            "completeness_score": v.completeness_score,
            "match_score": v.match_score,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


async def get_version(
    session: AsyncSession,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
) -> dict | None:
    """Return a single version with its full content, or None."""
    # Verify ownership
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        return None

    ver_stmt = select(ResumeVersion).where(
        ResumeVersion.id == version_id,
        ResumeVersion.resume_id == resume_id,
    )
    ver_result = await session.execute(ver_stmt)
    version = ver_result.scalar_one_or_none()
    if version is None:
        return None

    return {
        "id": str(version.id),
        "version_no": version.version_no,
        "content": version.content_json or {},
        "generated_by": version.generated_by,
        "source_type": version.source_type,
        "summary_note": version.summary_note,
        "completeness_score": version.completeness_score,
        "match_score": version.match_score,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


async def delete_version(
    session: AsyncSession,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    version_id: uuid.UUID,
) -> None:
    """Delete a resume version. Cannot delete the current (latest) version."""
    # Verify ownership
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user_id,
        Resume.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Resume not found")

    # Find the version
    ver_stmt = select(ResumeVersion).where(
        ResumeVersion.id == version_id,
        ResumeVersion.resume_id == resume_id,
    )
    ver_result = await session.execute(ver_stmt)
    version = ver_result.scalar_one_or_none()
    if version is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Version not found")

    # Cannot delete the current version
    if version.version_no == resume.current_version_no:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Cannot delete the current version")

    await session.execute(
        sa_delete(ResumeVersion).where(ResumeVersion.id == version_id)
    )
    await session.flush()


# ---------------------------------------------------------------------------
# Score calculation helpers
# ---------------------------------------------------------------------------

_SECTIONS = ("summary", "skills", "experiences", "projects", "highlights", "metrics", "interview_points")


def _calc_completeness(content: dict) -> float:
    """Calculate resume completeness as percentage of sections with content."""
    filled = sum(1 for s in _SECTIONS if content.get(s))
    return round(filled / len(_SECTIONS) * 100, 1)


def _calc_match_score(content: dict, role_skills: list[str]) -> float:
    """Calculate match score: % of role required skills found in resume skills."""
    if not role_skills:
        return 0.0
    resume_skills = set(s.lower() for s in (content.get("skills") or []))
    matched = sum(1 for s in role_skills if s.lower() in resume_skills)
    return round(matched / len(role_skills) * 100, 1)


async def create_resume_for_role(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    target_role_id: uuid.UUID,
    initial_content: ResumeContent,
    role_skills: list[str] | None = None,
    role_name: str | None = None,
    profile_contact: dict | None = None,
) -> ResumeResponse:
    """Create a new master resume for a given role with its first version.

    Used by the role-initialization agent pipeline.
    """
    if hasattr(initial_content, "model_dump"):
        content_dict = initial_content.model_dump()
    else:
        content_dict = dict(initial_content)

    # Auto-fill contact from profile if resume has no contact info
    if profile_contact and not content_dict.get("contact"):
        content_dict["contact"] = profile_contact

    completeness = _calc_completeness(content_dict)
    match_score = _calc_match_score(content_dict, role_skills or [])

    resume_name = f"{role_name} - 主简历" if role_name else "主简历"

    resume = Resume(
        workspace_id=workspace_id,
        user_id=user_id,
        target_role_id=target_role_id,
        resume_name=resume_name,
        resume_type="master",
        parent_resume_id=None,
        current_version_no=1,
        status="draft",
        completeness_score=completeness,
        match_score=match_score,
    )
    session.add(resume)
    await session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_no=1,
        content_json=content_dict,
        generated_by="agent",
        source_type="initial_draft",
        completeness_score=completeness,
        match_score=match_score,
    )
    session.add(version)
    await session.flush()
    await session.refresh(resume)

    return _to_response(resume, version)
