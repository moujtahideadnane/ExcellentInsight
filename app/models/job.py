import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, event, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.serialization import JSONSafe as JSON
from app.db.serialization import serialize_for_db
from app.models.base import Base, TenantMixin


class JobStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    DETECTING_SCHEMA = "detecting_schema"
    ANALYZING = "analyzing"
    ENRICHING = "enriching"
    BUILDING = "building"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisJob(Base, TenantMixin):
    __tablename__ = "analysis_jobs"

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_created_at", "created_at"),
        Index("ix_jobs_user_id", "user_id"),
        Index("ix_jobs_org_status_created", "org_id", "status", "created_at"),
        Index("ix_jobs_org_created_desc", "org_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_name: Mapped[str]
    file_path: Mapped[str]
    file_size_bytes: Mapped[int]
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False),
        default=JobStatus.PENDING,
    )
    progress: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(nullable=True)

    schema_result: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)
    stats_result: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)
    llm_result: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)
    dashboard_config: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)

    llm_tokens_used: Mapped[int] = mapped_column(default=0)
    processing_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="jobs")  # noqa: F821


def _auto_serialize(target, value, oldvalue, initiator):
    return serialize_for_db(value)


for _attr in ("schema_result", "stats_result", "llm_result", "dashboard_config"):
    event.listen(getattr(AnalysisJob, _attr), "set", _auto_serialize, retval=True)
