import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, event, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.serialization import JSONSafe as JSON
from app.db.serialization import serialize_for_db
from app.models.base import Base


class PipelineState(Base):
    """Persists the intermediate state of a pipeline execution.

    This allows a worker to resume an interrupted pipeline from the last
    successfully completed step, rather than starting from scratch.
    """

    __tablename__ = "pipeline_state"

    # One state per job
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"), primary_key=True)

    last_completed_step: Mapped[str | None] = mapped_column(nullable=True)

    # Serialised intermediate data (e.g. schemas, stats ids)
    # We don't store raw dataframes here (too large), just the metadata
    # needed to reconstruct context.
    step_outputs: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)

    # Original options/params passed to the job
    step_inputs: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)


# auto-serialize whenever the column value is replaced


def _auto_serialize_ps(target, value, oldvalue, initiator):
    return serialize_for_db(value)


for attr in ("step_outputs", "step_inputs"):
    event.listen(getattr(PipelineState, attr), "set", _auto_serialize_ps, retval=True)

    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"), onupdate=text("now()"))
