"""Centralised arq and Redis configuration.

Defines the queue topology and worker settings, ensuring consistency
between the API (producer) and worker (consumer).

Features:
- Dynamic worker scaling based on queue depth
- Priority queues (premium > pro > free)
- Queue monitoring and metrics
"""

from __future__ import annotations

import structlog
from arq.connections import RedisSettings

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

PIPELINE_REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)

# Priority levels for different organization plans
# Higher priority = processed first
QUEUE_PRIORITIES = {
    "premium": 3,  # Highest priority
    "pro": 2,      # Medium priority
    "free": 1,     # Standard priority
}

# Dynamic scaling thresholds
# Adjust max_jobs based on queue depth to prevent overload
SCALING_THRESHOLDS = {
    "low": {"queue_depth": 0, "max_jobs": 2},      # Light load: conserve resources
    "medium": {"queue_depth": 5, "max_jobs": 5},   # Normal load: default
    "high": {"queue_depth": 15, "max_jobs": 8},    # Heavy load: scale up
    "critical": {"queue_depth": 30, "max_jobs": 10}, # Critical: max capacity
}

# Worker topology configurations
# Use these in workers/settings.py and everywhere arq.create_pool is called.
QUEUE_SETTINGS = {
    "redis_settings": PIPELINE_REDIS_SETTINGS,
    "job_timeout": settings.ARQ_JOB_TIMEOUT,
    "max_jobs": settings.ARQ_MAX_JOBS,
    "result_ttl": settings.ARQ_RESULT_TTL,
}


async def get_queue_depth(redis_conn) -> int:
    """Get current queue depth for dynamic scaling decisions.

    Returns the total number of pending jobs across all priorities.
    """
    try:
        # ARQ uses a sorted set for the queue with score = enqueue time
        # Queue key format: arq:queue (default queue name)
        queue_key = "arq:queue"
        depth = await redis_conn.zcard(queue_key)
        return depth
    except Exception as e:
        logger.warning("queue_depth_check_failed", error=str(e))
        return 0


def get_dynamic_max_jobs(queue_depth: int) -> int:
    """Calculate optimal max_jobs based on current queue depth.

    Implements dynamic scaling to balance throughput and resource usage.
    """
    # Find appropriate scaling tier
    for tier_name in ["critical", "high", "medium", "low"]:
        tier = SCALING_THRESHOLDS[tier_name]
        if queue_depth >= tier["queue_depth"]:
            logger.info(
                "dynamic_scaling_applied",
                tier=tier_name,
                queue_depth=queue_depth,
                max_jobs=tier["max_jobs"]
            )
            return tier["max_jobs"]

    # Fallback to default
    return settings.ARQ_MAX_JOBS


def get_job_priority(org_plan: str) -> int:
    """Get priority level for organization's plan.

    Premium users get higher priority for faster processing.
    """
    return QUEUE_PRIORITIES.get(org_plan.lower(), QUEUE_PRIORITIES["free"])
