import os
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.session import get_db
from app.main import app
from app.models.base import Base

# Test database URL, prefer TEST_DATABASE_URL env var.  For CI/development
# we also allow falling back to the main DATABASE_URL so that tests hit the
# same Postgres instance developers use, avoiding sqlite dependency.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not TEST_DATABASE_URL:
    # final fallback: lightweight sqlite in-memory (requires aiosqlite)
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine; SQLite doesn't accept poolclass arguments, so
# only include NullPool for other dialects.
if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(TEST_DATABASE_URL)
else:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Note: per-test DB session override is applied inside the `db_session` fixture
# so that each test runs inside its own transaction which is rolled back.


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables before tests and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide a database session for each test and rollback afterwards.

    This fixture starts a transaction on a dedicated connection and binds the
    session to that connection. It also overrides the FastAPI `get_db`
    dependency for the duration of the test so HTTP requests use the same
    transactional session.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        async with TestingSessionLocal(bind=conn) as session:

            async def _override_get_db():
                yield session

            app.dependency_overrides[get_db] = _override_get_db
            try:
                yield session
            finally:
                await session.close()
                await trans.rollback()
                app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def client(db_session):
    """Provide an HTTP client for testing that uses the transactional DB session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(client):
    """Provide an authenticated client."""
    # Signup
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": f"test_{uuid.uuid4().hex}@example.com", "password": "testpassword123", "org_name": "Test Org"},
    )

    assert response.status_code == 201
    tokens = response.json()

    # Set authorization header
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    return client, tokens["user"]["id"], tokens["user"]["org_id"]
