"""Export structured career data as Markdown for LLM consumption."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.education import Education
from src.models.profile import CareerProfile
from src.models.project import Project
from src.models.work_experience import WorkExperience

logger = logging.getLogger(__name__)


async def export_markdown(
    session: AsyncSession,
    profile_id: uuid.UUID,
) -> str:
    """Export career profile as career-ops-style Markdown."""
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

    # ── Education ──────────────────────────────────────────
    edu_stmt = (
        select(Education)
        .where(Education.profile_id == profile_id)
        .order_by(Education.sort_order, Education.start_date.desc())
    )
    edu_result = await session.execute(edu_stmt)
    educations = list(edu_result.scalars().all())

    if educations:
        sections.append("\n## Education")
        for edu in educations:
            end_str = edu.end_date.isoformat() if edu.end_date else "Present"
            degree_str = f"{edu.degree} in {edu.field_of_study}" if edu.field_of_study else edu.degree
            sections.append(f"\n### {edu.institution_name} -- {edu.location}")
            sections.append(f"**{degree_str}** | {edu.start_date.isoformat()} - {end_str}")
            if edu.gpa:
                sections.append(f"GPA: {edu.gpa}")
            if edu.description:
                sections.append(f"\n{edu.description}")

            # Load projects for this education
            proj_stmt = (
                select(Project)
                .where(
                    Project.education_id == edu.id,
                    Project.profile_id == profile_id,
                )
                .order_by(Project.sort_order)
            )
            proj_result = await session.execute(proj_stmt)
            edu_projects = list(proj_result.scalars().all())

            for proj in edu_projects:
                sections.append(f"\n**{proj.name}**")
                if proj.description:
                    sections.append(f"{proj.description}")
                if proj.tech_stack:
                    sections.append(f"Tech: {', '.join(proj.tech_stack)}")

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

    # Standalone Projects (not linked to work experience or education)
    standalone_proj_stmt = (
        select(Project)
        .where(
            Project.profile_id == profile_id,
            Project.work_experience_id.is_(None),
            Project.education_id.is_(None),
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
