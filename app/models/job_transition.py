import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobTransition(Base):
    """Audit trail of status changes for an AnalysisJob."""

    __tablename__ = "job_transitions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True)

    from_status: Mapped[str | None] = mapped_column(nullable=True)
    to_status: Mapped[str]

    timestamp: Mapped[datetime] = mapped_column(server_default=text("now()"))

    # Store additional context (e.g. error details, progress, or retry params)
    metadata_json: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)
