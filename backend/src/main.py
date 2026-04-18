"""FastAPI application entry-point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api import router as api_router
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — runs logic on startup and shutdown."""
    # Startup: create all tables if they do not exist yet.
    # In production with Alembic migrations you may remove this block.
    import src.models  # noqa: F401 — ensure all models are registered
    from src.core.database import Base, async_engine

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown: dispose of the engine pool.
    await async_engine.dispose()


app = FastAPI(
    title="CareerAgent",
    version="0.1.0",
    description="AI-powered career development assistant",
    lifespan=lifespan,
)

# ---- Middleware ----------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- API routes ----------------------------------------------------------

app.include_router(api_router, prefix="/api")


# ---- Frontend static files (production) ----------------------------------

_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir() and settings.APP_ENV == "production":
    app.mount(
        "/",
        StaticFiles(directory=str(_frontend_dist), html=True),
        name="frontend-static",
    )
