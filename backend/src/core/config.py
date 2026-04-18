from pathlib import Path

from pydantic_settings import BaseSettings

# Load .env from project root (one level up from backend/) so all env vars
# (including GLM_API_KEY etc.) are available in os.environ for config.yaml resolution.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ROOT_ENV = _PROJECT_ROOT / ".env"

from dotenv import load_dotenv

load_dotenv(_ROOT_ENV)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/careeragent"
    REDIS_URL: str = "redis://localhost:6379/0"

    LANGSMITH_API_KEY: str = ""
    LANGSMITH_TRACING: bool = False
    LANGSMITH_PROJECT: str = "careeragent"

    APP_ENV: str = "development"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {"env_file": str(_ROOT_ENV), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
