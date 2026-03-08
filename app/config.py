from functools import lru_cache
from typing import List

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # ── Application ──
    APP_NAME: str = "ExcellentInsight"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_VERSION: str = "v1"
    PORT: int = 5000
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Database ──
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379"

    # ── Storage ──
    STORAGE_BACKEND: str = "local"  # local | s3
    STORAGE_LOCAL_PATH: str = "./uploads"
    # S3_BUCKET: str = ""
    # S3_REGION: str = "eu-west-1"
    # S3_ACCESS_KEY: str = ""
    # S3_SECRET_KEY: str = ""

    # ── Auth ──
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    JWT_REFRESH_EXPIRY_DAYS: int = 30

    # ── LLM ──
    LLM_PROVIDER: str = "openrouter"  # openrouter | openai | anthropic
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "arcee-ai/trinity-large-preview:free"
    LLM_FALLBACK_MODEL: str = "openai/gpt-oss-120b:free"
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.1
    LLM_CACHE_TTL_HOURS: int = 24

    # ── Upload Limits ──
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls", ".csv"]
    MAX_SHEETS_PER_FILE: int = 20
    MAX_ROWS_PER_SHEET: int = 500_000

    # ── ARQ Worker ──
    ARQ_MAX_JOBS: int = 5
    ARQ_JOB_TIMEOUT: int = 900  # 15 minutes
    ARQ_RESULT_TTL: int = 3600  # 1 hour


@lru_cache
def get_settings() -> Settings:
    return Settings()
