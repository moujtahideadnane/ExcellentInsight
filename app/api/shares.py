"""
Dashboard sharing API endpoints.

Allows users to create shareable links for dashboards with optional expiration.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant import get_job_for_tenant
from app.dependencies import get_current_org_id, get_current_user_id, get_db, get_rls_db
from app.models.job import JobStatus
from app.models.share import DashboardShare
from app.pipeline import orchestrator
from app.schemas.errors import RESPONSES_400, RESPONSES_401, RESPONSES_404

router = APIRouter(prefix="/shares", tags=["shares"])
logger = structlog.get_logger()


# ── Schemas ──────────────────────────────────────────────────


class CreateShareRequest(BaseModel):
    """Request to create a shareable link."""

    expires_in_days: Optional[int] = None  # None = never expires


class ShareResponse(BaseModel):
    """Response containing share details."""

    id: uuid.UUID
    job_id: uuid.UUID
    share_token: str
    share_url: str
    expires_at: Optional[datetime]
    is_active: bool
    view_count: int
    created_at: datetime


class ShareListResponse(BaseModel):
    """List of shares for a job."""

    shares: list[ShareResponse]


# ── Endpoints ────────────────────────────────────────────────


@router.post(
    "/dashboard/{job_id}",
    response_model=ShareResponse,
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_404},
)
async def create_dashboard_share(
    job_id: uuid.UUID,
    request: CreateShareRequest,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Create a shareable link for a dashboard."""
    # Verify job exists and belongs to org
    job = await get_job_for_tenant(db, job_id, current_org_id)

    if job.status != JobStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dashboard not ready for sharing. Job must be completed.",
        )

    # Generate secure random token (32 bytes = 64 hex chars)
    share_token = secrets.token_urlsafe(32)[:64]

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    # Create share record
    share = DashboardShare(
        job_id=job_id,
        org_id=current_org_id,
        created_by=current_user_id,
        share_token=share_token,
        expires_at=expires_at,
        is_active=True,
        view_count=0,
    )

    db.add(share)
    await db.commit()
    await db.refresh(share)

    logger.info(
        "dashboard_share_created",
        share_id=str(share.id),
        job_id=str(job_id),
        org_id=str(current_org_id),
        expires_at=expires_at.isoformat() if expires_at else None,
    )

    # Build share URL (frontend will handle the route)
    share_url = f"/shared/{share_token}"

    return ShareResponse(
        id=share.id,
        job_id=share.job_id,
        share_token=share.share_token,
        share_url=share_url,
        expires_at=share.expires_at,
        is_active=share.is_active,
        view_count=share.view_count,
        created_at=share.created_at,
    )


@router.get(
    "/dashboard/{job_id}",
    response_model=ShareListResponse,
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def list_dashboard_shares(
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """List all shares for a dashboard."""
    # Verify job exists and belongs to org
    await get_job_for_tenant(db, job_id, current_org_id)

    # Get all shares for this job
    result = await db.execute(
        select(DashboardShare)
        .where(DashboardShare.job_id == job_id)
        .where(DashboardShare.org_id == current_org_id)
        .order_by(DashboardShare.created_at.desc())
    )
    shares = result.scalars().all()

    share_responses = [
        ShareResponse(
            id=share.id,
            job_id=share.job_id,
            share_token=share.share_token,
            share_url=f"/shared/{share.share_token}",
            expires_at=share.expires_at,
            is_active=share.is_active,
            view_count=share.view_count,
            created_at=share.created_at,
        )
        for share in shares
    ]

    return ShareListResponse(shares=share_responses)


@router.delete(
    "/{share_id}",
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def revoke_share(
    share_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Revoke (deactivate) a share link."""
    result = await db.execute(
        select(DashboardShare)
        .where(DashboardShare.id == share_id)
        .where(DashboardShare.org_id == current_org_id)
    )
    share = result.scalar_one_or_none()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )

    # Deactivate the share
    await db.execute(
        update(DashboardShare)
        .where(DashboardShare.id == share_id)
        .values(is_active=False)
    )
    await db.commit()

    logger.info("dashboard_share_revoked", share_id=str(share_id), org_id=str(current_org_id))

    return {"message": "Share revoked successfully", "share_id": share_id}


@router.get(
    "/public/{share_token}",
    responses={**RESPONSES_404},
)
async def get_shared_dashboard(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint to view a shared dashboard (no authentication required).

    This endpoint bypasses RLS since it's public access via share token.
    """
    # Find active share by token
    result = await db.execute(
        select(DashboardShare).where(
            DashboardShare.share_token == share_token,
            DashboardShare.is_active == True,
        )
    )
    share = result.scalar_one_or_none()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared dashboard not found or link has expired",
        )

    # Check expiration
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This share link has expired",
        )

    # Get the job directly (bypass RLS for public access)
    from app.models.job import AnalysisJob

    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == share.job_id))
    job = result.scalar_one_or_none()

    if not job or job.status != JobStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not available",
        )

    # Update view count
    await db.execute(
        update(DashboardShare)
        .where(DashboardShare.id == share.id)
        .values(view_count=share.view_count + 1, last_viewed_at=datetime.utcnow())
    )
    await db.commit()

    # Build dashboard response
    dashboard_data = orchestrator.assemble_dashboard_response(job)

    logger.info(
        "shared_dashboard_viewed",
        share_id=str(share.id),
        job_id=str(job.id),
        view_count=share.view_count + 1,
    )

    return dashboard_data
