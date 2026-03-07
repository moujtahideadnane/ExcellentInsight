import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PipelineTelemetry(Base):
    """Stores performance metrics for each pipeline step execution."""

    __tablename__ = "pipeline_telemetry"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True)
    step_name: Mapped[str]

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(default=0)

    # Payload metrics
    rows_processed: Mapped[int] = mapped_column(default=0)
    columns_processed: Mapped[int] = mapped_column(default=0)
    data_size_bytes: Mapped[int] = mapped_column(default=0)

    error: Mapped[str | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
