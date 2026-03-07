import polars as pl

from app.pipeline.formula_engine import apply_formula, robust_date_parse


def test_datediff_basic():
    df = pl.DataFrame({"start": ["2024-01-01", "2024-01-01"], "end": ["2024-01-02", "2023-12-31"]})
    # 1. Test delay (positive)
    # 2. Test advance (negative)
    result = apply_formula(df, "DATEDIFF(start, end)", "result")

    assert result["result"][0] == 1.0
    assert result["result"][1] == -1.0


def test_datediff_mixed_formats():
    df = pl.DataFrame({"start": ["01/01/2024", "2024-01-01"], "end": ["2024-02-01", "01/02/2024"]})
    result = apply_formula(df, "DATEDIFF(start, end)", "result")
    # Approx 31 days
    assert 30 <= result["result"][0] <= 32
    assert 30 <= result["result"][1] <= 32


def test_is_before_kpi():
    # Standard On-Time Delivery logic
    df = pl.DataFrame(
        {
            "actual": ["2024-01-05", "2024-01-10"],
            "scheduled": ["2024-01-06", "2024-01-09"],  # One on time, one late
        }
    )
    result = apply_formula(df, "IS_BEFORE(actual, scheduled)", "ontime")

    assert result["ontime"][0] == 1.0
    assert result["ontime"][1] == 0.0
    assert result["ontime"].mean() == 0.5  # 50% On-Time rate


def test_ratio_calculation():
    df = pl.DataFrame({"revenue": [100, 200, 300], "costs": [50, 250, 150]})
    result = apply_formula(df, "RATIO(revenue, costs)", "margin_ratio")

    assert result["margin_ratio"][0] == 2.0
    assert result["margin_ratio"][1] == 0.8
    assert result["margin_ratio"][2] == 2.0


def test_diff_calculation():
    df = pl.DataFrame({"a": [10, 20], "b": [5, 25]})
    result = apply_formula(df, "DIFF(a, b)", "diff")
    assert result["diff"][0] == 5
    assert result["diff"][1] == -5


def test_robust_date_parse():
    df = pl.DataFrame({"d": ["05/12/2023", "2023-12-06", "INVALID"]})
    parsed = robust_date_parse(df, "d")
    assert parsed["d"].dtype.is_temporal()
    assert parsed["d"][0] is not None
    assert parsed["d"][1] is not None
    assert parsed["d"][2] is None
