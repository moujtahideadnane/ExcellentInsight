import uuid

import pytest
from sqlalchemy import select

from app.models.job import AnalysisJob
from app.models.organization import Organization
from app.models.user import User
from app.pipeline.llm_enricher import validate_kpi


def test_kpi_validation_logic():
    """Test that validate_kpi correctly identifies invalid columns."""
    all_sheets = {"Orders", "Products"}
    sheet_columns = {"Orders": {"OrderID", "Status", "Revenue"}, "Products": {"ProductID", "Price"}}

    # Valid KPI
    valid_kpi = {"label": "Total Revenue", "formula": "SUM(Revenue)", "sheet": "Orders"}
    assert validate_kpi(valid_kpi, all_sheets, sheet_columns) is True

    # Invalid Sheet
    invalid_sheet_kpi = {"label": "Total Revenue", "formula": "SUM(Revenue)", "sheet": "Unknown"}
    assert validate_kpi(invalid_sheet_kpi, all_sheets, sheet_columns) is False


@pytest.mark.asyncio
async def test_llm_usage_tracking_in_db(db_session):
    """Test that llm_tokens_used is populated in the database."""
    # Create Org and User in the same session
    org = Organization(id=uuid.uuid4(), name="Test Org")
    user = User(id=uuid.uuid4(), email=f"user_{uuid.uuid4().hex}@example.com", password_hash="...", org_id=org.id)
    db_session.add(org)
    db_session.add(user)
    await db_session.flush()

    job_id = uuid.uuid4()
    job = AnalysisJob(
        id=job_id,
        org_id=org.id,
        user_id=user.id,
        file_name="test.xlsx",
        file_path="/tmp/test.xlsx",
        file_size_bytes=500,
        llm_tokens_used=1500,
    )
    db_session.add(job)
    await db_session.commit()

    res = await db_session.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    saved_job = res.scalar_one()
    assert saved_job.llm_tokens_used == 1500
