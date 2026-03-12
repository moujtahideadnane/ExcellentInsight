"""
Dashboard share model for generating and managing shareable links.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DashboardShare(Base):
    """Represents a shareable link for a dashboard."""

    __tablename__ = "dashboard_shares"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Unique token for sharing (shorter than UUID for cleaner URLs)
    share_token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # Optional expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Active status (can be revoked)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships (optional, can add if needed)
    # job = relationship("AnalysisJob", back_populates="shares")
    # organization = relationship("Organization")
    # creator = relationship("User")

    def __repr__(self) -> str:
        return f"<DashboardShare(id={self.id}, token={self.share_token[:8]}..., active={self.is_active})>"
