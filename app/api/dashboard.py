import hashlib
import pickle
import uuid
from typing import Optional

import polars as pl
import redis.asyncio as redis
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.tenant import get_job_for_tenant
from app.dependencies import get_current_org_id, get_rls_db
from app.models.job import AnalysisJob, JobStatus
from app.pipeline import formula_engine, orchestrator, parser
from app.schemas.dashboard import DashboardResponse, KPIUpdateRequest
from app.schemas.errors import (
    RESPONSES_400,
    RESPONSES_401,
    RESPONSES_404,
    RESPONSES_409,
    RESPONSES_500,
)
from app.utils.export import export_dashboard_excel, export_dashboard_pdf

settings = get_settings()
logger = structlog.get_logger()

# Redis-backed cache for parsed dataframes to speed up drill-down requests.
# Format: drilldown:{job_id}:{file_hash} -> pickled ParsedData
# TTL: 1 hour (3600 seconds)
_CACHE_TTL = 3600


async def _get_redis_conn(request: Request) -> redis.Redis:
    """Get Redis connection from app state or create new one."""
    redis_conn = getattr(request.app.state, "redis", None)
    if redis_conn:
        return redis_conn
    return redis.from_url(settings.REDIS_URL, decode_responses=False)


async def _get_drill_down_cache(redis_conn: redis.Redis, job_id: str, file_path: str) -> Optional[parser.ParsedData]:
    """Retrieve parsed data from Redis cache."""
    try:
        # Generate cache key from job_id and file hash
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        cache_key = f"drilldown:{job_id}:{file_hash}"

        cached = await redis_conn.get(cache_key)
        if cached:
            logger.debug("drill_down_cache_hit", job_id=job_id)
            return pickle.loads(cached)
    except Exception as e:
        logger.warning("drill_down_cache_get_failed", job_id=job_id, error=str(e))
    return None


async def _set_drill_down_cache(redis_conn: redis.Redis, job_id: str, file_path: str, parsed_data: parser.ParsedData):
    """Store parsed data in Redis cache."""
    try:
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        cache_key = f"drilldown:{job_id}:{file_hash}"

        # Pickle the parsed data for storage
        serialized = pickle.dumps(parsed_data)
        await redis_conn.setex(cache_key, _CACHE_TTL, serialized)
        logger.debug("drill_down_cache_set", job_id=job_id, size_bytes=len(serialized))
    except Exception as e:
        logger.warning("drill_down_cache_set_failed", job_id=job_id, error=str(e))


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Endpoint for clearing the Redis drill-down cache for a specific job or all jobs.
@router.post("/cache/clear")
async def clear_drilldown_cache(
    request: Request,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    job_id: Optional[str] = None,
) -> dict:
    """Clear Redis drill-down cache. If job_id provided, clear only that job. Otherwise clear all."""
    try:
        redis_conn = await _get_redis_conn(request)
        if job_id:
            # Clear specific job's cache entries
            pattern = f"drilldown:{job_id}:*"
            cursor = 0
            cleared = 0
            while True:
                cursor, keys = await redis_conn.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis_conn.delete(*keys)
                    cleared += len(keys)
                if cursor == 0:
                    break
            return {"cleared": cleared, "job_id": job_id}
        else:
            # Clear all drill-down cache entries
            pattern = "drilldown:*"
            cursor = 0
            cleared = 0
            while True:
                cursor, keys = await redis_conn.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis_conn.delete(*keys)
                    cleared += len(keys)
                if cursor == 0:
                    break
            return {"cleared": cleared, "scope": "all"}
    except Exception as e:
        logger.error("cache_clear_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to clear cache: {str(e)}"
        )


@router.patch(
    "/{job_id}/kpis/{kpi_index}",
    response_model=DashboardResponse,
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_404},
)
async def update_kpi_formula(
    job_id: uuid.UUID,
    kpi_index: int,
    request: KPIUpdateRequest,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    job = await get_job_for_tenant(db, job_id, current_org_id)

    # Trigger re-calculation
    try:
        final_dashboard = await orchestrator.recalculate_kpi(str(job_id), kpi_index, request.formula)

        return DashboardResponse(
            job_id=job.id,
            overview=final_dashboard.get("overview", {}),
            kpis=final_dashboard.get("kpis", []),
            charts=final_dashboard.get("charts", []),
            insights=final_dashboard.get("insights", []),
            relationships=final_dashboard.get("relationships", []),
            joins=final_dashboard.get("joins", []),
            data_preview=final_dashboard.get("data_preview", {}),
            created_at=job.created_at,
            processing_time_ms=job.processing_time_ms,
            schema_summary=job.schema_result,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Re-calculation failed: {str(e)}")


@router.delete(
    "/{job_id}/kpis/{kpi_index}",
    response_model=DashboardResponse,
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_404},
)
async def delete_kpi(
    job_id: uuid.UUID,
    kpi_index: int,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Delete a specific KPI from the dashboard."""
    job = await get_job_for_tenant(db, job_id, current_org_id)

    dashboard_config = job.dashboard_config or {}
    kpis = dashboard_config.get("kpis", [])

    if kpi_index < 0 or kpi_index >= len(kpis):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid KPI index {kpi_index}",
        )

    deleted_kpi = kpis.pop(kpi_index)
    dashboard_config["kpis"] = kpis

    llm_result = job.llm_result or {}
    if "kpis" in llm_result and kpi_index < len(llm_result["kpis"]):
        llm_result["kpis"].pop(kpi_index)

    await db.execute(
        update(AnalysisJob)
        .where(AnalysisJob.id == job_id)
        .values(dashboard_config=dashboard_config, llm_result=llm_result)
    )
    await db.commit()

    logger.info(
        "kpi_deleted",
        job_id=str(job_id),
        kpi_index=kpi_index,
        kpi_label=deleted_kpi.get("label", "unknown"),
    )

    llm_usage = None
    usage = llm_result.get("usage") or {}
    if usage or (job.llm_tokens_used and job.llm_tokens_used > 0):
        llm_usage = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens") or job.llm_tokens_used,
        }

    return DashboardResponse(
        job_id=job.id,
        overview=dashboard_config.get("overview", {}),
        kpis=kpis,
        charts=dashboard_config.get("charts", []),
        insights=dashboard_config.get("insights", []),
        relationships=dashboard_config.get("relationships", []),
        joins=dashboard_config.get("joins", []),
        data_preview=dashboard_config.get("data_preview", {}),
        dataset_profile=dashboard_config.get("dataset_profile"),
        created_at=job.created_at,
        processing_time_ms=job.processing_time_ms,
        schema_summary=job.schema_result,
        llm_usage=llm_usage,
    )


@router.get(
    "/{job_id}",
    response_model=DashboardResponse,
    responses={**RESPONSES_401, **RESPONSES_404, **RESPONSES_409, **RESPONSES_500},
)
async def get_dashboard(
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    job = await get_job_for_tenant(db, job_id, current_org_id, require_done=True)

    if not job.dashboard_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard configuration missing despite job completion",
        )

    # Build llm_usage from job.llm_tokens_used and/or llm_result.usage
    llm_usage = None
    llm_result = job.llm_result or {}
    usage = llm_result.get("usage") or {}
    if usage or (job.llm_tokens_used and job.llm_tokens_used > 0):
        llm_usage = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens") or job.llm_tokens_used,
        }

    return DashboardResponse(
        job_id=job.id,
        overview=job.dashboard_config.get("overview", {}),
        kpis=job.dashboard_config.get("kpis", []),
        charts=job.dashboard_config.get("charts", []),
        insights=job.dashboard_config.get("insights", []),
        relationships=job.dashboard_config.get("relationships", []),
        joins=job.dashboard_config.get("joins", []),
        data_preview=job.dashboard_config.get("data_preview", {}),
        dataset_profile=job.dashboard_config.get("dataset_profile"),
        created_at=job.created_at,
        processing_time_ms=job.processing_time_ms,
        schema_summary=job.schema_result,
        llm_usage=llm_usage,
    )


@router.get(
    "/{job_id}/drill-down",
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_404},
)
async def drill_down(
    request: Request,
    job_id: uuid.UUID,
    sheet: str,
    column: str,
    value: str,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Return up to 100 raw rows that match the clicked chart label.

    Handles two common mismatches:
    * Sheet name: the parquet cache strips non-ASCII chars (e.g. "Données" →
      "Donnes").  We try an exact match first, then the stripped version, then
      a case-insensitive fuzzy match.
    * Column name: the LLM may emit the original header while the parquet stores
      the normalize_column_name() version (snake_case, lowercase).  We apply the
      same normalization to both sides before comparing.

    Uses Redis cache with 1-hour TTL to avoid re-parsing for frequent drill-downs.
    """
    import re as _re

    from app.pipeline.parser import normalize_column_name as _norm_col

    job = await get_job_for_tenant(db, job_id, current_org_id)

    # ── 1. Load parsed data (Redis cache or re-parse) ────────────────────────
    try:
        redis_conn = await _get_redis_conn(request)

        # Try to get from Redis cache first
        parsed_data = await _get_drill_down_cache(redis_conn, str(job_id), job.file_path)

        if not parsed_data:
            # Cache miss - parse and store in Redis
            logger.debug("drill_down_cache_miss", job_id=str(job_id))
            from app.pipeline import parser as parser_module

            parsed_data = await parser_module.parse_excel(job.file_path, job_id=str(job_id))

            # Store in Redis cache asynchronously (don't block on failure)
            await _set_drill_down_cache(redis_conn, str(job_id), job.file_path, parsed_data)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Uploaded file no longer available at {job.file_path}",
        )
    except Exception as e:
        logger.error("drill_down_parse_failed", job_id=str(job_id), error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    all_dfs: dict = {**parsed_data.dataframes}

    # ── 2. Rebuild virtual joined sheets ─────────────────────────────────────
    try:
        joins = (job.dashboard_config or {}).get("joins", [])
        for join in joins:
            left_df = all_dfs.get(join.get("left_sheet", ""))
            right_df = all_dfs.get(join.get("right_sheet", ""))
            if left_df is None or right_df is None:
                continue
            on_col = join.get("on", "")
            if on_col in left_df.columns and on_col in right_df.columns:
                if left_df[on_col].dtype != right_df[on_col].dtype:
                    left_df = left_df.with_columns(pl.col(on_col).cast(pl.String))
                    right_df = right_df.with_columns(pl.col(on_col).cast(pl.String))
            try:
                virtual_name = f"{join['left_sheet']}+{join['right_sheet']}"
                all_dfs[virtual_name] = left_df.join(right_df, on=on_col, how=join.get("how", "left"))
            except Exception as join_err:
                logger.warning("drill_down_join_failed", error=str(join_err))
    except Exception as e:
        logger.warning("drill_down_joins_skipped", error=str(e))

    # ── 3. Resolve sheet name ─────────────────────────────────────────────────
    # The parquet saver strips non-ASCII chars: re.sub(r'[^a-zA-Z0-9_-]', '', name)
    def _safe(s: str) -> str:
        return _re.sub(r"[^a-zA-Z0-9_-]", "", s)

    def _resolve_sheet(name: str, available: dict) -> str | None:
        # 1. Exact match
        if name in available:
            return name
        # 2. Safe-name match (stripped accents — matches parquet filenames)
        safe = _safe(name)
        if safe in available:
            return safe
        # 3. Case-insensitive fuzzy match
        name_l = name.lower().strip()
        for k in available:
            if k.lower().strip() == name_l or _safe(k).lower() == safe.lower():
                return k
        return None

    resolved_sheet = _resolve_sheet(sheet, all_dfs)
    if resolved_sheet is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sheet '{sheet}' not found. Available: {', '.join(all_dfs.keys())}",
        )

    df = all_dfs[resolved_sheet]

    # ── 4. Resolve column name ────────────────────────────────────────────────
    # The LLM may emit original header names; the parquet stores normalize_column_name()
    # versions (snake_case, lowercase, alphanumeric only).
    def _resolve_column(col: str, cols: list[str]) -> str | None:
        if col in cols:
            return col
        col_l = col.lower().strip()
        col_norm = _norm_col(col)
        for c in cols:
            if c.lower().strip() == col_l:
                return c
            if _norm_col(c) == col_norm:
                return c
        return None

    resolved_col = _resolve_column(column, df.columns)
    if resolved_col is None:
        raise HTTPException(
            status_code=400,
            detail=(f"Column '{column}' not found in sheet '{resolved_sheet}'. Available: {', '.join(df.columns)}"),
        )

    # ── 5. Filter rows ────────────────────────────────────────────────────────
    try:
        # Detect synthetic column references (__year__, __value__) from melted charts
        is_synthetic = resolved_col in ("__year__", "__value__")

        # If synthetic, we need to know what columns were melted
        y_cols = []
        if is_synthetic:
            subpipelines = (job.dashboard_config or {}).get("dataset_profile", {}).get("candidate_table_types", [])
            # Find the first subpipeline that might have signaled y_columns
            for sub in subpipelines:
                if sub.get("type") == "budget_projection":  # Or generic check for y_cols if we generalize it
                    # Extract years from headers if not explicitly stored
                    import re as _re

                    _year_pat = _re.compile(r"^\d{4}$")
                    y_cols = [c for c in df.columns if _year_pat.match(c)]
                    break

        if is_synthetic and resolved_col == "__year__" and y_cols:
            # If filtering for a specific year, find that column and filter for non-null
            if value in y_cols:
                filtered_df = df.filter(pl.col(value).is_not_null())
            else:
                filtered_df = df.filter(pl.lit(False))  # No match
        elif df[resolved_col].dtype.is_temporal():
            # Attempt date-parsing on the resolved column so temporal bucketing works.
            df = formula_engine.robust_date_parse(df, resolved_col)
            # Try each bucketing format that dashboard_builder.py uses.
            date_formats = ["%Y-%m", "%m-%d", "%H:%M"]
            filtered_df: pl.DataFrame | None = None
            for fmt in date_formats:
                try:
                    candidate = df.filter(pl.col(resolved_col).dt.to_string(fmt) == value)
                    if len(candidate) > 0:
                        filtered_df = candidate
                        logger.info(
                            "drill_down_matched",
                            sheet=resolved_sheet,
                            column=resolved_col,
                            value=value,
                            format=fmt,
                            rows=len(candidate),
                        )
                        break
                except Exception:
                    continue
            if not filtered_df or len(filtered_df) == 0:
                logger.warning(
                    "drill_down_no_match",
                    sheet=resolved_sheet,
                    column=resolved_col,
                    value=value,
                )
                return []
        else:
            val_norm = str(value).strip().lower()
            try:
                filtered_df = df.filter(
                    pl.col(resolved_col).cast(pl.String).str.strip_chars().str.to_lowercase() == val_norm
                )
            except Exception:
                filtered_df = df.filter(pl.col(resolved_col).cast(pl.String) == value)

            if len(filtered_df) == 0:
                logger.debug(
                    "drill_down_no_records",
                    sheet=resolved_sheet,
                    column=resolved_col,
                    value=value,
                )
                return []

        return filtered_df.head(100).to_dicts()

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(
            "drill_down_filter_error",
            sheet=resolved_sheet,
            column=resolved_col,
            value=value,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=f"Filtering failed: {str(e)}")


@router.post(
    "/{job_id}/stop",
    responses={**RESPONSES_401, **RESPONSES_404},
)
async def stop_analysis(
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    job = await get_job_for_tenant(db, job_id, current_org_id)

    if job.status in [JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED]:
        return {"message": "Job is already in a terminal state", "status": job.status}

    # Mark as cancelled — the orchestrator will pick this up at the next checkpoint
    await db.execute(update(AnalysisJob).where(AnalysisJob.id == job_id).values(status=JobStatus.CANCELLED))
    await db.commit()

    return {"message": "Analysis stopping...", "job_id": job_id}


@router.get(
    "/{job_id}/export/pdf",
    responses={**RESPONSES_401, **RESPONSES_404, **RESPONSES_500},
)
async def export_pdf(
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Export dashboard as PDF."""
    try:
        job = await get_job_for_tenant(db, job_id, current_org_id)

        if job.status != JobStatus.DONE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dashboard not ready for export. Job must be completed.",
            )

        # Build dashboard data structure
        dashboard_data = orchestrator.assemble_dashboard_response(job)

        # Generate PDF
        pdf_buffer = export_dashboard_pdf(dashboard_data)

        logger.info("dashboard_pdf_exported", job_id=str(job_id), org_id=str(current_org_id))

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=dashboard_{job_id}.pdf"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("pdf_export_failed", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF export",
        )


@router.get(
    "/{job_id}/export/excel",
    responses={**RESPONSES_401, **RESPONSES_404, **RESPONSES_500},
)
async def export_excel(
    job_id: uuid.UUID,
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
):
    """Export dashboard as Excel."""
    try:
        job = await get_job_for_tenant(db, job_id, current_org_id)

        if job.status != JobStatus.DONE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dashboard not ready for export. Job must be completed.",
            )

        # Build dashboard data structure
        dashboard_data = orchestrator.assemble_dashboard_response(job)

        # Generate Excel
        excel_buffer = export_dashboard_excel(dashboard_data)

        logger.info("dashboard_excel_exported", job_id=str(job_id), org_id=str(current_org_id))

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=dashboard_{job_id}.xlsx"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("excel_export_failed", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Excel export",
        )
