"""Seed script: resets all business data and creates the MVP user + workspace.

Usage:
    python -m scripts.seed
    # or from backend/ root:
    python scripts/seed.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember
from src.models.target_role import TargetRole, RoleCapabilityModel
from src.models.resume import Resume, ResumeVersion
from src.models.achievement import Achievement, AchievementRoleMatch, AchievementResumeLink
from src.models.gap import GapItem
from src.models.skill import SkillEntity
from src.models.jd import JDSnapshot, JDResumeTask
from src.models.agent import AgentRun, UpdateSuggestion

MVP_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
MVP_WORKSPACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def reset_data(session: AsyncSession) -> None:
    """Delete all business data in dependency order (child tables first)."""
    tables_to_clean = [
        UpdateSuggestion,
        AgentRun,
        AchievementResumeLink,
        AchievementRoleMatch,
        Achievement,
        JDResumeTask,
        JDSnapshot,
        GapItem,
        ResumeVersion,
        Resume,
        RoleCapabilityModel,
        TargetRole,
        SkillEntity,
        WorkspaceMember,
        Workspace,
        User,
    ]

    for model in tables_to_clean:
        result = await session.execute(delete(model))
        if result.rowcount:
            print(f"  [reset] Deleted {result.rowcount} rows from {model.__tablename__}")

    await session.flush()


async def seed_user_and_workspace(session: AsyncSession) -> None:
    """Create the MVP user and workspace."""
    user = User(
        id=MVP_USER_ID,
        email="dev@careeragent.dev",
        name="Developer",
    )
    session.add(user)
    print(f"  [seed] Created MVP user  id={user.id}  email={user.email}")

    workspace = Workspace(
        id=MVP_WORKSPACE_ID,
        name="Personal",
        owner_user_id=MVP_USER_ID,
        plan_type="personal",
    )
    session.add(workspace)
    print(f"  [seed] Created MVP workspace  id={workspace.id}  name={workspace.name}")

    member = WorkspaceMember(
        workspace_id=MVP_WORKSPACE_ID,
        user_id=MVP_USER_ID,
        role="owner",
    )
    session.add(member)
    print(f"  [seed] Created workspace membership")

    await session.flush()


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        print("[seed] Resetting all business data...")
        await reset_data(session)

        print("[seed] Creating seed data...")
        await seed_user_and_workspace(session)

        await session.commit()
        print("[seed] Done. Database is clean with MVP user + workspace.")


if __name__ == "__main__":
    asyncio.run(seed())
