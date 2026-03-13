import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.tenant import get_job_for_tenant, tenant_query
from app.dependencies import get_current_org_id, get_rls_db
from app.models.job import AnalysisJob, JobStatus
from app.pipeline.pipeline_steps import STATUS_TO_STEP
from app.schemas.errors import RESPONSES_400, RESPONSES_401, RESPONSES_404
from app.schemas.job import JobListResponse, JobResponse

logger = structlog.get_logger(__name__)

# Map DB/worker status to frontend SSE contract
# (Now uses central source of truth)
SSE_STATUS_MAP = {k: v for k, v in STATUS_TO_STEP.items()}

settings = get_settings()
router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "",
    response_model=JobListResponse,
    responses={**RESPONSES_400, **RESPONSES_401},
)
async def list_jobs(
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
    limit: int = Query(20, le=100, description="Number of jobs to return (max 100)"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (ISO timestamp from last job)"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status (e.g. done, failed, pending)"
    ),
):
    """List all analysis jobs for the current organisation with cursor-based pagination.

    Cursor-based pagination is more efficient than offset-based for large datasets
    and prevents issues with duplicate/missing items when data changes.

    The cursor is the created_at timestamp of the last job in the previous page.
    """
    base_query = tenant_query(AnalysisJob, current_org_id)
    filters = []

    # Apply optional status filter
    if status_filter:
        # Accept either lower- or upper-case input and normalize to enum values
        normalized_status = status_filter.lower()
        try:
            mapped_status = JobStatus(normalized_status)
            filters.append(AnalysisJob.status == mapped_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{status_filter}'. Valid values: {[s.value for s in JobStatus]}",
            ) from None

    # Apply cursor-based pagination
    if cursor:
        try:
            # Parse ISO timestamp cursor
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            filters.append(AnalysisJob.created_at < cursor_dt)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cursor format. Expected ISO timestamp, got: {cursor}",
            ) from None

    # Count total for UI (can be expensive - consider caching or removing for very large datasets)
    count_query = (
        select(func.count())
        .select_from(AnalysisJob)
        .where(AnalysisJob.org_id == current_org_id, *filters[:1] if status_filter else [])
    )
    total = await db.scalar(count_query)

    query = (
        base_query.where(*filters)
        .order_by(AnalysisJob.created_at.desc())
        .limit(limit + 1)  # Fetch one extra to determine if there are more pages
    )
    result = await db.execute(query)
    jobs = result.scalars().all()

    # Determine if there are more pages
    has_more = len(jobs) > limit
    if has_more:
        jobs = jobs[:limit]  # Remove the extra item

    # Generate next cursor from the last job's created_at
    next_cursor = None
    if has_more and jobs:
        next_cursor = jobs[-1].created_at.isoformat()

    return {"jobs": jobs, "total": total or 0, "limit": limit, "cursor": next_cursor, "has_more": has_more}


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def get_job(
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    return await get_job_for_tenant(db, job_id, current_org_id)


@router.get(
    "/{job_id}/progress",
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def job_progress(
    request: Request,
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    job = await get_job_for_tenant(db, job_id, current_org_id)

    async def event_generator():
        # --- Initial snapshot ---
        # `job.status` is already a `JobStatus` enum; map it directly via the
        # central STATUS_TO_STEP mapping to ensure consistency with the worker.
        frontend_status = SSE_STATUS_MAP.get(job.status, "parsing")

        initial_state: dict = {
            "status": frontend_status,
            "progress": job.progress or 0,
            "message": job.error_message or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if getattr(job, "processing_time_ms", None) is not None:
            initial_state["processing_time_ms"] = job.processing_time_ms

        yield f"data: {json.dumps(initial_state)}\n\n"

        # Already terminal — serve snapshot and close immediately
        if frontend_status in ("done", "failed"):
            return

        # --- Subscribe to Redis pub/sub for live updates ---
        redis_node = getattr(request.app.state, "redis", None)
        _managed_conn = False
        if not redis_node:
            try:
                redis_node = redis.from_url(settings.REDIS_URL)
                _managed_conn = True
            except Exception as e:
                logger.error("redis_connection_failed", job_id=str(job_id), error=str(e))
                # If Redis fails, still yield a warning but don't crash
                error_state = {
                    "status": "warning",
                    "message": "Live updates unavailable, but job is processing",
                    "progress": job.progress or 0,
                }
                yield f"data: {json.dumps(error_state)}\n\n"
                return

        try:
            pubsub = redis_node.pubsub(ignore_subscribe_messages=True)
            channel = f"job:{job_id}:progress"
            await pubsub.subscribe(channel)
        except Exception as e:
            logger.error("pubsub_subscription_failed", job_id=str(job_id), error=str(e))
            error_state = {
                "status": "warning",
                "message": "Unable to subscribe to live updates",
                "progress": job.progress or 0,
            }
            yield f"data: {json.dumps(error_state)}\n\n"
            if _managed_conn:
                await redis_node.aclose()
            return

        last_heartbeat = asyncio.get_event_loop().time()
        heartbeat_interval = 15.0  # seconds

        try:
            while True:
                try:
                    raw = await pubsub.get_message(timeout=0.5)

                    if raw and raw.get("type") == "message":
                        payload_str = raw["data"].decode("utf-8")
                        yield f"data: {payload_str}\n\n"

                        data = json.loads(payload_str)
                        if data.get("status") in ("done", "failed"):
                            break

                    now = asyncio.get_event_loop().time()
                    if now - last_heartbeat > heartbeat_interval:
                        yield ": heartbeat\n\n"
                        last_heartbeat = now
                except asyncio.CancelledError:
                    logger.info("sse_stream_cancelled", job_id=str(job_id))
                    break
                except Exception as e:
                    logger.error("sse_stream_error", job_id=str(job_id), error=str(e))
                    error_state = {
                        "status": "warning",
                        "message": f"Stream error: {str(e)[:100]}",
                        "progress": job.progress or 0,
                    }
                    yield f"data: {json.dumps(error_state)}\n\n"
                    break
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
            except Exception as e:
                logger.warning("pubsub_cleanup_error", job_id=str(job_id), error=str(e))
            if _managed_conn:
                try:
                    await redis_node.aclose()
                except Exception as e:
                    logger.warning("redis_cleanup_error", job_id=str(job_id), error=str(e))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
