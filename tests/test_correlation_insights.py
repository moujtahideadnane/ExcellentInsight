"""Tests for correlation insights detection in dashboard_builder."""

import polars as pl
import pytest

from app.pipeline.dashboard_builder import detect_correlation_insights
from app.pipeline.schema_detector import ColumnSchema, DetectedSchema, SheetSchema


def test_detect_correlation_insights_strong_positive():
    """Test detection of strong positive correlation."""
    # Create data with strong positive correlation
    df = pl.DataFrame(
        {
            "Sales": [100, 200, 300, 400, 500],
            "Marketing": [10, 20, 30, 40, 50],
            "Region": ["A", "B", "C", "D", "E"],
        }
    )

    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="Data",
                row_count=5,
                columns=[
                    ColumnSchema(
                        name="Sales",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Marketing",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Region",
                        inferred_type="Utf8",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                ],
            )
        ],
        relationships=[],
    )

    dataframes = {"Data": df}

    insights = detect_correlation_insights(dataframes, schema, threshold=0.7)

    assert len(insights) == 1
    assert insights[0]["type"] == "correlation"
    assert insights[0]["severity"] in ["high", "medium"]
    assert "Sales" in insights[0]["text"]
    assert "Marketing" in insights[0]["text"]
    assert "positive" in insights[0]["text"].lower()
    assert insights[0]["metadata"]["correlation"] > 0.7


def test_detect_correlation_insights_strong_negative():
    """Test detection of strong negative correlation."""
    # Create data with strong negative correlation
    df = pl.DataFrame(
        {
            "Price": [100, 90, 80, 70, 60],
            "Demand": [10, 20, 30, 40, 50],
        }
    )

    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="Economics",
                row_count=5,
                columns=[
                    ColumnSchema(
                        name="Price",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Demand",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                ],
            )
        ],
        relationships=[],
    )

    dataframes = {"Economics": df}

    insights = detect_correlation_insights(dataframes, schema, threshold=0.7)

    assert len(insights) == 1
    assert insights[0]["type"] == "correlation"
    assert "Price" in insights[0]["text"]
    assert "Demand" in insights[0]["text"]
    assert "negative" in insights[0]["text"].lower()
    assert insights[0]["metadata"]["correlation"] < -0.7


def test_detect_correlation_insights_below_threshold():
    """Test that weak correlations are not reported."""
    # Create data with weak correlation
    df = pl.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [5, 4, 6, 2, 8],  # Random values, weak correlation
        }
    )

    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="Data",
                row_count=5,
                columns=[
                    ColumnSchema(
                        name="A",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="B",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                ],
            )
        ],
        relationships=[],
    )

    dataframes = {"Data": df}

    insights = detect_correlation_insights(dataframes, schema, threshold=0.7)

    # Should not detect any insights for weak correlations
    assert len(insights) == 0


def test_detect_correlation_insights_no_numeric_columns():
    """Test that no insights are generated when there are no numeric columns."""
    df = pl.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie"],
            "City": ["NYC", "LA", "Chicago"],
        }
    )

    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="People",
                row_count=3,
                columns=[
                    ColumnSchema(
                        name="Name",
                        inferred_type="Utf8",
                        null_count=0,
                        unique_count=3,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="City",
                        inferred_type="Utf8",
                        null_count=0,
                        unique_count=3,
                        is_primary_key=False,
                    ),
                ],
            )
        ],
        relationships=[],
    )

    dataframes = {"People": df}

    insights = detect_correlation_insights(dataframes, schema, threshold=0.7)

    assert len(insights) == 0


def test_detect_correlation_insights_multiple_pairs():
    """Test detection of multiple correlations in same dataset."""
    # Create data with multiple correlated pairs
    df = pl.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": [2, 4, 6, 8, 10],  # Strong positive with A
            "C": [5, 4, 3, 2, 1],  # Strong negative with A
        }
    )

    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="Data",
                row_count=5,
                columns=[
                    ColumnSchema(
                        name="A",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="B",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="C",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                ],
            )
        ],
        relationships=[],
    )

    dataframes = {"Data": df}

    insights = detect_correlation_insights(dataframes, schema, threshold=0.7)

    # Should detect: A-B (positive), A-C (negative), B-C (negative)
    assert len(insights) == 3
    assert all(i["type"] == "correlation" for i in insights)


def test_detect_correlation_insights_metadata():
    """Test that insight metadata is correctly populated."""
    df = pl.DataFrame(
        {
            "X": [1, 2, 3, 4, 5],
            "Y": [2, 4, 6, 8, 10],
        }
    )

    schema = DetectedSchema(
        sheets=[
            SheetSchema(
                name="TestSheet",
                row_count=5,
                columns=[
                    ColumnSchema(
                        name="X",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                    ColumnSchema(
                        name="Y",
                        inferred_type="Int64",
                        null_count=0,
                        unique_count=5,
                        is_primary_key=False,
                    ),
                ],
            )
        ],
        relationships=[],
    )

    dataframes = {"TestSheet": df}

    insights = detect_correlation_insights(dataframes, schema, threshold=0.7)

    assert len(insights) == 1
    metadata = insights[0]["metadata"]
    assert metadata["sheet"] == "TestSheet"
    assert metadata["column1"] in ["X", "Y"]
    assert metadata["column2"] in ["X", "Y"]
    assert metadata["column1"] != metadata["column2"]
    assert "correlation" in metadata
    assert "direction" in metadata
    assert metadata["direction"] in ["positive", "negative"]
