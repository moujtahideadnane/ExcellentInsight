from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.pipeline.llm_enricher import enrich_data, validate_and_filter_llm_response
from app.pipeline.schema_detector import ColumnSchema, DetectedSchema, SheetSchema
from app.pipeline.stats_engine import FileStats


@pytest.mark.asyncio
async def test_column_validation_removes_invalid_references():
    """Test that LLM column validation removes invalid references."""
    # Create a real schema instead of mock for data validation
    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="Orders",
                row_count=100,
                columns=[
                    ColumnSchema(
                        name="order_id", inferred_type="integer", null_count=0, unique_count=100, is_primary_key=True
                    ),
                    ColumnSchema(
                        name="amount", inferred_type="float", null_count=0, unique_count=90, is_primary_key=False
                    ),
                ],
            ),
            SheetSchema(
                name="Customers",
                row_count=50,
                columns=[
                    ColumnSchema(
                        name="customer_id", inferred_type="integer", null_count=0, unique_count=50, is_primary_key=True
                    ),
                    ColumnSchema(
                        name="name", inferred_type="string", null_count=0, unique_count=45, is_primary_key=False
                    ),
                ],
            ),
        ],
        relationships=[],
    )

    # Mock data with some invalid references
    llm_data = {
        "domain": "Sales",
        "summary": "Test summary",
        "kpis": [
            {"label": "Valid KPI", "sheet": "Orders", "formula": "SUM(amount)"},
            {"label": "Invalid KPI", "sheet": "NonExistent", "formula": "SUM(x)"},
        ],
        "charts": [
            {"type": "bar", "title": "Valid Chart", "sheet": "Orders", "x_axis": "order_id", "y_axis": "amount"},
            {"type": "bar", "title": "Invalid Chart", "sheet": "NonExistent", "x_axis": "x", "y_axis": "y"},
        ],
        "insights": [],
        "joins": [],
    }

    # Validate
    validated = validate_and_filter_llm_response(llm_data, schema)

    # Should only have valid items
    assert len(validated["kpis"]) == 1
    assert validated["kpis"][0]["label"] == "Valid KPI"
    assert len(validated["charts"]) == 1
    assert validated["charts"][0]["title"] == "Valid Chart"


@pytest.mark.asyncio
async def test_llm_cache_hit():
    """Test that cache hit skips LLM call."""
    # Create mock schema and stats
    schema = MagicMock(spec=DetectedSchema)
    schema.sheets = []
    schema.relationships = []
    schema.to_dict.return_value = {"sheets": [], "relationships": []}

    stats = MagicMock(spec=FileStats)

    # Mock cache to return a hit
    cached_result = {
        "domain": "Cached Domain",
        "summary": "Cached summary",
        "kpis": [],
        "charts": [],
        "insights": [],
        "joins": [],
    }

    with patch("app.pipeline.llm_enricher.LLMCache") as MockCache:
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=cached_result)
        mock_cache.close = AsyncMock()
        MockCache.return_value = mock_cache

        # Mock OpenRouterClient to ensure it's not called
        with patch("app.pipeline.llm_enricher.OpenRouterClient") as MockClient:
            result = await enrich_data(schema, stats)

            # Verify cache was used
            mock_cache.get.assert_called_once()
            # Verify OpenRouterClient was never instantiated
            MockClient.assert_not_called()

            # Verify result
            assert result.domain == "Cached Domain"


@pytest.mark.asyncio
async def test_fallback_on_invalid_json():
    """Test fallback when LLM returns invalid JSON."""
    schema = MagicMock(spec=DetectedSchema)
    schema.sheets = []
    schema.relationships = []
    schema.to_dict.return_value = {"sheets": [], "relationships": []}

    stats = MagicMock(spec=FileStats)

    # Mock cache miss
    with patch("app.pipeline.llm_enricher.LLMCache") as MockCache:
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.close = AsyncMock()
        MockCache.return_value = mock_cache

        # Mock OpenRouterClient to return invalid JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.parsed_json = None  # Invalid JSON
        mock_client.complete = AsyncMock(return_value=mock_response)

        with patch("app.pipeline.llm_enricher.OpenRouterClient", return_value=mock_client):
            result = await enrich_data(schema, stats)

            # Should return fallback empty enrichment
            assert result.domain == "Unknown"
            assert result.summary == "No summary available."
            assert len(result.kpis) == 0
            assert len(result.charts) == 0
