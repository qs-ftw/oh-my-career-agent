"""Seed script: creates the MVP user and workspace if they do not exist.

Usage:
    python -m scripts.seed
    # or from backend/ root:
    python scripts/seed.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.workspace import Workspace

MVP_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
MVP_WORKSPACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # --- MVP User ---
        stmt = select(User).where(User.id == MVP_USER_ID)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=MVP_USER_ID,
                email="dev@careeragent.dev",
                name="Developer",
            )
            session.add(user)
            print(f"[seed] Created MVP user  id={user.id}  email={user.email}")
        else:
            print(f"[seed] MVP user already exists  id={user.id}")

        # --- MVP Workspace ---
        stmt = select(Workspace).where(Workspace.id == MVP_WORKSPACE_ID)
        result = await session.execute(stmt)
        workspace = result.scalar_one_or_none()

        if workspace is None:
            workspace = Workspace(
                id=MVP_WORKSPACE_ID,
                name="Personal",
                owner_user_id=MVP_USER_ID,
                plan_type="personal",
            )
            session.add(workspace)
            print(f"[seed] Created MVP workspace  id={workspace.id}  name={workspace.name}")
        else:
            print(f"[seed] MVP workspace already exists  id={workspace.id}")

        await session.commit()
        print("[seed] Done.")


if __name__ == "__main__":
    asyncio.run(seed())
