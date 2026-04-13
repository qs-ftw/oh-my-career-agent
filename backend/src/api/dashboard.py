"""Dashboard endpoints — live career asset metrics."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id
from src.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/stats",
    summary="Get dashboard statistics",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return aggregated career asset metrics."""
    user_id = await get_current_user_id()
    return await dashboard_service.get_dashboard_stats(db, user_id)


@router.get(
    "/recent-jd-decisions",
    summary="Get recent JD decisions",
)
async def get_recent_jd_decisions(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return the most recent JD tailoring decisions."""
    user_id = await get_current_user_id()
    return await dashboard_service.get_recent_jd_decisions(db, user_id)
