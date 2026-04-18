"""Main API router — aggregates all sub-routers under /api."""

from fastapi import APIRouter

from src.api import achievements, dashboard, educations, gaps, interactive_analysis, jd, pipeline_stream, profile, projects, resumes, role_analyze, roles, stories, suggestions, work_experiences

api_router = APIRouter()

# Register role_analyze BEFORE roles so /roles/analyze-jd matches before /roles/{role_id}
api_router.include_router(role_analyze.router)
api_router.include_router(roles.router)
api_router.include_router(resumes.router)
api_router.include_router(achievements.router)
api_router.include_router(interactive_analysis.router)
api_router.include_router(gaps.router)
api_router.include_router(jd.router)
api_router.include_router(suggestions.router)
api_router.include_router(profile.router)
api_router.include_router(stories.router)
api_router.include_router(dashboard.router)
api_router.include_router(work_experiences.router)
api_router.include_router(educations.router)
api_router.include_router(projects.router)
api_router.include_router(pipeline_stream.router)


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Lightweight health-check endpoint for load balancers and CI."""
    return {"status": "ok"}
