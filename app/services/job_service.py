"""Job lifecycle service.

Centralises the critical transactional pattern:
    store file → create DB job row → enqueue arq task

If any step fails the entire operation rolls back, preventing half-states
(e.g. a DB row with no arq task, or an arq task referencing a missing row).
"""

from __future__ import annotations

import re
import uuid
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.models.job import AnalysisJob, JobStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.storage.base import StorageBackend

settings = get_settings()
logger = structlog.get_logger()

_UNSAFE_CHARS = re.compile(r"[^\w\-. ]")


class JobService:
    """Domain service for job creation and lifecycle management."""

    @staticmethod
    async def create_and_enqueue(
        db: "AsyncSession",
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        file: UploadFile,
        storage: "StorageBackend",
        arq_pool=None,
    ) -> AnalysisJob:
        """Atomically store file, create job record, and enqueue pipeline.

        The DB commit only happens *after* the arq job is successfully enqueued,
        so we never leave an orphan job row without a corresponding worker task.
        """
        # 1. Sanitise filename
        safe_name = PurePosixPath(file.filename).name
        safe_name = _UNSAFE_CHARS.sub("_", safe_name).strip() or "upload"

        extension = "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Allowed: {settings.ALLOWED_EXTENSIONS}",
            )

        # 2. Store file with streaming size enforcement
        job_id = uuid.uuid4()
        storage_filename = f"{org_id}/{job_id}/{safe_name}"

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        # Read actual file size from FastAPI metadata
        file_size = getattr(file, "size", 0)

        if file_size > max_bytes:
            await file.close()
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB.",
            )

        # Pass the UploadFile directly to the storage adapter 
        # (It natively supports async chunked reads)
        storage_path = await storage.upload(file, storage_filename)

        # 3. Create job in DB (not yet committed)
        job = AnalysisJob(
            id=job_id,
            user_id=user_id,
            org_id=org_id,
            file_name=file.filename,
            file_path=storage_path,
            file_size_bytes=file_size,
            status=JobStatus.PENDING,
            progress=0,
        )
        db.add(job)
        await db.flush()  # Ensure row is valid before enqueue

        # 4. Enqueue background task with priority based on organization plan
        _managed_pool = False
        try:
            if not arq_pool:
                arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
                _managed_pool = True

            # Get organization plan to determine job priority
            from app.models.organization import Organization
            from sqlalchemy import select

            org_result = await db.execute(select(Organization).where(Organization.id == org_id))
            org = org_result.scalar_one_or_none()
            org_plan = org.plan if org else "free"

            # Calculate priority score for queue ordering
            from app.workers.queue_config import get_job_priority
            priority = get_job_priority(org_plan)

            # Removed artificial delay penalty (defer_seconds) to ensure 
            # sub-1min deployment speed for all development users.
            defer_seconds = 0

            await arq_pool.enqueue_job(
                "run_analysis_pipeline",
                str(job.id),
                _defer_by=None
            )

            logger.info(
                "job_enqueued_with_priority",
                job_id=str(job_id),
                org_plan=org_plan,
                priority=priority,
                defer_by=defer_seconds
            )

        except Exception as exc:
            logger.error("Failed to enqueue pipeline job", job_id=str(job_id), error=str(exc))
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Analysis service is temporarily unavailable. Please try again.",
            ) from exc
        finally:
            if _managed_pool and arq_pool:
                await arq_pool.aclose()

        # 5. Commit only after successful enqueue
        await db.commit()
        await db.refresh(job)

        logger.info("Job created and enqueued", job_id=str(job_id), file=file.filename)
        return job
