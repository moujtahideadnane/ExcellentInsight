"""Tests for the advanced LLM validation layer."""

import pytest

from app.pipeline.schema_detector import ColumnSchema, DetectedSchema, SheetSchema
from app.utils.llm_validation import (
    HallucinationType,
    validate_aggregations,
    validate_charts,
    validate_formulas,
    validate_joins,
    validate_llm_output,
    validate_schema_references,
    validate_semantic_quality,
)


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing."""
    return DetectedSchema(
        sheets=[
            SheetSchema(
                name="Orders",
                row_count=1000,
                columns=[
                    ColumnSchema(
                        name="OrderID",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=1000,
                        is_primary_key=True,
                    ),
                    ColumnSchema(
                        name="OrderDate",
                        inferred_type="Datetime",
                        null_count=5,
                        unique_count=300,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Amount",
                        inferred_type="Float64",
                        null_count=0,
                        unique_count=850,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Status",
                        inferred_type="Utf8",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                ],
            ),
            SheetSchema(
                name="Customers",
                row_count=500,
                columns=[
                    ColumnSchema(
                        name="CustomerID",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=500,
                        is_primary_key=True,
                    ),
                    ColumnSchema(
                        name="Name",
                        inferred_type="Utf8",
                        null_count=0,
                        unique_count=495,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Region",
                        inferred_type="Utf8",
                        null_count=0,
                        unique_count=8,
                        is_primary_key=False,
                    ),
                ],
            ),
        ],
        relationships=[],
    )


@pytest.fixture
def sample_stats_by_sheet():
    """Create sample stats for testing."""
    from unittest.mock import MagicMock

    # Create mock column stats
    status_stat = MagicMock()
    status_stat.unique_count = 5

    amount_stat = MagicMock()
    amount_stat.unique_count = 850

    orderid_stat = MagicMock()
    orderid_stat.unique_count = 1000

    region_stat = MagicMock()
    region_stat.unique_count = 8

    name_stat = MagicMock()
    name_stat.unique_count = 495

    return {
        "Orders": {
            "OrderID": orderid_stat,
            "Amount": amount_stat,
            "Status": status_stat,
        },
        "Customers": {
            "Region": region_stat,
            "Name": name_stat,
        },
    }


# === Schema Reference Tests ===


def test_validate_nonexistent_column(sample_schema):
    """Test detection of non-existent column references."""
    data = {
        "kpis": [
            {
                "label": "Invalid KPI",
                "sheet": "Orders",
                "formula": "SUM(NonExistentColumn)",
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_schema_references(data, sample_schema)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.NONEXISTENT_COLUMN for e in errors)
    assert any("NonExistentColumn" in e.message for e in errors)


def test_validate_nonexistent_sheet(sample_schema):
    """Test detection of non-existent sheet references."""
    data = {
        "kpis": [
            {
                "label": "Invalid KPI",
                "sheet": "NonExistentSheet",
                "formula": "SUM(Amount)",
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_schema_references(data, sample_schema)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.NONEXISTENT_SHEET for e in errors)
    assert any("NonExistentSheet" in e.message for e in errors)


def test_validate_wrong_sheet_for_column(sample_schema):
    """Test detection of column in wrong sheet."""
    data = {
        "kpis": [
            {
                "label": "Wrong Sheet KPI",
                "sheet": "Customers",  # Amount is in Orders, not Customers
                "formula": "SUM(Amount)",
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_schema_references(data, sample_schema)
    assert len(errors) > 0
    assert any(
        e.hallucination_type == HallucinationType.WRONG_SHEET_FOR_COLUMN for e in errors
    )


def test_validate_chart_references(sample_schema):
    """Test validation of chart column references."""
    data = {
        "kpis": [],
        "charts": [
            {
                "type": "bar",
                "title": "Invalid Chart",
                "sheet": "Orders",
                "x_axis": "NonExistentX",
                "y_axis": "NonExistentY",
                "aggregation": "sum",
            }
        ],
        "joins": [],
    }

    errors = validate_schema_references(data, sample_schema)
    assert len(errors) >= 2  # At least one for x_axis, one for y_axis
    assert any("NonExistentX" in e.message for e in errors)
    assert any("NonExistentY" in e.message for e in errors)


# === Formula Validation Tests ===


def test_validate_invalid_function(sample_schema):
    """Test detection of invalid function names."""
    data = {
        "kpis": [
            {
                "label": "Invalid Function KPI",
                "sheet": "Orders",
                "formula": "MAGIC_FUNCTION(Amount)",  # Not in ALLOWED_FUNCTIONS
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_formulas(data, sample_schema)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.INVALID_FUNCTION for e in errors)
    assert any("MAGIC_FUNCTION" in e.message for e in errors)


def test_validate_formula_syntax(sample_schema):
    """Test detection of formula syntax errors."""
    data = {
        "kpis": [
            {
                "label": "Syntax Error KPI",
                "sheet": "Orders",
                "formula": "SUM(Amount",  # Missing closing parenthesis
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_formulas(data, sample_schema)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.INVALID_SYNTAX for e in errors)
    assert any("parenthes" in e.message.lower() for e in errors)


def test_validate_type_mismatch(sample_schema):
    """Test detection of type mismatches in formulas."""
    data = {
        "kpis": [
            {
                "label": "Type Mismatch KPI",
                "sheet": "Orders",
                "formula": "SUM(Status) + AVG(Status)",  # Status is text, not numeric
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_formulas(data, sample_schema)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.TYPE_MISMATCH for e in errors)


# === Aggregation Validation Tests ===


def test_validate_invalid_aggregation(sample_schema):
    """Test detection of invalid aggregation types."""
    data = {
        "kpis": [
            {
                "label": "Invalid Agg KPI",
                "sheet": "Orders",
                "formula": "SUM(Amount)",
                "aggregation": "magic_agg",  # Not in ALLOWED_AGGREGATIONS
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_aggregations(data, sample_schema, None)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.INVALID_AGGREGATION for e in errors)


def test_validate_aggregation_on_id_column(sample_schema, sample_stats_by_sheet):
    """Test detection of SUM/AVG on ID columns."""
    data = {
        "kpis": [
            {
                "label": "Sum of IDs",
                "sheet": "Orders",
                "formula": "SUM(OrderID)",  # OrderID is unique (1000/1000)
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_aggregations(data, sample_schema, sample_stats_by_sheet)
    assert len(errors) > 0
    assert any(
        e.hallucination_type == HallucinationType.AGGREGATION_ON_ID_COLUMN for e in errors
    )


def test_validate_aggregation_on_text(sample_schema, sample_stats_by_sheet):
    """Test detection of numeric aggregation on text columns."""
    data = {
        "kpis": [
            {
                "label": "Sum of Text",
                "sheet": "Orders",
                "formula": "SUM(Status)",  # Status is text
                "aggregation": "sum",
            }
        ],
        "charts": [],
        "joins": [],
    }

    errors = validate_aggregations(data, sample_schema, sample_stats_by_sheet)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.AGGREGATION_ON_TEXT for e in errors)


# === Chart Validation Tests ===


def test_validate_invalid_chart_type(sample_schema):
    """Test detection of invalid chart types."""
    data = {
        "kpis": [],
        "charts": [
            {
                "type": "magic_chart",  # Not a valid chart type
                "title": "Invalid Type",
                "sheet": "Orders",
                "x_axis": "OrderDate",
                "y_axis": "Amount",
                "aggregation": "sum",
            }
        ],
        "joins": [],
    }

    errors = validate_charts(data, sample_schema, None)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.INVALID_CHART_TYPE for e in errors)


def test_validate_pie_chart_time_series(sample_schema):
    """Test detection of pie charts with time-series data."""
    data = {
        "kpis": [],
        "charts": [
            {
                "type": "pie",
                "title": "Pie over Time",
                "sheet": "Orders",
                "x_axis": "OrderDate",  # Date column
                "y_axis": "Amount",
                "aggregation": "sum",
            }
        ],
        "joins": [],
    }

    errors = validate_charts(data, sample_schema, None)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.PIE_CHART_TIME_SERIES for e in errors)


def test_validate_high_cardinality_split_by(sample_schema, sample_stats_by_sheet):
    """Test detection of high-cardinality split_by."""
    data = {
        "kpis": [],
        "charts": [
            {
                "type": "bar",
                "title": "High Cardinality Split",
                "sheet": "Customers",
                "x_axis": "Region",
                "y_axis": "CustomerID",
                "split_by": "Name",  # Name has 495 unique values
                "aggregation": "count",
            }
        ],
        "joins": [],
    }

    errors = validate_charts(data, sample_schema, sample_stats_by_sheet)
    assert len(errors) > 0
    assert any(
        e.hallucination_type == HallucinationType.INAPPROPRIATE_SPLIT_BY for e in errors
    )


def test_validate_duplicate_chart(sample_schema):
    """Test detection of duplicate charts."""
    data = {
        "kpis": [],
        "charts": [
            {
                "type": "bar",
                "title": "Chart 1",
                "sheet": "Orders",
                "x_axis": "Status",
                "y_axis": "Amount",
                "aggregation": "sum",
            },
            {
                "type": "line",  # Different type, but same data
                "title": "Chart 2",
                "sheet": "Orders",
                "x_axis": "Status",
                "y_axis": "Amount",
                "aggregation": "sum",
            },
        ],
        "joins": [],
    }

    errors = validate_charts(data, sample_schema, None)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.DUPLICATE_CHART for e in errors)


# === Join Validation Tests ===


def test_validate_join_missing_keys(sample_schema):
    """Test detection of joins without join keys."""
    data = {
        "kpis": [],
        "charts": [],
        "joins": [
            {
                "left_sheet": "Orders",
                "right_sheet": "Customers",
                "how": "inner",
                # Missing 'on' or 'left_on'+'right_on'
            }
        ],
    }

    errors = validate_joins(data, sample_schema)
    assert len(errors) > 0
    assert any(e.hallucination_type == HallucinationType.MISSING_JOIN_KEY for e in errors)


def test_validate_join_nonexistent_column(sample_schema):
    """Test detection of join keys that don't exist."""
    data = {
        "kpis": [],
        "charts": [],
        "joins": [
            {
                "left_sheet": "Orders",
                "right_sheet": "Customers",
                "on": "NonExistentColumn",
                "how": "inner",
            }
        ],
    }

    errors = validate_joins(data, sample_schema)
    assert len(errors) >= 2  # One for each sheet
    assert any(e.hallucination_type == HallucinationType.NONEXISTENT_COLUMN for e in errors)


# === Integration Test ===


def test_validate_llm_output_integration(sample_schema, sample_stats_by_sheet):
    """Test the master validation function with mixed valid/invalid data."""
    data = {
        "domain": "Sales",
        "summary": "Test dashboard",
        "kpis": [
            # Valid KPI
            {
                "label": "Total Revenue",
                "sheet": "Orders",
                "formula": "SUM(Amount)",
                "aggregation": "sum",
            },
            # Invalid: non-existent column
            {
                "label": "Invalid KPI",
                "sheet": "Orders",
                "formula": "SUM(FakeColumn)",
                "aggregation": "sum",
            },
            # Invalid: aggregation on ID
            {
                "label": "Sum IDs",
                "sheet": "Orders",
                "formula": "SUM(OrderID)",
                "aggregation": "sum",
            },
        ],
        "charts": [
            # Valid chart
            {
                "type": "bar",
                "title": "Revenue by Status",
                "sheet": "Orders",
                "x_axis": "Status",
                "y_axis": "Amount",
                "aggregation": "sum",
            },
            # Invalid: pie chart with time series
            {
                "type": "pie",
                "title": "Bad Pie",
                "sheet": "Orders",
                "x_axis": "OrderDate",
                "y_axis": "Amount",
                "aggregation": "sum",
            },
        ],
        "joins": [],
        "insights": [],
    }

    cleaned_data, errors = validate_llm_output(data, sample_schema, sample_stats_by_sheet)

    # Should have errors
    assert len(errors) > 0

    # Should have removed items with critical errors
    assert len(cleaned_data["kpis"]) < len(data["kpis"])

    # Valid KPI should still be there
    assert any(kpi["label"] == "Total Revenue" for kpi in cleaned_data["kpis"])

    # Invalid KPI with fake column should be removed (critical error)
    assert not any(kpi["label"] == "Invalid KPI" for kpi in cleaned_data["kpis"])
