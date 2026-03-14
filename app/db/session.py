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

# ── Connection pool monitoring threshold (seconds) ────────────────────────────
POOL_CHECKOUT_THRESHOLD_SECONDS = 2.0  # Warn if waiting > 2s for connection

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


@event.listens_for(engine.sync_engine, "connect")
def _on_connect(dbapi_conn, connection_record):
    """Track connection creation time for pool monitoring."""
    connection_record.info["connected_at"] = time.perf_counter()


@event.listens_for(engine.sync_engine, "checkout")
def _on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Monitor connection checkout time to detect pool exhaustion."""
    checkout_start = connection_record.info.get("checkout_start")
    if checkout_start:
        wait_time = time.perf_counter() - checkout_start
        if wait_time > POOL_CHECKOUT_THRESHOLD_SECONDS:
            logger.warning(
                "Slow connection pool checkout",
                wait_seconds=round(wait_time, 2),
                pool_size=engine.pool.size(),
                overflow=engine.pool.overflow(),
                checkedin=engine.pool.checkedin(),
            )


@event.listens_for(engine.sync_engine, "checkin")
def _on_checkin(dbapi_conn, connection_record):
    """Track when connection is returned to pool."""
    connection_record.info["checkout_start"] = time.perf_counter()


async def get_db():
    """Dependency that provides a database session with automatic cleanup.

    Ensures that:
    - Session is properly closed even if exceptions occur
    - Uncommitted transactions are rolled back to prevent connection hanging
    - Connection is returned to the pool promptly
    """
    session = async_session_factory()
    try:
        yield session
    finally:
        # Ensure any uncommitted transaction is rolled back
        # This prevents connections from being held with open transactions
        try:
            if session.in_transaction():
                await session.rollback()
        except Exception as e:
            logger.warning("Failed to rollback session transaction", error=str(e))
        finally:
            # Always close the session to return connection to pool
            await session.close()


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
