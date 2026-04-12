"""Target role endpoints -- CRUD backed by the database."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.role import RoleCreate, RoleListResponse, RoleResponse, RoleUpdate
from src.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new target role",
)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """Create a new target role and auto-initialize resume + gaps via agent."""
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    role = await role_service.create_role(db, user_id, workspace_id, body)

    # Run agent pipeline to generate capability model, resume skeleton, initial gaps
    try:
        await role_service.initialize_role_assets(
            db, user_id, workspace_id, role.id, body
        )
    except Exception as e:
        # Don't fail role creation if agent pipeline fails
        import logging
        logging.getLogger(__name__).error(f"Agent init failed for role {role.id}: {e}")

    return role


@router.get(
    "",
    response_model=RoleListResponse,
    summary="List all target roles",
)
async def list_roles(
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
) -> RoleListResponse:
    """Return all target roles for the current user."""
    user_id = await get_current_user_id()
    items = await role_service.list_roles(db, user_id, status_filter=status_filter)
    return RoleListResponse(items=items, total=len(items))


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get target role detail",
)
async def get_role(
    role_id: uuid.UUID = Path(..., description="The role UUID"),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """Retrieve a single target role by its ID."""
    user_id = await get_current_user_id()
    role = await role_service.get_role(db, user_id, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.patch(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update a target role",
)
async def update_role(
    body: RoleUpdate,
    role_id: uuid.UUID = Path(..., description="The role UUID"),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """Partially update a target role."""
    user_id = await get_current_user_id()
    role = await role_service.update_role(db, user_id, role_id, body)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a target role",
)
async def delete_role(
    role_id: uuid.UUID = Path(..., description="The role UUID"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a target role (sets deleted_at timestamp)."""
    user_id = await get_current_user_id()
    deleted = await role_service.delete_role(db, user_id, role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
