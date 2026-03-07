import polars as pl

from app.pipeline.dashboard_builder import build_dashboard
from app.pipeline.llm_enricher import ChartRecommendation, KPISuggestion, LLMEnrichment
from app.pipeline.schema_detector import DetectedSchema, SheetSchema
from app.pipeline.stats_engine import FileStats


def test_build_dashboard_kpis_and_charts():
    # Setup Mock Data
    df = pl.DataFrame(
        {
            "OrderID": [1, 2, 3, 4],
            "OrderDate": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "DeliveryDate": ["2024-01-02", "2024-01-01", "2024-01-04", "2024-01-04"],
            "Value": [100, 200, 300, 400],
        }
    )

    dataframes = {"Sheet1": df}

    schema = DetectedSchema(sheets=[SheetSchema(name="Sheet1", columns=[], row_count=4)], relationships=[])

    stats = FileStats(sheets=[])

    enrichment = LLMEnrichment(
        domain="Sales",
        summary="Test summary",
        kpis=[
            KPISuggestion(label="Total Value", formula="Value", sheet="Sheet1", aggregation="sum", format="number"),
            KPISuggestion(
                label="Avg Delay",
                formula="DATEDIFF(OrderDate, DeliveryDate)",
                sheet="Sheet1",
                aggregation="avg",
                format="number",
            ),
        ],
        charts=[
            ChartRecommendation(
                type="line",
                title="Trend",
                description="desc",
                sheet="Sheet1",
                x_axis="OrderDate",
                y_axis="Value",
                aggregation="sum",
            )
        ],
        insights=[],
        joins=[],
    )

    dashboard = build_dashboard(dataframes, schema, stats, enrichment)

    # Assertions
    kpis = {k["label"]: k["value"] for k in dashboard["kpis"]}
    assert kpis["Total Value"] == 1000.0

    # Delays: [1, -1, 1, 0] -> Avg = 0.25
    assert kpis["Avg Delay"] == 0.25

    assert len(dashboard["charts"]) == 1
    chart_data = dashboard["charts"][0]["data"]
    # Check aggregation: first date (2024-01-01) has value 100; label may be "2024-01-01" or "01-01" (temporal scaling)
    assert len(chart_data) == 4
    point_with_100 = next((p for p in chart_data if p["value"] == 100.0), None)
    assert point_with_100 is not None
    assert point_with_100["label"] in ("2024-01-01", "01-01")


def test_time_chart_conversion_and_negative():
    # Setup a sheet where y-axis is a DATEDIFF formula producing both
    # positive and negative results; underlying values are in days.
    df = pl.DataFrame(
        {
            "Start": ["2024-01-01", "2024-01-10", "2024-01-05"],
            "End": ["2024-01-02", "2024-01-05", "2024-01-03"],
        }
    )
    dataframes = {"S": df}
    schema = DetectedSchema(sheets=[SheetSchema(name="S", columns=[], row_count=3)], relationships=[])
    stats = FileStats(sheets=[])
    enrichment = LLMEnrichment(
        domain="Test",
        summary="",
        kpis=[],
        charts=[
            ChartRecommendation(
                type="line",
                title="DelayTrend",
                description="",
                sheet="S",
                x_axis="Start",
                y_axis="DATEDIFF(Start, End)",
                aggregation="avg",
                unit=None,
            )
        ],
        insights=[],
        joins=[],
    )
    dashboard = build_dashboard(dataframes, schema, stats, enrichment)
    chart = dashboard["charts"][0]
    # values from formula: [1, -5, -2] days -> average over same day groups
    data_vals = [row["value"] for row in chart["data"]]
    # Should include negative numbers
    assert any(v < 0 for v in data_vals)
    # Because values are in days and range >1 day, conversion should yield
    # hours not milliseconds -- we expect unit of 'h' or 'days', not 'ms'.
    assert chart["unit"] in ("h", "days")
    # confirm no ms
    assert chart["unit"] != "ms"


def test_smart_convert_time_values_base_units():
    from app.pipeline.dashboard_builder import smart_convert_time_values

    # base seconds (default)
    unit, vals = smart_convert_time_values([0.5, 2])
    assert unit == "sec"
    # base days should treat 0.5 day as 12h
    unit2, vals2 = smart_convert_time_values([0.5, 2], base_unit="days")
    assert unit2 in ("h", "days")
    # base minutes should not convert to ms since values > 1 minute.
    # Depending on the magnitudes the output unit might even be hours.
    unit3, vals3 = smart_convert_time_values([30, 120], base_unit="min")
    assert unit3 in ("sec", "min", "h", "days")
    # negative-only list should still choose based on magnitude, not sign
    unit4, vals4 = smart_convert_time_values([-0.5, -2], base_unit="sec")
    assert unit4 == "sec" or unit4 == "min" or unit4 == "h" or unit4 == "days"
