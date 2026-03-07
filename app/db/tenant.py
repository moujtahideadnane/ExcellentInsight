"""Tenant-scoped query helpers.

Provides reusable functions that automatically apply org_id filtering
to all tenant-scoped queries, preventing accidental cross-tenant data leaks.
"""

from __future__ import annotations

import uuid
from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.models.job import AnalysisJob

T = TypeVar("T", bound=Base)


def tenant_query(model: type[T], org_id: uuid.UUID):
    """Return a base SELECT filtered by org_id.

    Usage::

        query = tenant_query(AnalysisJob, org_id).where(AnalysisJob.status == "done")
        result = await db.execute(query)
    """
    return select(model).where(model.org_id == org_id)  # type: ignore[attr-defined]


async def get_job_for_tenant(
    db: AsyncSession,
    job_id: uuid.UUID,
    org_id: uuid.UUID,
    *,
    require_done: bool = False,
) -> AnalysisJob:
    """Fetch a single job scoped to the tenant, or raise 404.

    Parameters
    ----------
    require_done : bool
        If True, also raises 409 when the job exists but is not DONE.
    """
    from app.models.job import JobStatus  # avoid circular import at module level

    query = select(AnalysisJob).where(
        AnalysisJob.id == job_id,
        AnalysisJob.org_id == org_id,
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if require_done and job.status != JobStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Analysis not complete. Current status: {job.status}",
        )

    return job
