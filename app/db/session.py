"""Database session factory and slow-query monitoring.

Provides the async engine, session factory, RLS context setter,
and event listeners that log queries exceeding a configurable threshold.
"""

from __future__ import annotations

import time

import structlog
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

# ── Slow query threshold (ms) ────────────────────────────────────────────────
SLOW_QUERY_THRESHOLD_MS = 500

# Build kwargs adaptively depending on dialect.  SQLite (including
# the memory uri used in unit tests) does not accept pool_size/max_overflow
# and will raise a TypeError if passed, so we omit them.
engine_kwargs: dict[str, object] = {"echo": settings.DEBUG}

# Only include Postgres-specific arguments when not using SQLite
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["connect_args"] = {
        "server_settings": {
            # Kill any single statement that runs longer than 30 s
            "statement_timeout": "30000",
        }
    }

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Slow query event listeners ───────────────────────────────────────────────
# These fire on the *sync* core engine that underlies the async wrapper.


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_times = conn.info.get("query_start_time")
    if not start_times:
        return
    elapsed_ms = (time.perf_counter() - start_times.pop()) * 1000
    if elapsed_ms > SLOW_QUERY_THRESHOLD_MS:
        logger.warning(
            "Slow query detected",
            duration_ms=round(elapsed_ms, 1),
            statement=statement[:200],  # truncate to avoid log spam
        )


async def get_db():
    async with async_session_factory() as session:
        yield session


async def set_db_context(session: AsyncSession, org_id: str, user_id: str):
    """Sets PostgreSQL local variables for RLS.

    SECURITY: Validates UUIDs before execution to prevent SQL injection.
    PostgreSQL's SET LOCAL doesn't support parameterized values, so we
    validate the input is a valid UUID before using it in the statement.
    """
    import uuid as uuid_module

    # Validate inputs are valid UUIDs (raises ValueError if not)
    try:
        uuid_module.UUID(org_id)
        uuid_module.UUID(user_id)
    except ValueError as e:
        logger.error("Invalid UUID for RLS context", org_id=org_id, user_id=user_id, error=str(e))
        raise ValueError(f"Invalid UUID format for RLS context: {e}") from e

    # Safe to use in SET LOCAL since we've validated it's a UUID
    await session.execute(text(f"SET LOCAL app.current_org_id = '{org_id}'"))
    await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))
