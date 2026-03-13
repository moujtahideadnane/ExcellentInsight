"""Pipeline step protocol and context.

Defines the interface every pipeline step must satisfy, plus the shared
PipelineContext that flows through the step chain.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

import polars as pl
import structlog

logger = structlog.get_logger()

# Per-step timeout limits (in seconds)
STEP_TIMEOUTS = {
    "parsing": 300,  # 5 minutes for large Excel files
    "schema": 60,  # 1 minute for schema detection
    "stats": 300,  # 5 minutes for statistical analysis
    "llm": 360,  # 45 seconds for LLM enrichment (already has 30s internal timeout)
    "dashboard": 120,  # 2 minutes for dashboard building
}


@dataclass
class StepTelemetry:
    """Per-step performance metrics collected during pipeline execution."""

    step_name: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_ms: int = 0
    rows_processed: int = 0
    columns_processed: int = 0
    data_size_bytes: int = 0
    error: str | None = None

    def finish(self, *, error: str | None = None) -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "rows_processed": self.rows_processed,
            "columns_processed": self.columns_processed,
            "data_size_bytes": self.data_size_bytes,
            "error": self.error,
        }


@dataclass
class PipelineContext:
    """Shared mutable context threaded through every pipeline step."""

    job_id: str
    file_path: str

    # Intermediate results — populated by successive steps
    dataframes: dict[str, pl.DataFrame] = field(default_factory=dict)
    schema: Any = None  # DetectedSchema | None
    stats: Any = None  # FileStats | None
    enrichment: Any = None  # LLMEnrichment | None
    dashboard: dict | None = None

    # Domain / profiling information
    dataset_profile: Any = None  # DatasetProfile | None
    active_subpipelines: list[str] = field(default_factory=list)

    # Telemetry accumulator
    telemetry: list[StepTelemetry] = field(default_factory=list)

    # Per-step options (override via config or retry params)
    step_options: dict[str, dict[str, Any]] = field(default_factory=dict)


@runtime_checkable
class PipelineStep(Protocol):
    """Interface that every pipeline step must implement."""

    name: str

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Run this step, mutating and returning *context*."""
        ...


async def execute_step_with_timeout(step: PipelineStep, context: PipelineContext) -> PipelineContext:
    """Execute a pipeline step with timeout protection.

    Args:
        step: The pipeline step to execute
        context: The pipeline context

    Returns:
        Updated pipeline context

    Raises:
        asyncio.TimeoutError: If step exceeds its timeout limit
    """
    timeout = STEP_TIMEOUTS.get(step.name, 600)  # Default: 10 minutes

    try:
        result = await asyncio.wait_for(step.execute(context), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.error(
            "pipeline_step_timeout",
            step_name=step.name,
            timeout_seconds=timeout,
            job_id=context.job_id,
        )
        raise TimeoutError(f"Pipeline step '{step.name}' exceeded timeout of {timeout}s") from None
