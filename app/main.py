from contextlib import asynccontextmanager

import redis.asyncio as redis
import structlog
import uvicorn
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.config import get_settings
from app.db.session import async_session_factory
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware

settings = get_settings()

# Configure structlog for production JSON logging
if settings.APP_ENV == "production":
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Starting ExcellentInsight API", env=settings.APP_ENV, version=settings.API_VERSION)

    # 1. General Redis pool (for auth blocklist, SSE, etc.)
    try:
        app.state.redis = redis.from_url(settings.REDIS_URL, decode_responses=False)
        await app.state.redis.ping()
        logger.info("General Redis pool initialised")
    except Exception as exc:
        logger.error("General Redis pool failed to start", error=str(exc))
        app.state.redis = None

    # 2. Shared arq pool — avoids creating a new pool per upload request
    try:
        app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        logger.info("arq Redis pool initialised")
    except Exception as exc:
        logger.warning("arq Redis pool NOT available — uploads will use per-request pools", error=str(exc))
        app.state.arq_pool = None

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Stopping ExcellentInsight API")
    if getattr(app.state, "redis", None):
        await app.state.redis.aclose()
    if getattr(app.state, "arq_pool", None):
        await app.state.arq_pool.aclose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Request ID middleware (first to set request.state.request_id)
app.add_middleware(RequestIDMiddleware)

# Response Compression (gzip/brotli) - add early in chain for maximum benefit
from app.middleware.compression import CompressionMiddleware

app.add_middleware(CompressionMiddleware, min_size=500)

# Error Handler (catches unhandled errors and returns standardized envelope)
app.add_middleware(ErrorHandlerMiddleware)

# Rate Limiting
app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["ETag", "X-Request-ID"],  # Allow frontend to read these headers
)

# API Router
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")

# Register exception handlers to normalize HTTPException and validation errors
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
async def health_check():
    result = {"status": "ok", "app": settings.APP_NAME, "version": settings.API_VERSION}

    # Check DB
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        result["db"] = "ok"
    except Exception as e:
        result["db"] = f"error: {str(e)}"
        result["status"] = "degraded"

    # Check Redis (reuse the shared pool from lifespan — no throwaway connections)
    try:
        r = getattr(app.state, "redis", None)
        if r:
            await r.ping()
            # Get connection pool info for monitoring
            pool_info = {}
            try:
                # Try to get pool statistics if available
                if hasattr(r, "connection_pool"):
                    pool = r.connection_pool
                    # Get current pool state
                    pool_info = {
                        "max_connections": getattr(pool, "max_connections", "N/A"),
                        "available_connections": len(getattr(pool, "_available_connections", [])),
                        "in_use_connections": len(getattr(pool, "_in_use_connections", set())),
                    }
            except Exception:
                # Pool introspection failed, skip detailed metrics
                pass

            result["redis"] = {
                "status": "ok",
                "pool": pool_info if pool_info else "metrics_unavailable"
            }
        else:
            result["redis"] = "unavailable"
            result["status"] = "degraded"
    except Exception as e:
        result["redis"] = f"error: {str(e)}"
        result["status"] = "degraded"

    # Check arq pool and queue depth
    arq_pool_available = getattr(app.state, "arq_pool", None)
    if arq_pool_available:
        result["arq_pool"] = "ok"
        # Get queue depth for monitoring and dynamic scaling
        try:
            from app.workers.queue_config import get_dynamic_max_jobs, get_queue_depth

            r = getattr(app.state, "redis", None)
            if r:
                queue_depth = await get_queue_depth(r)
                recommended_max_jobs = get_dynamic_max_jobs(queue_depth)

                result["queue"] = {
                    "depth": queue_depth,
                    "current_max_jobs": settings.ARQ_MAX_JOBS,
                    "recommended_max_jobs": recommended_max_jobs,
                    "scaling_needed": recommended_max_jobs != settings.ARQ_MAX_JOBS
                }
        except Exception as e:
            logger.warning("queue_depth_check_failed", error=str(e))
            result["queue"] = "metrics_unavailable"
    else:
        result["arq_pool"] = "unavailable"

    status_code = 200 if result["status"] == "ok" else 503
    return JSONResponse(content=result, status_code=status_code)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
