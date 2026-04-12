"""Target role endpoints — CRUD stubs returning mock data."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.schemas.role import RoleCreate, RoleListResponse, RoleResponse, RoleUpdate
from src.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new target role",
)
async def create_role(body: RoleCreate) -> RoleResponse:
    """Create a new target role with the given parameters."""
    return await role_service.create_role(body)


@router.get(
    "",
    response_model=RoleListResponse,
    summary="List all target roles",
)
async def list_roles(
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status"),
) -> RoleListResponse:
    """Return all target roles for the current user."""
    items = await role_service.list_roles()
    return RoleListResponse(items=items, total=len(items))


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get target role detail",
)
async def get_role(
    role_id: uuid.UUID = Path(..., description="The role UUID"),
) -> RoleResponse:
    """Retrieve a single target role by its ID."""
    role = await role_service.get_role(role_id)
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
) -> RoleResponse:
    """Partially update a target role."""
    role = await role_service.update_role(role_id, body)
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
) -> None:
    """Soft-delete a target role (sets deleted_at timestamp)."""
    await role_service.delete_role(role_id)
