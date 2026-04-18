# Phase 1: 候选人数据建模 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat CandidateProfile + Achievement data model with a structured three-layer hierarchy (CareerProfile → WorkExperience → Project → Achievement), add Markdown export for LLM consumption, and wire up frontend CRUD.

**Architecture:** New DB tables (`career_profiles`, `work_experiences`, `projects`) with the refactored `achievements` table linking into the hierarchy. A `CareerMarkdownService` exports structured DB data as career-ops-style Markdown for LLM pipelines. Frontend gets a new Career page with tabbed sections for profile, work experiences, projects, and achievements.

**Tech Stack:** SQLAlchemy 2.0 (async), Pydantic v2, Alembic, FastAPI, React 19, TanStack Query, Tailwind CSS

---

### Task 1: Create CareerProfile ORM model

**Files:**
- Modify: `backend/src/models/profile.py`

Replace the existing `CandidateProfile` with `CareerProfile`.

- [ ] **Step 1: Rewrite `backend/src/models/profile.py`**

```python
"""CareerProfile model — canonical structured career data."""

import uuid

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class CareerProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = "career_profiles"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    headline: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    portfolio_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    github_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    professional_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skill_categories: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
```

- [ ] **Step 2: Update `backend/src/models/__init__.py`**

Replace the `CandidateProfile` import with `CareerProfile`:

```python
from src.models.profile import CareerProfile
```

Update `__all__` to replace `"CandidateProfile"` with `"CareerProfile"`.

- [ ] **Step 3: Commit**

```bash
git add backend/src/models/profile.py backend/src/models/__init__.py
git commit -m "feat(models): replace CandidateProfile with CareerProfile"
```

---

### Task 2: Create WorkExperience ORM model

**Files:**
- Create: `backend/src/models/work_experience.py`

- [ ] **Step 1: Create `backend/src/models/work_experience.py`**

```python
"""WorkExperience model — a role at a company."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class WorkExperience(IDMixin, TimestampMixin, Base):
    __tablename__ = "work_experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

- [ ] **Step 2: Register in `backend/src/models/__init__.py`**

Add import and `__all__` entry:

```python
from src.models.work_experience import WorkExperience
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/models/work_experience.py backend/src/models/__init__.py
git commit -m "feat(models): add WorkExperience model"
```

---

### Task 3: Create Project ORM model

**Files:**
- Create: `backend/src/models/project.py`

- [ ] **Step 1: Create `backend/src/models/project.py`**

```python
"""Project model — a project within a work experience or standalone."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class Project(IDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    work_experience_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_experiences.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tech_stack: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

- [ ] **Step 2: Register in `backend/src/models/__init__.py`**

```python
from src.models.project import Project
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/models/project.py backend/src/models/__init__.py
git commit -m "feat(models): add Project model"
```

---

### Task 4: Refactor Achievement ORM model

**Files:**
- Modify: `backend/src/models/achievement.py`

- [ ] **Step 1: Rewrite `backend/src/models/achievement.py`**

Keep `AchievementRoleMatch` and `AchievementResumeLink` unchanged. Replace the `Achievement` class:

```python
"""Achievement, AchievementRoleMatch, and AchievementResumeLink models."""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IDMixin, TimestampMixin


class Achievement(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievements"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    work_experience_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_experiences.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="raw")
    date_occurred: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)


# AchievementRoleMatch and AchievementResumeLink stay the same —
# but update their FK to reference the new achievements table by name
# (table name "achievements" does not change, so no FK breakage).


class AchievementRoleMatch(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievement_role_matches"

    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False, index=True,
    )
    target_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_roles.id"), nullable=False, index=True,
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class AchievementResumeLink(IDMixin, TimestampMixin, Base):
    __tablename__ = "achievement_resume_links"

    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False, index=True,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True,
    )
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id"), nullable=True, default=None,
    )
    applied_section: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    applied_mode: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/models/achievement.py
git commit -m "feat(models): refactor Achievement with project/work_experience links and parsed_data"
```

---

### Task 5: Create Pydantic schemas for new models

**Files:**
- Modify: `backend/src/schemas/profile.py`
- Create: `backend/src/schemas/work_experience.py`
- Create: `backend/src/schemas/project.py`
- Modify: `backend/src/schemas/achievement.py`

- [ ] **Step 1: Rewrite `backend/src/schemas/profile.py`**

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CareerProfileUpsert(BaseModel):
    """Request body for creating or updating a career profile."""
    name: str = Field(default="", max_length=100)
    headline: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=50)
    linkedin_url: str = Field(default="", max_length=500)
    portfolio_url: str = Field(default="", max_length=500)
    github_url: str = Field(default="", max_length=500)
    location: str = Field(default="", max_length=100)
    professional_summary: str = Field(default="")
    skill_categories: dict[str, list[str]] = Field(default_factory=dict)


class CareerProfileResponse(BaseModel):
    """Full career profile returned by the API."""
    id: UUID
    name: str
    headline: str
    email: str
    phone: str
    linkedin_url: str
    portfolio_url: str
    github_url: str
    location: str
    professional_summary: str
    skill_categories: dict[str, list[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileCompletenessResponse(BaseModel):
    """Profile completeness metrics."""
    total_fields: int
    filled_fields: int
    completeness_pct: float
    missing_high_value: list[str]
```

- [ ] **Step 2: Create `backend/src/schemas/work_experience.py`**

```python
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkExperienceCreate(BaseModel):
    """Request body for creating a work experience."""
    company_name: str = Field(..., min_length=1, max_length=200)
    company_url: str = Field(default="", max_length=500)
    location: str = Field(default="", max_length=100)
    role_title: str = Field(..., min_length=1, max_length=200)
    start_date: date
    end_date: date | None = None
    description: str = Field(default="")
    sort_order: int = Field(default=0)


class WorkExperienceUpdate(BaseModel):
    """Request body for updating a work experience. All fields optional."""
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    role_title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    sort_order: int | None = None


class WorkExperienceResponse(BaseModel):
    """Full work experience returned by the API."""
    id: UUID
    profile_id: UUID
    company_name: str
    company_url: str
    location: str
    role_title: str
    start_date: date
    end_date: date | None
    description: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Create `backend/src/schemas/project.py`**

```python
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request body for creating a project."""
    work_experience_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    tech_stack: list[str] = Field(default_factory=list)
    url: str = Field(default="", max_length=500)
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int = Field(default=0)


class ProjectUpdate(BaseModel):
    """Request body for updating a project. All fields optional."""
    work_experience_id: UUID | None = None
    name: str | None = None
    description: str | None = None
    tech_stack: list[str] | None = None
    url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int | None = None


class ProjectResponse(BaseModel):
    """Full project returned by the API."""
    id: UUID
    profile_id: UUID
    work_experience_id: UUID | None
    name: str
    description: str
    tech_stack: list[str]
    url: str
    start_date: date | None
    end_date: date | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Rewrite `backend/src/schemas/achievement.py`**

```python
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AchievementCreate(BaseModel):
    """Request body for creating a new achievement."""
    project_id: UUID | None = None
    work_experience_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=512)
    raw_content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    source_type: str = Field(default="manual", max_length=50)
    date_occurred: date | None = None


class AchievementResponse(BaseModel):
    """Full achievement detail returned by the API."""
    id: UUID
    profile_id: UUID
    project_id: UUID | None = None
    work_experience_id: UUID | None = None
    title: str
    raw_content: str
    parsed_data: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
    importance_score: float = 0.0
    source_type: str = "manual"
    status: str = "raw"
    date_occurred: date | None = None
    analysis_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AchievementAnalysisRequest(BaseModel):
    """Request to trigger AI analysis on an achievement."""
    achievement_id: UUID
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/schemas/profile.py backend/src/schemas/work_experience.py backend/src/schemas/project.py backend/src/schemas/achievement.py
git commit -m "feat(schemas): add Pydantic schemas for CareerProfile, WorkExperience, Project, and refactored Achievement"
```

---

### Task 6: Update service layer — career profile

**Files:**
- Modify: `backend/src/services/profile_service.py`

- [ ] **Step 1: Rewrite `backend/src/services/profile_service.py`**

```python
"""Database-backed service for career profile operations."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.profile import CareerProfile
from src.schemas.profile import (
    CareerProfileResponse,
    CareerProfileUpsert,
    ProfileCompletenessResponse,
)

logger = logging.getLogger(__name__)


def _to_response(p: CareerProfile) -> CareerProfileResponse:
    return CareerProfileResponse(
        id=p.id,
        name=p.name,
        headline=p.headline,
        email=p.email,
        phone=p.phone,
        linkedin_url=p.linkedin_url,
        portfolio_url=p.portfolio_url,
        github_url=p.github_url,
        location=p.location,
        professional_summary=p.professional_summary,
        skill_categories=p.skill_categories or {},
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


async def get_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> CareerProfileResponse | None:
    stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return None
    return _to_response(profile)


async def upsert_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: CareerProfileUpsert,
) -> CareerProfileResponse:
    stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CareerProfile(
            workspace_id=workspace_id,
            user_id=user_id,
        )
        session.add(profile)

    profile.name = data.name
    profile.headline = data.headline
    profile.email = data.email
    profile.phone = data.phone
    profile.linkedin_url = data.linkedin_url
    profile.portfolio_url = data.portfolio_url
    profile.github_url = data.github_url
    profile.location = data.location
    profile.professional_summary = data.professional_summary
    profile.skill_categories = data.skill_categories

    await session.flush()
    await session.refresh(profile)
    return _to_response(profile)


async def get_completeness(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> ProfileCompletenessResponse:
    profile_resp = await get_profile(session, user_id, workspace_id)

    if profile_resp is None:
        return ProfileCompletenessResponse(
            total_fields=6,
            filled_fields=0,
            completeness_pct=0.0,
            missing_high_value=["name", "headline", "email", "professional_summary", "skill_categories", "location"],
        )

    fields = {
        "name": bool(profile_resp.name),
        "headline": bool(profile_resp.headline),
        "email": bool(profile_resp.email),
        "professional_summary": bool(profile_resp.professional_summary),
        "skill_categories": bool(profile_resp.skill_categories),
        "location": bool(profile_resp.location),
    }

    filled = sum(1 for v in fields.values() if v)
    total = len(fields)
    missing = [k for k, v in fields.items() if not v]

    return ProfileCompletenessResponse(
        total_fields=total,
        filled_fields=filled,
        completeness_pct=round(filled / total * 100, 1),
        missing_high_value=missing,
    )


async def get_profile_context(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> dict:
    """Load profile as a dict for agent state injection."""
    stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        return {}

    return {
        "name": profile.name,
        "headline": profile.headline,
        "email": profile.email,
        "phone": profile.phone,
        "linkedin_url": profile.linkedin_url,
        "portfolio_url": profile.portfolio_url,
        "github_url": profile.github_url,
        "location": profile.location,
        "professional_summary": profile.professional_summary,
        "skill_categories": profile.skill_categories or {},
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/services/profile_service.py
git commit -m "feat(services): update profile_service for new CareerProfile model"
```

---

### Task 7: Create service layer — work experiences and projects

**Files:**
- Create: `backend/src/services/work_experience_service.py`
- Create: `backend/src/services/project_service.py`

- [ ] **Step 1: Create `backend/src/services/work_experience_service.py`**

```python
"""Database-backed service for work experience CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.work_experience import WorkExperience
from src.schemas.work_experience import (
    WorkExperienceCreate,
    WorkExperienceResponse,
    WorkExperienceUpdate,
)


def _to_response(w: WorkExperience) -> WorkExperienceResponse:
    return WorkExperienceResponse(
        id=w.id,
        profile_id=w.profile_id,
        company_name=w.company_name,
        company_url=w.company_url,
        location=w.location,
        role_title=w.role_title,
        start_date=w.start_date,
        end_date=w.end_date,
        description=w.description,
        sort_order=w.sort_order,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


async def list_by_profile(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> list[WorkExperienceResponse]:
    stmt = (
        select(WorkExperience)
        .where(WorkExperience.profile_id == profile_id)
        .order_by(WorkExperience.sort_order, WorkExperience.start_date.desc())
    )
    result = await session.execute(stmt)
    return [_to_response(w) for w in result.scalars().all()]


async def create(
    session: AsyncSession,
    profile_id: uuid.UUID,
    data: WorkExperienceCreate,
) -> WorkExperienceResponse:
    exp = WorkExperience(profile_id=profile_id, **data.model_dump())
    session.add(exp)
    await session.flush()
    await session.refresh(exp)
    return _to_response(exp)


async def update(
    session: AsyncSession,
    experience_id: uuid.UUID,
    data: WorkExperienceUpdate,
) -> WorkExperienceResponse | None:
    stmt = select(WorkExperience).where(WorkExperience.id == experience_id)
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()
    if exp is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(exp, field, value)
    await session.flush()
    await session.refresh(exp)
    return _to_response(exp)


async def delete(
    session: AsyncSession,
    experience_id: uuid.UUID,
) -> bool:
    stmt = select(WorkExperience).where(WorkExperience.id == experience_id)
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()
    if exp is None:
        return False
    await session.delete(exp)
    await session.flush()
    return True
```

- [ ] **Step 2: Create `backend/src/services/project_service.py`**

```python
"""Database-backed service for project CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


def _to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        profile_id=p.profile_id,
        work_experience_id=p.work_experience_id,
        name=p.name,
        description=p.description,
        tech_stack=p.tech_stack or [],
        url=p.url,
        start_date=p.start_date,
        end_date=p.end_date,
        sort_order=p.sort_order,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


async def list_by_profile(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> list[ProjectResponse]:
    stmt = (
        select(Project)
        .where(Project.profile_id == profile_id)
        .order_by(Project.sort_order, Project.created_at.desc())
    )
    result = await session.execute(stmt)
    return [_to_response(p) for p in result.scalars().all()]


async def create(
    session: AsyncSession,
    profile_id: uuid.UUID,
    data: ProjectCreate,
) -> ProjectResponse:
    proj = Project(profile_id=profile_id, **data.model_dump())
    session.add(proj)
    await session.flush()
    await session.refresh(proj)
    return _to_response(proj)


async def update(
    session: AsyncSession,
    project_id: uuid.UUID,
    data: ProjectUpdate,
) -> ProjectResponse | None:
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    proj = result.scalar_one_or_none()
    if proj is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(proj, field, value)
    await session.flush()
    await session.refresh(proj)
    return _to_response(proj)


async def delete(
    session: AsyncSession,
    project_id: uuid.UUID,
) -> bool:
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    proj = result.scalar_one_or_none()
    if proj is None:
        return False
    await session.delete(proj)
    await session.flush()
    return True
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/services/work_experience_service.py backend/src/services/project_service.py
git commit -m "feat(services): add work_experience and project CRUD services"
```

---

### Task 8: Update achievement service for new model

**Files:**
- Modify: `backend/src/services/achievement_service.py`

- [ ] **Step 1: Update `_to_response` and `create_achievement` in achievement_service.py**

The `_to_response` function needs to map the new Achievement fields. The `create_achievement` needs to accept `project_id`, `work_experience_id`, `date_occurred`, and auto-resolve `profile_id`.

Update the imports at the top to include `CareerProfile`:

```python
from src.models.profile import CareerProfile
```

Update `_to_response`:

```python
def _to_response(a: Achievement, analysis_error: str | None = None) -> AchievementResponse:
    parsed = a.parsed_data or {}
    return AchievementResponse(
        id=a.id,
        profile_id=a.profile_id,
        project_id=a.project_id,
        work_experience_id=a.work_experience_id,
        title=a.title,
        raw_content=a.raw_content or "",
        parsed_data=a.parsed_data,
        tags=a.tags if isinstance(a.tags, list) else [],
        importance_score=a.importance_score,
        source_type=a.source_type,
        status=a.status,
        date_occurred=a.date_occurred,
        analysis_error=analysis_error,
        created_at=a.created_at,
    )
```

Update `create_achievement` to accept `AchievementCreate` (which now has `project_id`, `work_experience_id`, `date_occurred`), and auto-resolve `profile_id` from the user's `CareerProfile`:

```python
async def create_achievement(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: AchievementCreate,
) -> AchievementResponse:
    # Resolve profile_id — auto-create profile if missing
    profile_stmt = select(CareerProfile).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    profile_result = await session.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()

    if profile is None:
        profile = CareerProfile(workspace_id=workspace_id, user_id=user_id)
        session.add(profile)
        await session.flush()

    achievement = Achievement(
        profile_id=profile.id,
        project_id=data.project_id,
        work_experience_id=data.work_experience_id,
        title=data.title,
        raw_content=data.raw_content,
        tags=data.tags or [],
        source_type=data.source_type,
        date_occurred=data.date_occurred,
    )
    session.add(achievement)
    await session.flush()
    await session.refresh(achievement)
    return _to_response(achievement)
```

Also update the analysis pipeline result handling in `run_achievement_pipeline` — where it writes parsed results to the Achievement row, change from the old `_json` fields to `parsed_data`:

```python
# Where the pipeline writes back parsed results:
achievement.parsed_data = pipeline_result.get("achievement_parsed")
achievement.importance_score = (
    (pipeline_result.get("achievement_parsed") or {}).get("importance_score", 0.0)
)
achievement.status = "analyzed"
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/services/achievement_service.py
git commit -m "feat(services): update achievement_service for new data model"
```

---

### Task 9: Create CareerMarkdownService

**Files:**
- Create: `backend/src/services/career_markdown_service.py`

- [ ] **Step 1: Create `backend/src/services/career_markdown_service.py`**

```python
"""Export structured career data as Markdown for LLM consumption."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.achievement import Achievement
from src.models.profile import CareerProfile
from src.models.project import Project
from src.models.work_experience import WorkExperience

logger = logging.getLogger(__name__)


async def export_markdown(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> str:
    """Export career profile as career-ops-style Markdown.

    Structure:
    # CV -- Name
    ## Contact Info
    ## Professional Summary
    ## Work Experience
    ### Company -- Location
    **Role** | Dates
    **Project Name**
    - Achievement bullet
    ## Projects
    ## Skills
    """
    # Load profile
    profile_stmt = select(CareerProfile).where(CareerProfile.id == profile_id)
    result = await session.execute(profile_stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return ""

    sections: list[str] = []

    # Header
    name = profile.name or "Candidate"
    sections.append(f"# CV -- {name}\n")

    # Contact
    contact_parts = []
    if profile.location:
        contact_parts.append(profile.location)
    if profile.email:
        contact_parts.append(profile.email)
    if profile.linkedin_url:
        contact_parts.append(f"[LinkedIn]({profile.linkedin_url})")
    if profile.github_url:
        contact_parts.append(f"[GitHub]({profile.github_url})")
    if profile.portfolio_url:
        contact_parts.append(f"[Portfolio]({profile.portfolio_url})")
    if contact_parts:
        sections.append(f"\n## Contact Info\n{' | '.join(contact_parts)}\n")

    # Professional Summary
    if profile.professional_summary:
        sections.append(f"\n## Professional Summary\n{profile.professional_summary}\n")

    # Work Experience
    exp_stmt = (
        select(WorkExperience)
        .where(WorkExperience.profile_id == profile_id)
        .order_by(WorkExperience.sort_order, WorkExperience.start_date.desc())
    )
    exp_result = await session.execute(exp_stmt)
    experiences = list(exp_result.scalars().all())

    if experiences:
        sections.append("\n## Work Experience")
        for exp in experiences:
            end_str = exp.end_date.isoformat() if exp.end_date else "Present"
            sections.append(f"\n### {exp.company_name} -- {exp.location}")
            sections.append(f"**{exp.role_title}** | {exp.start_date.isoformat()} - {end_str}")

            if exp.description:
                sections.append(f"\n{exp.description}")

            # Load projects for this work experience
            proj_stmt = (
                select(Project)
                .where(
                    Project.work_experience_id == exp.id,
                    Project.profile_id == profile_id,
                )
                .order_by(Project.sort_order)
            )
            proj_result = await session.execute(proj_stmt)
            projects = list(proj_result.scalars().all())

            for proj in projects:
                sections.append(f"\n**{proj.name}**")
                if proj.description:
                    sections.append(f"{proj.description}")
                if proj.tech_stack:
                    sections.append(f"技术栈: {', '.join(proj.tech_stack)}")

                # Load achievements for this project
                ach_stmt = (
                    select(Achievement)
                    .where(Achievement.project_id == proj.id)
                    .order_by(Achievement.importance_score.desc())
                )
                ach_result = await session.execute(ach_stmt)
                for ach in ach_result.scalars().all():
                    bullet = _achievement_bullet(ach)
                    if bullet:
                        sections.append(f"- {bullet}")

            # Achievements directly under this work experience (no project)
            direct_ach_stmt = (
                select(Achievement)
                .where(
                    Achievement.work_experience_id == exp.id,
                    Achievement.project_id.is_(None),
                )
                .order_by(Achievement.importance_score.desc())
            )
            direct_ach_result = await session.execute(direct_ach_stmt)
            for ach in direct_ach_result.scalars().all():
                bullet = _achievement_bullet(ach)
                if bullet:
                    sections.append(f"- {bullet}")

    # Standalone Projects (not linked to work experience)
    standalone_proj_stmt = (
        select(Project)
        .where(
            Project.profile_id == profile_id,
            Project.work_experience_id.is_(None),
        )
        .order_by(Project.sort_order)
    )
    standalone_result = await session.execute(standalone_proj_stmt)
    standalone_projects = list(standalone_result.scalars().all())

    if standalone_projects:
        sections.append("\n## Projects")
        for proj in standalone_projects:
            line = f"- **{proj.name}**"
            if proj.tech_stack:
                line += f" | {', '.join(proj.tech_stack)}"
            sections.append(line)
            if proj.description:
                sections.append(f"  {proj.description}")

            ach_stmt = (
                select(Achievement)
                .where(Achievement.project_id == proj.id)
                .order_by(Achievement.importance_score.desc())
            )
            ach_result = await session.execute(ach_stmt)
            for ach in ach_result.scalars().all():
                bullet = _achievement_bullet(ach)
                if bullet:
                    sections.append(f"  - {bullet}")

    # Standalone Achievements (not linked to project or work experience)
    free_ach_stmt = (
        select(Achievement)
        .where(
            Achievement.profile_id == profile_id,
            Achievement.project_id.is_(None),
            Achievement.work_experience_id.is_(None),
        )
        .order_by(Achievement.importance_score.desc())
    )
    free_ach_result = await session.execute(free_ach_stmt)
    free_achievements = list(free_ach_result.scalars().all())

    if free_achievements:
        sections.append("\n## Key Achievements")
        for ach in free_achievements:
            bullet = _achievement_bullet(ach)
            if bullet:
                sections.append(f"- {bullet}")

    # Skills
    skill_categories = profile.skill_categories or {}
    if skill_categories:
        sections.append("\n## Skills")
        for category, skills in skill_categories.items():
            sections.append(f"- **{category}:** {', '.join(skills)}")

    return "\n".join(sections) + "\n"


def _achievement_bullet(ach: Achievement) -> str:
    """Format an achievement as a single bullet point."""
    if ach.parsed_data and ach.parsed_data.get("summary"):
        return ach.parsed_data["summary"]
    return ach.title
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/services/career_markdown_service.py
git commit -m "feat(services): add CareerMarkdownService for LLM-friendly export"
```

---

### Task 10: Update API routes

**Files:**
- Modify: `backend/src/api/profile.py`
- Create: `backend/src/api/work_experiences.py`
- Create: `backend/src/api/projects.py`
- Modify: `backend/src/api/router.py`

- [ ] **Step 1: Update `backend/src/api/profile.py`**

Update imports to use new schema names (`CareerProfileResponse`, `CareerProfileUpsert`):

```python
"""Career profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.schemas.profile import (
    CareerProfileResponse,
    CareerProfileUpsert,
    ProfileCompletenessResponse,
)
from src.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "",
    response_model=CareerProfileResponse | None,
    summary="Get career profile",
)
async def get_profile(
    db: AsyncSession = Depends(get_db),
) -> CareerProfileResponse | None:
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.get_profile(db, user_id, workspace_id)


@router.put(
    "",
    response_model=CareerProfileResponse,
    summary="Create or update career profile",
)
async def upsert_profile(
    body: CareerProfileUpsert,
    db: AsyncSession = Depends(get_db),
) -> CareerProfileResponse:
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.upsert_profile(db, user_id, workspace_id, body)


@router.get(
    "/completeness",
    response_model=ProfileCompletenessResponse,
    summary="Get profile completeness metrics",
)
async def get_completeness(
    db: AsyncSession = Depends(get_db),
) -> ProfileCompletenessResponse:
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    return await profile_service.get_completeness(db, user_id, workspace_id)
```

- [ ] **Step 2: Create `backend/src/api/work_experiences.py`**

```python
"""Work experience endpoints — CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.models.profile import CareerProfile
from src.schemas.work_experience import (
    WorkExperienceCreate,
    WorkExperienceResponse,
    WorkExperienceUpdate,
)
from src.services import work_experience_service

router = APIRouter(prefix="/work-experiences", tags=["work-experiences"])


async def _resolve_profile_id(db: AsyncSession, user_id: uuid.UUID, workspace_id: uuid.UUID) -> uuid.UUID:
    stmt = select(CareerProfile.id).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await db.execute(stmt)
    profile_id = result.scalar_one_or_none()
    if profile_id is None:
        raise HTTPException(status_code=404, detail="Career profile not found. Create one first.")
    return profile_id


@router.get("", response_model=list[WorkExperienceResponse])
async def list_work_experiences(db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    profile_id = await _resolve_profile_id(db, user_id, workspace_id)
    return await work_experience_service.list_by_profile(db, profile_id)


@router.post("", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_work_experience(
    body: WorkExperienceCreate,
    db: AsyncSession = Depends(get_db),
):
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    profile_id = await _resolve_profile_id(db, user_id, workspace_id)
    return await work_experience_service.create(db, profile_id, body)


@router.patch("/{experience_id}", response_model=WorkExperienceResponse)
async def update_work_experience(
    experience_id: uuid.UUID = Path(...),
    body: WorkExperienceUpdate = ...,
    db: AsyncSession = Depends(get_db),
):
    result = await work_experience_service.update(db, experience_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Work experience not found")
    return result


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_experience(
    experience_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
):
    deleted = await work_experience_service.delete(db, experience_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Work experience not found")
```

- [ ] **Step 3: Create `backend/src/api/projects.py`**

```python
"""Project endpoints — CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user_id, get_current_workspace_id
from src.models.profile import CareerProfile
from src.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from src.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


async def _resolve_profile_id(db: AsyncSession, user_id: uuid.UUID, workspace_id: uuid.UUID) -> uuid.UUID:
    stmt = select(CareerProfile.id).where(
        CareerProfile.user_id == user_id,
        CareerProfile.workspace_id == workspace_id,
    )
    result = await db.execute(stmt)
    profile_id = result.scalar_one_or_none()
    if profile_id is None:
        raise HTTPException(status_code=404, detail="Career profile not found. Create one first.")
    return profile_id


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    profile_id = await _resolve_profile_id(db, user_id, workspace_id)
    return await project_service.list_by_profile(db, profile_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    user_id = await get_current_user_id()
    workspace_id = await get_current_workspace_id()
    profile_id = await _resolve_profile_id(db, user_id, workspace_id)
    return await project_service.create(db, profile_id, body)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID = Path(...),
    body: ProjectUpdate = ...,
    db: AsyncSession = Depends(get_db),
):
    result = await project_service.update(db, project_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db),
):
    deleted = await project_service.delete(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
```

- [ ] **Step 4: Update `backend/src/api/router.py`**

Add the new routers:

```python
from src.api import work_experiences, projects
# ...existing imports...

api_router.include_router(work_experiences.router)
api_router.include_router(projects.router)
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/profile.py backend/src/api/work_experiences.py backend/src/api/projects.py backend/src/api/router.py
git commit -m "feat(api): add CRUD endpoints for work experiences and projects, update profile routes"
```

---

### Task 11: Update career_assets assembly in role_service

**Files:**
- Modify: `backend/src/services/role_service.py`

- [ ] **Step 1: Update career_assets loading to use new models**

In the `initialize_role_assets` function (and any other place that builds `career_assets`), replace the old Achievement loading with the `CareerMarkdownService`:

```python
# At the top, add import:
from src.services.career_markdown_service import export_markdown

# Replace the old achievement-loading block with:
# Load career profile
profile_stmt = select(CareerProfile).where(
    CareerProfile.user_id == user_id,
    CareerProfile.workspace_id == workspace_id,
)
profile_result = await session.execute(profile_stmt)
profile = profile_result.scalar_one_or_none()

if profile:
    career_md = await export_markdown(session, profile.id)
    career_assets = {"cv_markdown": career_md}
else:
    career_assets = {"cv_markdown": ""}
```

Also update the `agent_input` dict to pass `career_assets` with the new Markdown format.

- [ ] **Step 2: Commit**

```bash
git add backend/src/services/role_service.py
git commit -m "feat(services): update career_assets assembly to use CareerMarkdownService"
```

---

### Task 12: Generate Alembic migration and clean up DB

**Files:**
- Generate: `backend/alembic/versions/xxx_career_data_model.py`

- [ ] **Step 1: Generate migration**

```bash
cd backend
alembic revision --autogenerate -m "career_data_model_restructure"
```

- [ ] **Step 2: Review the generated migration**

Open the generated file and verify it includes:
- DROP TABLE `candidate_profiles` (if exists)
- CREATE TABLE `career_profiles`
- CREATE TABLE `work_experiences`
- CREATE TABLE `projects`
- DROP + CREATE TABLE `achievements` (or ALTER to match new schema)

If the autogenerate misses the DROP for the old table, add it manually:

```python
def upgrade():
    op.drop_table("candidate_profiles", if_exists=True)
    op.drop_table("achievements", if_exists=True)
    # ... rest of autogenerate output for CREATE TABLEs
```

- [ ] **Step 3: Run migration**

```bash
alembic upgrade head
```

- [ ] **Step 4: Verify tables**

```bash
python -c "from src.core.database import async_engine; import asyncio; from sqlalchemy import inspect; asyncio.run(inspect(async_engine).get_table_names())"
```

Or simply start the backend and check it boots without errors.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/
git commit -m "feat(db): add migration for career data model restructure"
```

---

### Task 13: Update frontend TypeScript types

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add new types to `frontend/src/types/index.ts`**

Add these interfaces:

```typescript
export interface CareerProfile {
  id: string;
  name: string;
  headline: string;
  email: string;
  phone: string;
  linkedin_url: string;
  portfolio_url: string;
  github_url: string;
  location: string;
  professional_summary: string;
  skill_categories: Record<string, string[]>;
  created_at: string;
  updated_at: string;
}

export interface WorkExperience {
  id: string;
  profile_id: string;
  company_name: string;
  company_url: string;
  location: string;
  role_title: string;
  start_date: string;
  end_date: string | null;
  description: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  profile_id: string;
  work_experience_id: string | null;
  name: string;
  description: string;
  tech_stack: string[];
  url: string;
  start_date: string | null;
  end_date: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}
```

Update the `Achievement` interface:

```typescript
export interface Achievement {
  id: string;
  profile_id: string;
  project_id: string | null;
  work_experience_id: string | null;
  title: string;
  raw_content: string;
  parsed_data: Record<string, unknown> | null;
  tags: string[];
  importance_score: number;
  source_type: string;
  status: "raw" | "analyzed" | "applied";
  date_occurred: string | null;
  analysis_error?: string;
  created_at: string;
}
```

Remove or keep the old `CandidateProfile` type if other code still references it — but all references should be updated to `CareerProfile`.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(types): add CareerProfile, WorkExperience, Project types and update Achievement"
```

---

### Task 14: Update frontend API client and hooks

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/hooks/useProfile.ts`
- Create: `frontend/src/hooks/useWorkExperiences.ts`
- Create: `frontend/src/hooks/useProjects.ts`
- Modify: `frontend/src/hooks/useAchievements.ts`

- [ ] **Step 1: Update `frontend/src/lib/api.ts`**

Update `profileApi` and add new API modules:

```typescript
export const profileApi = {
  get: () => apiClient.get("/profile"),
  upsert: (data: unknown) => apiClient.put("/profile", data),
  completeness: () => apiClient.get("/profile/completeness"),
};

export const workExperienceApi = {
  list: () => apiClient.get("/work-experiences"),
  create: (data: unknown) => apiClient.post("/work-experiences", data),
  update: (id: string, data: unknown) => apiClient.patch(`/work-experiences/${id}`, data),
  delete: (id: string) => apiClient.delete(`/work-experiences/${id}`),
};

export const projectApi = {
  list: () => apiClient.get("/projects"),
  create: (data: unknown) => apiClient.post("/projects", data),
  update: (id: string, data: unknown) => apiClient.patch(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
};
```

- [ ] **Step 2: Update `frontend/src/hooks/useProfile.ts`**

Update to use `CareerProfile` type:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";
import type { CareerProfile, ProfileCompleteness } from "@/types";

export function useProfile() {
  return useQuery<CareerProfile | null>({
    queryKey: ["profile"],
    queryFn: async () => {
      const { data } = await profileApi.get();
      return data;
    },
  });
}

export function useProfileCompleteness() {
  return useQuery<ProfileCompleteness>({
    queryKey: ["profile", "completeness"],
    queryFn: async () => {
      const { data } = await profileApi.completeness();
      return data;
    },
  });
}

export function useUpsertProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await profileApi.upsert(data);
      return res.data as CareerProfile;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });
}
```

- [ ] **Step 3: Create `frontend/src/hooks/useWorkExperiences.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workExperienceApi } from "@/lib/api";
import type { WorkExperience } from "@/types";

export function useWorkExperiences() {
  return useQuery<WorkExperience[]>({
    queryKey: ["workExperiences"],
    queryFn: async () => {
      const { data } = await workExperienceApi.list();
      return data;
    },
  });
}

export function useCreateWorkExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await workExperienceApi.create(data);
      return res.data as WorkExperience;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
    },
  });
}

export function useUpdateWorkExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await workExperienceApi.update(id, data);
      return res.data as WorkExperience;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
    },
  });
}

export function useDeleteWorkExperience() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await workExperienceApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workExperiences"] });
    },
  });
}
```

- [ ] **Step 4: Create `frontend/src/hooks/useProjects.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectApi } from "@/lib/api";
import type { Project } from "@/types";

export function useProjects() {
  return useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: async () => {
      const { data } = await projectApi.list();
      return data;
    },
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await projectApi.create(data);
      return res.data as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const res = await projectApi.update(id, data);
      return res.data as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await projectApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
```

- [ ] **Step 5: Update `frontend/src/hooks/useAchievements.ts`**

Update to use the new `Achievement` type (remove old fields like `parsed_summary`, `technical_points`, etc. — they're now inside `parsed_data`).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/useProfile.ts frontend/src/hooks/useWorkExperiences.ts frontend/src/hooks/useProjects.ts frontend/src/hooks/useAchievements.ts
git commit -m "feat(frontend): add API client and hooks for work experiences and projects"
```

---

### Task 15: Update frontend Profile page and create Career page

**Files:**
- Modify: `frontend/src/pages/Profile.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update `frontend/src/pages/Profile.tsx`**

The Profile page already handles contact info and headline. Update it to:
1. Use `CareerProfile` type instead of `CandidateProfile`
2. Add `name` and `professional_summary` fields
3. Add `skill_categories` management (key-value pairs of category → skills)
4. Remove `exit_story`, `superpowers`, `proof_points`, `compensation`, `preferences`, `constraints` (these were from the old model)

The page should have these sections:
- Name
- Headline
- Professional Summary (textarea)
- Contact Info (email, phone, linkedin, github, portfolio, location — keep existing)
- Skill Categories (add category → add skills under it)

Below the profile form, add a section for Work Experiences with add/edit/delete, and a section for Projects with add/edit/delete. Use a tab or accordion pattern.

This is a large UI change — implement it as follows:

**Profile form section** — reuse existing form pattern with the new fields.

**Work Experience section** — card-based list with "Add" button. Each card shows company, role, dates, and has edit/delete. Add form is a modal or inline expandable form.

**Project section** — same card-based pattern. Projects can optionally be linked to a work experience (dropdown select).

Keep it functional — Tailwind CSS classes matching the existing patterns (border, rounded-md, px-3 py-2, etc.).

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Profile.tsx
git commit -m "feat(frontend): update Profile page for new CareerProfile model with work experiences and projects"
```

---

### Task 16: Update Achievements page for new data model

**Files:**
- Modify: `frontend/src/pages/Achievements.tsx`

- [ ] **Step 1: Update achievement rendering to use `parsed_data`**

Replace all references to the old flat fields (`parsed_summary`, `technical_points`, `challenges`, `solutions`, `metrics`, `interview_points`) with `parsed_data`:

```typescript
const parsed = achievement.parsed_data;
const summary = parsed?.summary ?? "";
const technical_points = (parsed?.technical_points ?? []) as unknown[];
const challenges = (parsed?.challenges ?? []) as unknown[];
const solutions = (parsed?.solutions ?? []) as unknown[];
const metrics = (parsed?.metrics ?? []) as unknown[];
const interview_points = (parsed?.interview_points ?? []) as unknown[];
```

The `itemText()` helper continues to work since it handles both strings and objects.

Also update the create achievement form to optionally select a `project_id` and `work_experience_id` (dropdown from the user's data).

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Achievements.tsx
git commit -m "feat(frontend): update Achievements page to use parsed_data and link to projects/work experiences"
```

---

## Verification

1. **Backend starts**: `cd backend && uvicorn src.main:app --reload` — no import errors
2. **DB tables created**: Check that `career_profiles`, `work_experiences`, `projects`, and new `achievements` tables exist
3. **Profile CRUD**: `curl -X PUT /api/profile -d '{"name":"Test","headline":"Engineer"}'` — returns profile
4. **Work Experience CRUD**: Create, list, update, delete work experiences via API
5. **Project CRUD**: Create, list, update, delete projects via API
6. **Achievement CRUD**: Create achievement with optional `project_id` and `work_experience_id`
7. **Markdown export**: `CareerMarkdownService.export_markdown()` produces valid career-ops-style Markdown
8. **Frontend loads**: `npm run dev` — Profile page renders with new form fields
9. **Frontend CRUD**: Can create/edit/delete work experiences and projects from the Profile page
10. **Achievement pipeline**: Analyzing an achievement still works, results stored in `parsed_data`
