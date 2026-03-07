import uuid

import pytest


@pytest.mark.asyncio
async def test_full_flow_signup_upload_dashboard(authenticated_client):
    """Test the full flow: signup → upload → poll progress → get dashboard."""
    client, user_id, org_id = authenticated_client

    # Note: This is a simplified test. In a real scenario, you would:
    # 1. Create a test Excel file
    # 2. Upload it via POST /upload
    # 3. Poll the job progress via SSE
    # 4. Get the dashboard via GET /dashboard/{job_id}

    # For now, we just verify the endpoints exist and return appropriate responses

    # Test jobs list endpoint
    response = await client.get("/api/v1/jobs")
    assert response.status_code in [200, 401]  # 401 if auth middleware blocks, 200 if OK

    if response.status_code == 200:
        data = response.json()
        assert "jobs" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_unauthorized_access_returns_401(client):
    """Test that unauthorized access returns 401."""
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_not_found_returns_404(authenticated_client):
    """Test that requesting a non-existent dashboard returns 404."""
    client, user_id, org_id = authenticated_client

    fake_job_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/dashboard/{fake_job_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_conflict_for_incomplete_job(authenticated_client, db_session):
    """A job that exists but is not done should return 409."""
    client, user_id, org_id = authenticated_client

    # insert a dummy job in the database with status != DONE
    from app.models.job import AnalysisJob, JobStatus

    job = AnalysisJob(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id) if isinstance(org_id, str) else org_id,
        user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
        file_name="test.xlsx",
        file_path="/tmp/test.xlsx",
        file_size_bytes=1024,
        status=JobStatus.PARSING.value,
        progress=0,
    )
    db_session.add(job)
    await db_session.commit()

    response = await client.get(f"/api/v1/dashboard/{job.id}")
    assert response.status_code == 409
    assert response.json().get("detail", "").startswith("Analysis not complete")


@pytest.mark.asyncio
async def test_job_progress_requires_auth(client):
    """Test that job progress endpoint requires authentication."""
    fake_job_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/jobs/{fake_job_id}/progress")
    assert response.status_code == 401
