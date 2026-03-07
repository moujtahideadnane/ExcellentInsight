import uuid

import pytest

from app.models.job import AnalysisJob, JobStatus
from app.models.organization import Organization
from app.models.user import User
from app.utils.security import decode_token


@pytest.mark.asyncio
async def test_refresh_token_payload_has_org_id(authenticated_client):
    """Test that the refresh token includes org_id."""
    client, user_id, org_id = authenticated_client

    email = f"refresh_test_{uuid.uuid4().hex}@example.com"
    signup_response = await client.post(
        "/api/v1/auth/signup", json={"email": email, "password": "testpassword123", "org_name": "Refresh Org"}
    )

    assert signup_response.status_code == 201
    refresh_token = signup_response.json()["refresh_token"]
    payload = decode_token(refresh_token)

    assert "org_id" in payload
    assert payload["org_id"] == str(signup_response.json()["user"]["org_id"])


@pytest.mark.asyncio
async def test_tenant_isolation_jobs(authenticated_client, client, db_session):
    """Test that Org A cannot see Org B's jobs."""
    client_a, user_id_a, org_id_a = authenticated_client

    # Create Org B
    org_b = Organization(id=uuid.uuid4(), name="Org B")
    user_b = User(id=uuid.uuid4(), email=f"org_b_{uuid.uuid4().hex}@example.com", password_hash="...", org_id=org_b.id)
    db_session.add(org_b)
    db_session.add(user_b)
    await db_session.flush()  # Ensure org and user exist before job

    job_b = AnalysisJob(
        id=uuid.uuid4(),
        org_id=org_b.id,
        user_id=user_b.id,
        file_name="secret_b.xlsx",
        file_path="/tmp/secret_b.xlsx",
        file_size_bytes=1000,
        status=JobStatus.DONE,
    )
    db_session.add(job_b)
    await db_session.commit()

    # Org A tries to GET Org B's job
    response = await client_a.get(f"/api/v1/jobs/{job_b.id}")
    assert response.status_code == 404
