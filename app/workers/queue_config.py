"""Centralised arq and Redis configuration.

Defines the queue topology and worker settings, ensuring consistency
between the API (producer) and worker (consumer).
"""

from __future__ import annotations

from arq.connections import RedisSettings

from app.config import get_settings

settings = get_settings()

PIPELINE_REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)

# Worker topology configurations
# Use these in workers/settings.py and everywhere arq.create_pool is called.
QUEUE_SETTINGS = {
    "redis_settings": PIPELINE_REDIS_SETTINGS,
    "job_timeout": settings.ARQ_JOB_TIMEOUT,
    "max_jobs": settings.ARQ_MAX_JOBS,
    "result_ttl": settings.ARQ_RESULT_TTL,
}
