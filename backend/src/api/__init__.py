"""API package — re-exports the aggregated router for convenience."""

from src.api.router import api_router as router

__all__ = ["router"]
