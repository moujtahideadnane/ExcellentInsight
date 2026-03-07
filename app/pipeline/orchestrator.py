import json
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
import structlog
from sqlalchemy import select, update

from app.config import get_settings
from app.db.serialization import serialize_for_db
from app.db.session import async_session_factory, set_db_context
from app.models.job import AnalysisJob, JobStatus
from app.models.job_transition import JobTransition
from app.models.pipeline_telemetry import PipelineTelemetry

# Ensure steps are registered
from app.pipeline import steps
from app.pipeline.llm_enricher import DatasetProfile, classify_table_types
from app.pipeline.pipeline_steps import (
    STATUS_TO_STEP,
    STEP_DISPLAY_NAMES,
)
from app.pipeline.step_base import PipelineContext, execute_step_with_timeout
from app.pipeline.step_registry import get_pipeline_steps
from app.pipeline.subpipelines import select_subpipelines

settings = get_settings()
logger = structlog.get_logger()


def _llm_tokens_from_usage(usage: dict) -> int:
    total = usage.get("total_tokens")
    if total is not None:
        return int(total)
    return int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)


async def log_transition(db, job_id: str, from_status: JobStatus | None, to_status: JobStatus, metadata: dict = None):
    transition = JobTransition(
        job_id=uuid.UUID(job_id),
        from_status=from_status.value if from_status else None,
        to_status=to_status.value,
        metadata_json=metadata,
    )
    db.add(transition)


async def publish_progress(
    redis_conn, job_id: str, status: JobStatus, progress: int, message: str = "", processing_time_ms: int = None
):
    data = {
        "status": STATUS_TO_STEP.get(status, "parsing"),
        "progress": progress,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if processing_time_ms is not None:
        data["processing_time_ms"] = processing_time_ms
    await redis_conn.publish(f"job:{job_id}:progress", json.dumps(data))


# ``json_ready`` was previously used as a loose helper for serialisation.
# we keep it around as an alias for backwards compatibility but the main
# implementation has moved to ``serialize_for_db`` in ``app/db/serialization``.


def json_ready(data: Any) -> Any:
    return serialize_for_db(data)


async def run_analysis_pipeline(ctx: dict, job_id: str, from_step: str = None, step_options: dict = None) -> None:
    logger.info("Starting pipeline", job_id=job_id, from_step=from_step)
    start_time = datetime.now(timezone.utc)
    redis_conn = redis.from_url(settings.REDIS_URL)

    async with async_session_factory() as db:
        # helper ensures a failed commit rolls back the transaction
        async def commit_or_rollback():
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise

        # normalize job identifier to UUID so all queries use the proper type
        job_uuid = uuid.UUID(job_id)

        # Ensure RLS context is set for worker operations using the job's org/user
        class PipelineError(Exception):
            def __init__(self, message: str, error_code: str = "PIPELINE_ERROR", retryable: bool = False):
                super().__init__(message)
                self.error_code = error_code
                self.retryable = retryable

        try:
            result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_uuid))
            initial_job = result.scalar_one_or_none()
            if initial_job:
                await set_db_context(db, str(initial_job.org_id), str(initial_job.user_id))
        except Exception:
            # If anything goes wrong here, continue without RLS (will be handled by DB policies/tests)
            logger.debug("Failed to set RLS context for worker", job_id=job_id)

        async def check_cancellation() -> bool:
            """Check if the job has been cancelled by the user."""
            res = await db.execute(select(AnalysisJob.status).where(AnalysisJob.id == job_uuid))
            current_status = res.scalar()
            if current_status == JobStatus.CANCELLED:
                logger.info("Pipeline cancelled by user", job_id=job_id)
                await publish_progress(
                    redis_conn, job_id, JobStatus.CANCELLED, progress=0, message="Analysis stopped by user"
                )
                return True
            return False

        try:
            # 1. Fetch Job and check if we can resume
            result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_uuid))
            job = result.scalar_one_or_none()
            if not job:
                logger.error("Job not found", job_id=job_id)
                await redis_conn.close()
                return

            prev_status = JobStatus(job.status) if job.status else None
            if await check_cancellation():
                return

            # 2. Setup Context
            context = PipelineContext(job_id=job_id, file_path=job.file_path, step_options=step_options or {})

            # 3. Check for existing state to resume/retry
            from app.models.pipeline_state import PipelineState

            state_result = await db.execute(select(PipelineState).where(PipelineState.job_id == job_uuid))
            pipeline_state = state_result.scalar_one_or_none()

            last_completed = None
            if from_step:
                # Use from_step for explicit retry (Feature 12)
                # We subtract one from the step index to find the 'last completed' before it
                last_completed = None  # logic handled by loop below
            elif pipeline_state:
                last_completed = pipeline_state.last_completed_step
                logger.info("Resuming pipeline from state", job_id=job_id, last_completed=last_completed)

                # Reconstruct context from saved outputs
                outputs = pipeline_state.step_outputs or {}
                # Rehydrate schema and stats so resumed runs have required context
                try:
                    from app.pipeline.schema_detector import (
                        ColumnSchema,
                        DetectedSchema,
                        Relationship,
                        SheetSchema,
                    )
                    from app.pipeline.stats_engine import (
                        ColumnStats,
                        FileStats,
                        SheetStats,
                    )

                    schema_dict = outputs.get("schema") or {}
                    stats_dict = outputs.get("stats") or {}

                    # Reconstruct DetectedSchema
                    if schema_dict:
                        sheets = []
                        for s in schema_dict.get("sheets", []):
                            cols = [ColumnSchema(**c) for c in s.get("columns", [])]
                            sheets.append(SheetSchema(name=s.get("name"), columns=cols, row_count=s.get("row_count")))
                        rels = [Relationship(**r) for r in schema_dict.get("relationships", [])]
                        context.schema = DetectedSchema(sheets=sheets, relationships=rels)

                    # Reconstruct FileStats
                    if stats_dict:
                        sheet_stats = []
                        for s in stats_dict.get("sheets", []) if isinstance(stats_dict, dict) else stats_dict:
                            # Support both dict with 'sheets' key and legacy list form
                            s_obj = s
                            if isinstance(stats_dict, dict):
                                s_obj = s
                            c_stats = [ColumnStats(**c) for c in s_obj.get("columns", [])]
                            sheet_stats.append(
                                SheetStats(
                                    name=s_obj.get("name"),
                                    row_count=s_obj.get("row_count"),
                                    columns=c_stats,
                                    correlations=s_obj.get("correlations"),
                                )
                            )
                        context.stats = FileStats(sheets=sheet_stats)
                except Exception:
                    logger.exception(
                        "Failed to rehydrate pipeline state; will re-run missing steps if needed", job_id=job_id
                    )

            # 4. Execution Loop
            steps = get_pipeline_steps()
            total_steps = len(steps)

            STEP_TO_JOB_STATUS = {
                "parsing": JobStatus.PARSING,
                "schema": JobStatus.DETECTING_SCHEMA,
                "stats": JobStatus.ANALYZING,
                "llm": JobStatus.ENRICHING,
                "dashboard": JobStatus.BUILDING,
            }

            # Precompute reverse mapping from pipeline step name to JobStatus
            # (excluding terminal states) to avoid rebuilding it in the loop.
            STEP_TO_STATUS = {
                step_name: status
                for status, step_name in STATUS_TO_STEP.items()
                if status not in (JobStatus.FAILED, JobStatus.CANCELLED)
            }

            # Skip already completed steps if resuming/retrying
            resume_index = 0
            if from_step:
                for i, step in enumerate(steps):
                    if step.name == from_step:
                        resume_index = i
                        break
            elif last_completed:
                for i, step in enumerate(steps):
                    if step.name == last_completed:
                        resume_index = i + 1
                        break

            # BUG FIX: If we are resuming from a step > 0 (e.g. LLM or Dashboard),
            # we must ensure that context.dataframes is populated.
            # Since dataframes are large and not stored in DB, we re-parse if needed.
            if resume_index > 0 and not context.dataframes:
                from app.pipeline.steps import ParsingStep

                logger.info(
                    "Resuming pipeline: re-populating dataframes", job_id=job_id, resume_from=steps[resume_index].name
                )
                await ParsingStep().execute(context)

            for i in range(resume_index, total_steps):
                step = steps[i]

                # Update progress: map step name to job status using precomputed mapping
                job_status = STEP_TO_STATUS.get(step.name, JobStatus.PARSING)
                progress_val = int((i / total_steps) * 100)

                display_msg = STEP_DISPLAY_NAMES.get(step.name, f"Running {step.name}...")
                await publish_progress(redis_conn, job_id, job_status, progress_val, display_msg)

                # Log transition if status changes
                if prev_status != job_status:
                    await log_transition(db, job_id, prev_status, job_status)
                    prev_status = job_status

                await db.execute(
                    update(AnalysisJob)
                    .where(AnalysisJob.id == job_uuid)
                    .values(status=job_status, progress=progress_val)
                )
                await commit_or_rollback()

                # Check for cancellation before executing the step
                if await check_cancellation():
                    return

                # Execute step with timeout protection
                try:
                    await execute_step_with_timeout(step, context)
                except TimeoutError as e:
                    logger.error(
                        "pipeline_step_timeout_error",
                        job_id=job_id,
                        step_name=step.name,
                        error=str(e),
                    )
                    # Treat timeout as fatal error - re-raise to fail the job
                    raise PipelineError(
                        f"Step '{step.name}' timed out: {str(e)}",
                        error_code="STEP_TIMEOUT",
                        retryable=True,
                    )

                # After stats are available, derive dataset_profile and active sub-pipelines once.
                if step.name == "stats" and context.dataset_profile is None and context.schema is not None:
                    try:
                        candidate_types = classify_table_types(context.schema)
                        context.dataset_profile = DatasetProfile(
                            total_rows=None,
                            total_columns=None,
                            has_dates=any(
                                "date" in (c.inferred_type or "").lower()
                                or "time" in (c.inferred_type or "").lower()
                                or "date" in (c.name or "").lower()
                                or "time" in (c.name or "").lower()
                                for s in context.schema.sheets
                                for c in s.columns
                            ),
                            has_amounts=False,
                            candidate_table_types=candidate_types,
                        )
                        sub_cfgs = select_subpipelines(context.dataset_profile)
                        context.active_subpipelines = [cfg.type_name for cfg in sub_cfgs]
                        if sub_cfgs:
                            # Attach any per-step options, e.g., prompt hints for the LLM step.
                            llm_opts = context.step_options.get("llm", {})
                            llm_opts.setdefault("subpipeline_types", context.active_subpipelines)
                            context.step_options["llm"] = llm_opts
                            logger.info(
                                "Sub-pipelines selected",
                                job_id=job_id,
                                subpipelines=context.active_subpipelines,
                            )
                    except Exception:
                        logger.exception("Failed to derive dataset_profile or sub-pipelines", job_id=job_id)

                # Save State for Resilience
                # ``json_ready`` now knows how to walk Pydantic models and other
                # common objects, so callers can hand it the raw attribute rather
                # than manually converting with ``to_dict``/``model_dump``.
                step_outputs = {
                    "schema": json_ready(context.schema) if context.schema else None,
                    "stats": json_ready(context.stats) if context.stats else None,
                    "llm": json_ready(context.enrichment) if context.enrichment else None,
                    "dashboard": json_ready(context.dashboard) if context.dashboard else None,
                    "dataset_profile": json_ready(context.dataset_profile) if context.dataset_profile else None,
                }

                if not pipeline_state:
                    pipeline_state = PipelineState(
                        job_id=uuid.UUID(job_id), last_completed_step=step.name, step_outputs=step_outputs
                    )
                    db.add(pipeline_state)
                else:
                    pipeline_state.last_completed_step = step.name
                    pipeline_state.step_outputs = step_outputs

                await commit_or_rollback()

                if await check_cancellation():
                    return

            # 5. Finalise
            processing_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Log transition to DONE
            await log_transition(db, job_id, prev_status, JobStatus.DONE)

            # Persist results to Job
            await db.execute(
                update(AnalysisJob)
                .where(AnalysisJob.id == job_id)
                .values(
                    status=JobStatus.DONE,
                    progress=100,
                    schema_result=serialize_for_db(context.schema) if context.schema else None,
                    stats_result=serialize_for_db(context.stats) if context.stats else None,
                    llm_result=serialize_for_db(context.enrichment) if context.enrichment else None,
                    dashboard_config=serialize_for_db(context.dashboard),
                    completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    processing_time_ms=processing_time_ms,
                    llm_tokens_used=_llm_tokens_from_usage(context.enrichment.usage)
                    if (context.enrichment and context.enrichment.usage)
                    else 0,
                )
            )

            # Persist Telemetry
            for t in context.telemetry:
                telemetry_row = PipelineTelemetry(
                    job_id=job_uuid,
                    step_name=t.step_name,
                    started_at=t.started_at,
                    completed_at=t.completed_at,
                    duration_ms=t.duration_ms,
                    rows_processed=t.rows_processed,
                    columns_processed=t.columns_processed,
                    data_size_bytes=t.data_size_bytes,
                    error=t.error,
                )
                db.add(telemetry_row)

            await commit_or_rollback()
            await publish_progress(redis_conn, job_id, JobStatus.DONE, 100, "Dashboard ready!", processing_time_ms)

        except Exception as e:
            # Classify pipeline error
            if isinstance(e, PipelineError):
                error_code = e.error_code
                retryable = e.retryable
            else:
                error_code = "INTERNAL_ERROR"
                retryable = False

            logger.exception("Pipeline failed", job_id=job_id, error=str(e), error_code=error_code)
            # Publish readable progress to clients
            await publish_progress(redis_conn, job_id, JobStatus.FAILED, 0, f"Error: {error_code}")

            # Store structured error info in the job's error_message as JSON
            try:
                error_payload = json.dumps({"error_code": error_code, "message": str(e), "retryable": retryable})
            except Exception:
                error_payload = str(e)

            await db.execute(
                update(AnalysisJob)
                .where(AnalysisJob.id == job_uuid)
                .values(status=JobStatus.FAILED, error_message=error_payload)
            )
            await commit_or_rollback()
        finally:
            await redis_conn.close()


async def recalculate_kpi(job_id: str, kpi_index: int, new_formula: str) -> dict:
    """Updates a specific KPI formula and re-calculates its value."""
    logger.info("Recalculating KPI", job_id=job_id, kpi_index=kpi_index, formula=new_formula)

    async with async_session_factory() as db:
        job_uuid = uuid.UUID(job_id)
        result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_uuid))
        job = result.scalar_one_or_none()
        if not job or not job.dashboard_config:
            raise ValueError("Job or dashboard config not found")

        # 1. Update formula in LLM result (persistence)
        llm_result = job.llm_result or {}
        if "kpis" in llm_result and kpi_index < len(llm_result["kpis"]):
            llm_result["kpis"][kpi_index]["formula"] = new_formula
            llm_result["kpis"][kpi_index]["description"] = f"Manual override formula: {new_formula}"
        else:
            raise ValueError(f"KPI index {kpi_index} out of bounds")

        # 2. Re-parse and Re-build (Partial optimization)
        # We reuse some logic but wrap it in the new context/step structure for consistency
        context = PipelineContext(job_id=job_id, file_path=job.file_path)

        # Step 1: Parsing
        from app.pipeline.steps import ParsingStep

        await ParsingStep().execute(context)

        # Step 2: Inject saved schema and stats into context instead of re-calculating
        # (This keeps the speed optimization of 'recalculate_kpi')
        from app.pipeline.llm_enricher import LLMEnrichment
        from app.pipeline.schema_detector import (
            ColumnSchema,
            DetectedSchema,
            Relationship,
            SheetSchema,
        )
        from app.pipeline.stats_engine import ColumnStats, FileStats, SheetStats

        # Deserialize objects
        enrichment = LLMEnrichment.model_validate(llm_result)
        # Ensure any KPIs/charts referencing joined sheet names have join recommendations
        try:
            from app.pipeline.llm_enricher import auto_inject_joins

            enrichment = auto_inject_joins(enrichment, context.schema)
        except Exception:
            logger.exception("auto_inject_joins failed during recalculate_kpi; continuing")

        context.enrichment = enrichment

        schema_dict = job.schema_result or {}
        stats_dict = job.stats_result or []

        sheets = []
        for s in schema_dict.get("sheets", []):
            cols = [ColumnSchema(**c) for c in s.get("columns", [])]
            sheets.append(SheetSchema(name=s["name"], columns=cols, row_count=s["row_count"]))
        rels = [Relationship(**r) for r in schema_dict.get("relationships", [])]
        context.schema = DetectedSchema(sheets=sheets, relationships=rels)

        sheet_stats = []
        stats_list = stats_dict.get("sheets", []) if isinstance(stats_dict, dict) else stats_dict
        for s in stats_list:
            c_stats = [ColumnStats(**c) for c in s.get("columns", [])]
            sheet_stats.append(
                SheetStats(
                    name=s["name"], row_count=s["row_count"], columns=c_stats, correlations=s.get("correlations")
                )
            )
        context.stats = FileStats(sheets=sheet_stats)

        # Step 3: Run only DashboardStep
        from app.pipeline.steps import DashboardStep

        await DashboardStep().execute(context)

        # 3. Update Job
        await db.execute(
            update(AnalysisJob)
            .where(AnalysisJob.id == job_uuid)
            .values(llm_result=json_ready(llm_result), dashboard_config=json_ready(context.dashboard))
        )
        await db.commit()

        # 5. Return updated dashboard
        return context.dashboard
