"""Main API router — aggregates all sub-routers under /api."""

from fastapi import APIRouter

from src.api import achievements, dashboard, gaps, jd, profile, resumes, roles, stories, suggestions

api_router = APIRouter()

api_router.include_router(roles.router)
api_router.include_router(resumes.router)
api_router.include_router(achievements.router)
api_router.include_router(gaps.router)
api_router.include_router(jd.router)
api_router.include_router(suggestions.router)
api_router.include_router(profile.router)
api_router.include_router(stories.router)
api_router.include_router(dashboard.router)


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Lightweight health-check endpoint for load balancers and CI."""
    return {"status": "ok"}
