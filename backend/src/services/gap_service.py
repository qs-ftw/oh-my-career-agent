"""Database-backed service for gap operations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gap import GapItem
from src.schemas.gap import GapResponse, GapUpdate


def _to_response(gap: GapItem) -> GapResponse:
    return GapResponse(
        id=gap.id,
        target_role_id=gap.target_role_id,
        skill_name=gap.skill_name,
        gap_type=gap.gap_type,
        priority=gap.priority,
        current_state=gap.current_state or "",
        target_state=gap.target_state or "",
        evidence=gap.evidence_json or [],
        improvement_plan=gap.improvement_plan_json or {},
        progress=gap.progress,
        status=gap.status,
        created_at=gap.created_at,
        updated_at=gap.updated_at,
    )


async def list_gaps(
    session: AsyncSession,
    user_id: uuid.UUID,
    role_id: uuid.UUID | None = None,
) -> list[GapResponse]:
    """List gaps for user, optionally filtered by role."""
    stmt = (
        select(GapItem)
        .where(GapItem.user_id == user_id)
        .order_by(GapItem.priority.desc(), GapItem.created_at.desc())
    )
    if role_id is not None:
        stmt = stmt.where(GapItem.target_role_id == role_id)

    result = await session.execute(stmt)
    gaps = result.scalars().all()
    return [_to_response(g) for g in gaps]


async def list_gaps_for_role(
    session: AsyncSession,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
) -> list[GapResponse]:
    """List all gaps for a specific role."""
    return await list_gaps(session, user_id, role_id=role_id)


async def update_gap(
    session: AsyncSession,
    user_id: uuid.UUID,
    gap_id: uuid.UUID,
    data: GapUpdate,
) -> GapResponse | None:
    """Update a gap item."""
    stmt = select(GapItem).where(
        GapItem.id == gap_id,
        GapItem.user_id == user_id,
    )
    result = await session.execute(stmt)
    gap = result.scalar_one_or_none()
    if gap is None:
        return None

    update_map = data.model_dump(exclude_unset=True)
    if "status" in update_map:
        gap.status = update_map["status"]
        if update_map["status"] == "closed":
            gap.closed_at = datetime.now(UTC)
    if "progress" in update_map:
        gap.progress = update_map["progress"]

    gap.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(gap)
    return _to_response(gap)
