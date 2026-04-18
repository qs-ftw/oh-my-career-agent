"""Gap endpoints — database-backed CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id
from src.schemas.gap import GapResponse, GapUpdate
from src.services import gap_service

router = APIRouter(tags=["gaps"])


@router.get(
    "/gaps",
    response_model=list[GapResponse],
    summary="List all gaps",
)
async def list_gaps(
    role_id: uuid.UUID | None = Query(default=None, description="Filter by target role ID"),
    db: AsyncSession = Depends(get_db),
) -> list[GapResponse]:
    """Return all gap items, optionally filtered by role."""
    user_id = await get_current_user_id()
    return await gap_service.list_gaps(db, user_id, role_id=role_id)


@router.patch(
    "/gaps/{gap_id}",
    response_model=GapResponse,
    summary="Update a gap",
)
async def update_gap(
    body: GapUpdate,
    gap_id: uuid.UUID = Path(..., description="The gap UUID"),
    db: AsyncSession = Depends(get_db),
) -> GapResponse:
    """Partially update a gap (e.g. change status or progress)."""
    user_id = await get_current_user_id()
    gap = await gap_service.update_gap(db, user_id, gap_id, body)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap not found")
    return gap


@router.get(
    "/roles/{role_id}/gaps",
    response_model=list[GapResponse],
    summary="List gaps for a specific role",
)
async def list_gaps_for_role(
    role_id: uuid.UUID = Path(..., description="The target role UUID"),
    db: AsyncSession = Depends(get_db),
) -> list[GapResponse]:
    """Return all gap items associated with a target role."""
    user_id = await get_current_user_id()
    return await gap_service.list_gaps_for_role(db, user_id, role_id)
