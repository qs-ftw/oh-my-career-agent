"""Stub service for JD (job description) operations."""

from __future__ import annotations

import uuid

from src.schemas.jd import JDParsedResponse, JDTailorResponse
from src.schemas.resume import ResumeContent


async def parse_jd(raw_jd: str) -> JDParsedResponse:
    """Parse raw JD text into structured data (stub)."""
    return JDParsedResponse(
        role_name="Senior Backend Engineer",
        keywords=["distributed systems", "microservices", " observability"],
        required_skills=["Go", "PostgreSQL", "gRPC", "Docker"],
        bonus_items=["Kubernetes", "Terraform", "CI/CD"],
        style={"tone": "formal", "length": "medium"},
    )


async def tailor_jd(
    raw_jd: str,
    mode: str,
    base_resume_id: uuid.UUID | None = None,
) -> JDTailorResponse:
    """Generate a tailored resume for a given JD (stub)."""
    return JDTailorResponse(
        resume=ResumeContent(
            summary="Senior backend engineer with deep distributed systems expertise.",
            skills=[{"category": "Languages", "items": ["Go", "Python"]}],
            experiences=[],
            projects=[],
            highlights=[],
            metrics=[],
            interview_points=[],
        ),
        ability_match_score=0.78,
        resume_match_score=0.72,
        readiness_score=0.75,
        recommendation="Strong candidate. Consider highlighting gRPC and observability experience.",
        missing_items=["Terraform", "CI/CD pipeline design"],
        optimization_notes=["Add metrics quantification to experience bullets"],
    )


async def get_task(task_id: uuid.UUID) -> dict:
    """Retrieve the result of a JD processing task (stub)."""
    return {"task_id": str(task_id), "status": "completed"}
