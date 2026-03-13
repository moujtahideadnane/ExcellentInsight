"""Advanced validation layer for LLM-generated dashboard configurations.

This module implements comprehensive validation to catch various types of
hallucinations before they reach the dashboard configuration.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from app.pipeline.schema_detector import DetectedSchema

logger = structlog.get_logger()


# === Hallucination Type Definitions ===


class HallucinationType:
    """Types of hallucinations the LLM can produce in dashboard generation."""

    # Schema hallucinations
    NONEXISTENT_COLUMN = "nonexistent_column"
    NONEXISTENT_SHEET = "nonexistent_sheet"
    WRONG_SHEET_FOR_COLUMN = "wrong_sheet_for_column"

    # Formula hallucinations
    INVALID_FUNCTION = "invalid_function"
    INVALID_SYNTAX = "invalid_syntax"
    TYPE_MISMATCH = "type_mismatch"
    CIRCULAR_REFERENCE = "circular_reference"

    # Aggregation hallucinations
    INVALID_AGGREGATION = "invalid_aggregation"
    AGGREGATION_ON_ID_COLUMN = "aggregation_on_id_column"
    AGGREGATION_ON_TEXT = "aggregation_on_text"

    # Chart hallucinations
    INVALID_CHART_TYPE = "invalid_chart_type"
    PIE_CHART_TIME_SERIES = "pie_chart_time_series"
    HIGH_CARDINALITY_AXIS = "high_cardinality_axis"
    DUPLICATE_CHART = "duplicate_chart"

    # Join hallucinations
    IMPOSSIBLE_JOIN = "impossible_join"
    MISSING_JOIN_KEY = "missing_join_key"
    TYPE_INCOMPATIBLE_JOIN = "type_incompatible_join"

    # Semantic hallucinations
    MEANINGLESS_KPI = "meaningless_kpi"
    REVERSED_AXIS = "reversed_axis"
    INAPPROPRIATE_SPLIT_BY = "inappropriate_split_by"


# === Allowed Functions and Aggregations ===

ALLOWED_FUNCTIONS = {
    # Arithmetic
    "SUM",
    "AVG",
    "COUNT",
    "COUNTIF",
    "MIN",
    "MAX",
    # Statistical
    "MEDIAN",
    "STDEV",
    "VAR",
    "PERCENTILE",
    "MODE",
    # Date functions
    "DATEDIFF",
    "IS_BEFORE",
    # Comparison
    "LT",
    "GT",
    # Mathematical
    "RATIO",
    "DIFF",
    # Conditional
    "COALESCE",
    # Note: CORR is implemented but should only be used in insights pipeline, not KPIs
    # Note: Not yet implemented in formula_engine.py:
    # ABS, ROUND, FLOOR, CEIL, IF, CONCAT, LENGTH, IS_AFTER, LTE, GTE, EQ, NEQ, QUARTILE, RANGE
}

ALLOWED_AGGREGATIONS = {"sum", "avg", "count", "min", "max", "median", "stddev", "stdev", "var", "mode", "percentile"}

VALID_CHART_TYPES = {"bar", "line", "area", "pie"}

VALID_FORMATS = {"number", "percentage", "currency"}

VALID_PRIORITIES = {"high", "medium", "low"}

VALID_SEVERITIES = {"high", "medium", "low", "info", "warning"}


# === Validation Error Class ===


class ValidationError:
    """Represents a single validation error."""

    def __init__(
        self,
        hallucination_type: str,
        severity: str,
        message: str,
        field: Optional[str] = None,
        suggested_fix: Optional[str] = None,
    ):
        self.hallucination_type = hallucination_type
        self.severity = severity  # 'critical', 'high', 'medium', 'low'
        self.message = message
        self.field = field
        self.suggested_fix = suggested_fix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.hallucination_type,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
            "suggested_fix": self.suggested_fix,
        }


# === Core Validation Functions ===


def validate_schema_references(
    data: Dict[str, Any],
    schema: DetectedSchema,
) -> List[ValidationError]:
    """Validate that all sheet and column references exist in the schema.

    Catches:
    - NONEXISTENT_COLUMN: Column doesn't exist in any sheet
    - NONEXISTENT_SHEET: Sheet doesn't exist
    - WRONG_SHEET_FOR_COLUMN: Column exists but not in the specified sheet
    """
    errors: List[ValidationError] = []

    # Build lookup structures
    all_sheets = {s.name for s in schema.sheets}
    sheet_columns: Dict[str, Set[str]] = {s.name: {c.name for c in s.columns} for s in schema.sheets}
    # All columns across all sheets for fuzzy matching
    all_columns = set()
    for cols in sheet_columns.values():
        all_columns.update(cols)

    # Validate KPIs
    for kpi in data.get("kpis", []):
        sheet = kpi.get("sheet", "")
        formula = kpi.get("formula", "")
        label = kpi.get("label", "unnamed")

        # Check sheet exists
        if not _is_valid_sheet_reference(sheet, all_sheets):
            errors.append(
                ValidationError(
                    HallucinationType.NONEXISTENT_SHEET,
                    "critical",
                    f"KPI '{label}' references non-existent sheet '{sheet}'",
                    field=f"kpis.{label}.sheet",
                    suggested_fix=_suggest_sheet_name(sheet, all_sheets),
                )
            )
            continue

        # Extract column references from formula
        column_refs = _extract_column_references(formula)
        available_cols = _resolve_sheet_columns(sheet, all_sheets, sheet_columns)

        for col_ref in column_refs:
            if col_ref not in available_cols:
                # Check if column exists in another sheet
                other_sheet = _find_sheet_with_column(col_ref, sheet_columns)
                if other_sheet:
                    errors.append(
                        ValidationError(
                            HallucinationType.WRONG_SHEET_FOR_COLUMN,
                            "critical",
                            f"KPI '{label}' formula references column '{col_ref}' which exists in sheet '{other_sheet}', not '{sheet}'",
                            field=f"kpis.{label}.formula",
                            suggested_fix=f"Use sheet '{other_sheet}' or create a join",
                        )
                    )
                else:
                    errors.append(
                        ValidationError(
                            HallucinationType.NONEXISTENT_COLUMN,
                            "critical",
                            f"KPI '{label}' formula references non-existent column '{col_ref}'",
                            field=f"kpis.{label}.formula",
                            suggested_fix=_suggest_column_name(col_ref, all_columns),
                        )
                    )

        # Validate group_by column
        group_by = kpi.get("group_by")
        if group_by and group_by not in available_cols:
            errors.append(
                ValidationError(
                    HallucinationType.NONEXISTENT_COLUMN,
                    "high",
                    f"KPI '{label}' group_by references non-existent column '{group_by}'",
                    field=f"kpis.{label}.group_by",
                    suggested_fix=_suggest_column_name(group_by, available_cols),
                )
            )

    # Validate charts
    for chart in data.get("charts", []):
        sheet = chart.get("sheet", "")
        title = chart.get("title", "untitled")
        x_axis = chart.get("x_axis")
        y_axis = chart.get("y_axis")
        split_by = chart.get("split_by")

        # Check sheet exists
        if not _is_valid_sheet_reference(sheet, all_sheets):
            errors.append(
                ValidationError(
                    HallucinationType.NONEXISTENT_SHEET,
                    "critical",
                    f"Chart '{title}' references non-existent sheet '{sheet}'",
                    field=f"charts.{title}.sheet",
                    suggested_fix=_suggest_sheet_name(sheet, all_sheets),
                )
            )
            continue

        available_cols = _resolve_sheet_columns(sheet, all_sheets, sheet_columns)

        # Validate x_axis
        if x_axis:
            x_cols = _extract_column_references(x_axis)
            for col in x_cols:
                if col not in available_cols:
                    errors.append(
                        ValidationError(
                            HallucinationType.NONEXISTENT_COLUMN,
                            "critical",
                            f"Chart '{title}' x_axis references non-existent column '{col}'",
                            field=f"charts.{title}.x_axis",
                            suggested_fix=_suggest_column_name(col, available_cols),
                        )
                    )

        # Validate y_axis (can be formula or column)
        if y_axis and not _is_formula(y_axis):
            y_cols = _extract_column_references(y_axis)
            for col in y_cols:
                if col not in available_cols:
                    errors.append(
                        ValidationError(
                            HallucinationType.NONEXISTENT_COLUMN,
                            "critical",
                            f"Chart '{title}' y_axis references non-existent column '{col}'",
                            field=f"charts.{title}.y_axis",
                            suggested_fix=_suggest_column_name(col, available_cols),
                        )
                    )

        # Validate split_by
        if split_by and split_by not in available_cols:
            errors.append(
                ValidationError(
                    HallucinationType.NONEXISTENT_COLUMN,
                    "high",
                    f"Chart '{title}' split_by references non-existent column '{split_by}'",
                    field=f"charts.{title}.split_by",
                    suggested_fix=_suggest_column_name(split_by, available_cols),
                )
            )

    return errors


def validate_formulas(
    data: Dict[str, Any],
    schema: DetectedSchema,
) -> List[ValidationError]:
    """Validate formula syntax and function usage.

    Catches:
    - INVALID_FUNCTION: Function not in allowed list
    - INVALID_SYNTAX: Malformed formula
    - TYPE_MISMATCH: Operation on incompatible types
    """
    errors: List[ValidationError] = []

    # Build column type map
    column_types: Dict[str, Dict[str, str]] = {}
    for s in schema.sheets:
        column_types[s.name] = {c.name: c.inferred_type for c in s.columns}

    # Validate KPI formulas
    for kpi in data.get("kpis", []):
        formula = kpi.get("formula", "")
        label = kpi.get("label", "unnamed")
        sheet = kpi.get("sheet", "")

        # Extract function calls
        functions = _extract_functions(formula)
        for func in functions:
            if func not in ALLOWED_FUNCTIONS:
                errors.append(
                    ValidationError(
                        HallucinationType.INVALID_FUNCTION,
                        "critical",
                        f"KPI '{label}' uses disallowed function '{func}'",
                        field=f"kpis.{label}.formula",
                        suggested_fix=f"Use one of: {', '.join(sorted(ALLOWED_FUNCTIONS))}",
                    )
                )

        # Check syntax
        syntax_error = _check_formula_syntax(formula)
        if syntax_error:
            errors.append(
                ValidationError(
                    HallucinationType.INVALID_SYNTAX,
                    "critical",
                    f"KPI '{label}' has syntax error: {syntax_error}",
                    field=f"kpis.{label}.formula",
                )
            )

        # Type checking (basic)
        if sheet in column_types:
            type_error = _check_type_compatibility(formula, column_types[sheet])
            if type_error:
                errors.append(
                    ValidationError(
                        HallucinationType.TYPE_MISMATCH,
                        "high",
                        f"KPI '{label}' has type error: {type_error}",
                        field=f"kpis.{label}.formula",
                    )
                )

    return errors


def validate_aggregations(
    data: Dict[str, Any],
    schema: DetectedSchema,
    stats_by_sheet: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[ValidationError]:
    """Validate aggregation choices are appropriate for data.

    Catches:
    - INVALID_AGGREGATION: Aggregation type not recognized
    - AGGREGATION_ON_ID_COLUMN: Sum/avg on ID column (unique count ≈ row count)
    - AGGREGATION_ON_TEXT: Numeric aggregation on text column
    """
    errors: List[ValidationError] = []

    # Build column type and cardinality maps
    column_info: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for s in schema.sheets:
        column_info[s.name] = {}
        for c in s.columns:
            info = {
                "type": c.inferred_type,
                "unique_count": None,
                "row_count": s.row_count,
            }
            # Add stats if available
            if stats_by_sheet and s.name in stats_by_sheet:
                col_stat = stats_by_sheet[s.name].get(c.name)
                if col_stat:
                    info["unique_count"] = getattr(col_stat, "unique_count", None)
            column_info[s.name][c.name] = info

    # Validate KPI aggregations
    for kpi in data.get("kpis", []):
        agg = kpi.get("aggregation", "").lower()
        label = kpi.get("label", "unnamed")
        formula = kpi.get("formula", "")
        sheet = kpi.get("sheet", "")

        # Check aggregation is valid
        if agg and agg not in ALLOWED_AGGREGATIONS:
            errors.append(
                ValidationError(
                    HallucinationType.INVALID_AGGREGATION,
                    "high",
                    f"KPI '{label}' uses invalid aggregation '{agg}'",
                    field=f"kpis.{label}.aggregation",
                    suggested_fix=f"Use one of: {', '.join(sorted(ALLOWED_AGGREGATIONS))}",
                )
            )

        # Check if aggregating on ID column
        if agg in ("sum", "avg") and sheet in column_info:
            cols = _extract_column_references(formula)
            for col in cols:
                if col in column_info[sheet]:
                    info = column_info[sheet][col]
                    unique = info.get("unique_count")
                    total = info.get("row_count")

                    # If unique count ≈ row count, likely an ID
                    if unique and total and unique >= 0.9 * total:
                        errors.append(
                            ValidationError(
                                HallucinationType.AGGREGATION_ON_ID_COLUMN,
                                "high",
                                f"KPI '{label}' applies {agg.upper()} to likely ID column '{col}' (unique={unique}, total={total})",
                                field=f"kpis.{label}.formula",
                                suggested_fix="Use COUNT instead, or select a measure column",
                            )
                        )

        # Check numeric aggregation on text column
        if agg in ("sum", "avg", "median", "stddev", "var") and sheet in column_info:
            cols = _extract_column_references(formula)
            for col in cols:
                if col in column_info[sheet]:
                    col_type = column_info[sheet][col].get("type", "").lower()
                    if "str" in col_type or "utf" in col_type or "text" in col_type:
                        errors.append(
                            ValidationError(
                                HallucinationType.AGGREGATION_ON_TEXT,
                                "high",
                                f"KPI '{label}' applies numeric aggregation '{agg}' to text column '{col}'",
                                field=f"kpis.{label}.formula",
                                suggested_fix="Use COUNT or select a numeric column",
                            )
                        )

    # Validate chart aggregations
    for chart in data.get("charts", []):
        agg = chart.get("aggregation", "").lower()
        title = chart.get("title", "untitled")

        if agg and agg not in ALLOWED_AGGREGATIONS:
            errors.append(
                ValidationError(
                    HallucinationType.INVALID_AGGREGATION,
                    "high",
                    f"Chart '{title}' uses invalid aggregation '{agg}'",
                    field=f"charts.{title}.aggregation",
                    suggested_fix=f"Use one of: {', '.join(sorted(ALLOWED_AGGREGATIONS))}",
                )
            )

    return errors


def validate_charts(
    data: Dict[str, Any],
    schema: DetectedSchema,
    stats_by_sheet: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[ValidationError]:
    """Validate chart configurations are semantically correct.

    Catches:
    - INVALID_CHART_TYPE: Chart type not recognized
    - PIE_CHART_TIME_SERIES: Pie chart used for time-series data
    - HIGH_CARDINALITY_AXIS: x_axis or split_by has too many distinct values
    - DUPLICATE_CHART: Same x/y combination
    - REVERSED_AXIS: Categorical on y-axis, numeric on x-axis
    """
    errors: List[ValidationError] = []

    # Build column info
    column_info: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for s in schema.sheets:
        column_info[s.name] = {}
        for c in s.columns:
            info = {
                "type": c.inferred_type,
                "is_date": "date" in c.inferred_type.lower() or "time" in c.inferred_type.lower(),
                "is_numeric": any(t in c.inferred_type.lower() for t in ["int", "float", "decimal", "number"]),
                "unique_count": None,
            }
            if stats_by_sheet and s.name in stats_by_sheet:
                col_stat = stats_by_sheet[s.name].get(c.name)
                if col_stat:
                    info["unique_count"] = getattr(col_stat, "unique_count", None)
            column_info[s.name][c.name] = info

    seen_combinations: Set[Tuple[str, str, str]] = set()

    for chart in data.get("charts", []):
        title = chart.get("title", "untitled")
        chart_type = chart.get("type", "bar")
        sheet = chart.get("sheet", "")
        x_axis = chart.get("x_axis")
        y_axis = chart.get("y_axis")
        split_by = chart.get("split_by")

        # Validate chart type
        if chart_type not in VALID_CHART_TYPES:
            errors.append(
                ValidationError(
                    HallucinationType.INVALID_CHART_TYPE,
                    "high",
                    f"Chart '{title}' has invalid type '{chart_type}'",
                    field=f"charts.{title}.type",
                    suggested_fix=f"Use one of: {', '.join(VALID_CHART_TYPES)}",
                )
            )

        # Check for pie chart with time-series
        if chart_type == "pie" and sheet in column_info:
            x_cols = _extract_column_references(x_axis) if x_axis else []
            for col in x_cols:
                if col in column_info[sheet] and column_info[sheet][col]["is_date"]:
                    errors.append(
                        ValidationError(
                            HallucinationType.PIE_CHART_TIME_SERIES,
                            "high",
                            f"Chart '{title}' uses pie chart for time-series data (x_axis='{col}')",
                            field=f"charts.{title}.type",
                            suggested_fix="Use 'line', 'area', or 'bar' for time-series",
                        )
                    )

        # Check for high cardinality on x_axis
        if sheet in column_info and x_axis:
            x_cols = _extract_column_references(x_axis)
            for col in x_cols:
                if col in column_info[sheet]:
                    unique = column_info[sheet][col].get("unique_count")
                    if unique and unique > 50:
                        errors.append(
                            ValidationError(
                                HallucinationType.HIGH_CARDINALITY_AXIS,
                                "medium",
                                f"Chart '{title}' uses high-cardinality column '{col}' as x_axis ({unique} distinct values)",
                                field=f"charts.{title}.x_axis",
                                suggested_fix="Use a column with fewer distinct values or add filters",
                            )
                        )

        # Check for high cardinality on split_by
        if sheet in column_info and split_by and split_by in column_info[sheet]:
            unique = column_info[sheet][split_by].get("unique_count")
            if unique and unique > 15:
                errors.append(
                    ValidationError(
                        HallucinationType.INAPPROPRIATE_SPLIT_BY,
                        "high",
                        f"Chart '{title}' uses high-cardinality column '{split_by}' as split_by ({unique} distinct values)",
                        field=f"charts.{title}.split_by",
                        suggested_fix="Use a column with ≤15 distinct values or omit split_by",
                    )
                )

        # Check for duplicate charts (same x/y/sheet)
        if x_axis and y_axis and sheet:
            combo = (sheet, x_axis, y_axis)
            if combo in seen_combinations:
                errors.append(
                    ValidationError(
                        HallucinationType.DUPLICATE_CHART,
                        "low",
                        f"Chart '{title}' is duplicate of another chart (sheet='{sheet}', x='{x_axis}', y='{y_axis}')",
                        field=f"charts.{title}",
                        suggested_fix="Remove duplicate or vary x/y/split_by",
                    )
                )
            seen_combinations.add(combo)

        # Check for reversed axes (categorical on y, numeric on x)
        if sheet in column_info and x_axis and y_axis:
            x_cols = _extract_column_references(x_axis)
            y_cols = _extract_column_references(y_axis)
            if x_cols and y_cols:
                x_col = x_cols[0]
                y_col = y_cols[0]
                if x_col in column_info[sheet] and y_col in column_info[sheet]:
                    x_is_numeric = column_info[sheet][x_col]["is_numeric"]
                    y_is_numeric = column_info[sheet][y_col]["is_numeric"]
                    y_is_cat = not y_is_numeric and not column_info[sheet][y_col]["is_date"]

                    if x_is_numeric and y_is_cat:
                        errors.append(
                            ValidationError(
                                HallucinationType.REVERSED_AXIS,
                                "medium",
                                f"Chart '{title}' has numeric x_axis ('{x_col}') and categorical y_axis ('{y_col}')",
                                field=f"charts.{title}",
                                suggested_fix="Swap x_axis and y_axis",
                            )
                        )

    return errors


def validate_joins(
    data: Dict[str, Any],
    schema: DetectedSchema,
) -> List[ValidationError]:
    """Validate join configurations are possible.

    Catches:
    - IMPOSSIBLE_JOIN: Sheets don't have common columns
    - MISSING_JOIN_KEY: Join missing 'on' or 'left_on'+'right_on'
    - TYPE_INCOMPATIBLE_JOIN: Join key types don't match
    """
    errors: List[ValidationError] = []

    # Build sheet info
    sheet_columns: Dict[str, Dict[str, str]] = {}
    for s in schema.sheets:
        sheet_columns[s.name] = {c.name: c.inferred_type for c in s.columns}

    for join in data.get("joins", []):
        left_sheet = join.get("left_sheet", "")
        right_sheet = join.get("right_sheet", "")
        on_col = join.get("on")
        left_on = join.get("left_on")
        right_on = join.get("right_on")

        # Check sheets exist
        if left_sheet not in sheet_columns:
            errors.append(
                ValidationError(
                    HallucinationType.NONEXISTENT_SHEET,
                    "critical",
                    f"Join references non-existent left sheet '{left_sheet}'",
                    field=f"joins.{left_sheet}+{right_sheet}.left_sheet",
                )
            )
            continue

        if right_sheet not in sheet_columns:
            errors.append(
                ValidationError(
                    HallucinationType.NONEXISTENT_SHEET,
                    "critical",
                    f"Join references non-existent right sheet '{right_sheet}'",
                    field=f"joins.{left_sheet}+{right_sheet}.right_sheet",
                )
            )
            continue

        # Check join keys present
        if not on_col and not (left_on and right_on):
            errors.append(
                ValidationError(
                    HallucinationType.MISSING_JOIN_KEY,
                    "critical",
                    f"Join between '{left_sheet}' and '{right_sheet}' missing join keys",
                    field=f"joins.{left_sheet}+{right_sheet}",
                    suggested_fix="Specify 'on' or both 'left_on' and 'right_on'",
                )
            )
            continue

        # Validate join key columns exist and types match
        if on_col:
            if on_col not in sheet_columns[left_sheet]:
                errors.append(
                    ValidationError(
                        HallucinationType.NONEXISTENT_COLUMN,
                        "critical",
                        f"Join key '{on_col}' not found in left sheet '{left_sheet}'",
                        field=f"joins.{left_sheet}+{right_sheet}.on",
                    )
                )
            if on_col not in sheet_columns[right_sheet]:
                errors.append(
                    ValidationError(
                        HallucinationType.NONEXISTENT_COLUMN,
                        "critical",
                        f"Join key '{on_col}' not found in right sheet '{right_sheet}'",
                        field=f"joins.{left_sheet}+{right_sheet}.on",
                    )
                )

            # Check type compatibility
            if on_col in sheet_columns[left_sheet] and on_col in sheet_columns[right_sheet]:
                left_type = sheet_columns[left_sheet][on_col]
                right_type = sheet_columns[right_sheet][on_col]
                if not _types_compatible(left_type, right_type):
                    errors.append(
                        ValidationError(
                            HallucinationType.TYPE_INCOMPATIBLE_JOIN,
                            "high",
                            f"Join key '{on_col}' has incompatible types: {left_type} vs {right_type}",
                            field=f"joins.{left_sheet}+{right_sheet}.on",
                            suggested_fix="Cast one column to match the other type",
                        )
                    )

        elif left_on and right_on:
            if left_on not in sheet_columns[left_sheet]:
                errors.append(
                    ValidationError(
                        HallucinationType.NONEXISTENT_COLUMN,
                        "critical",
                        f"Join left_on '{left_on}' not found in sheet '{left_sheet}'",
                        field=f"joins.{left_sheet}+{right_sheet}.left_on",
                    )
                )
            if right_on not in sheet_columns[right_sheet]:
                errors.append(
                    ValidationError(
                        HallucinationType.NONEXISTENT_COLUMN,
                        "critical",
                        f"Join right_on '{right_on}' not found in sheet '{right_sheet}'",
                        field=f"joins.{left_sheet}+{right_sheet}.right_on",
                    )
                )

            # Check type compatibility
            if left_on in sheet_columns[left_sheet] and right_on in sheet_columns[right_sheet]:
                left_type = sheet_columns[left_sheet][left_on]
                right_type = sheet_columns[right_sheet][right_on]
                if not _types_compatible(left_type, right_type):
                    errors.append(
                        ValidationError(
                            HallucinationType.TYPE_INCOMPATIBLE_JOIN,
                            "high",
                            f"Join keys have incompatible types: {left_on}({left_type}) vs {right_on}({right_type})",
                            field=f"joins.{left_sheet}+{right_sheet}",
                            suggested_fix="Cast one column to match the other type",
                        )
                    )

    return errors


def validate_semantic_quality(
    data: Dict[str, Any],
) -> List[ValidationError]:
    """Validate semantic quality of suggestions.

    Catches:
    - MEANINGLESS_KPI: KPI with no business value (e.g. "COUNT of ID")
    """
    errors: List[ValidationError] = []

    # Check for meaningless KPIs
    for kpi in data.get("kpis", []):
        label = kpi.get("label", "").lower()
        formula = kpi.get("formula", "").lower()
        agg = kpi.get("aggregation", "").lower()

        # Pattern: COUNT(ID), SUM(ID), etc.
        if agg in ("count", "sum", "avg") and ("id" in formula or "key" in formula):
            if "unique" not in label and "distinct" not in label:
                errors.append(
                    ValidationError(
                        HallucinationType.MEANINGLESS_KPI,
                        "low",
                        f"KPI '{kpi.get('label')}' may not provide business value (aggregating ID/key columns)",
                        field=f"kpis.{kpi.get('label')}",
                        suggested_fix="Use COUNT(DISTINCT ...) or select a measure column",
                    )
                )

    return errors


# === Master Validation Function ===


def validate_llm_output(
    data: Dict[str, Any],
    schema: DetectedSchema,
    stats_by_sheet: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], List[ValidationError]]:
    """Run all validation checks on LLM output.

    Returns:
        Tuple of (cleaned_data, all_errors)
        - cleaned_data: Data with critical errors removed, high errors flagged
        - all_errors: List of all validation errors found
    """
    all_errors: List[ValidationError] = []

    # Run all validation checks
    all_errors.extend(validate_schema_references(data, schema))
    all_errors.extend(validate_formulas(data, schema))
    all_errors.extend(validate_aggregations(data, schema, stats_by_sheet))
    all_errors.extend(validate_charts(data, schema, stats_by_sheet))
    all_errors.extend(validate_joins(data, schema))
    all_errors.extend(validate_semantic_quality(data))

    # Log errors
    critical_count = sum(1 for e in all_errors if e.severity == "critical")
    high_count = sum(1 for e in all_errors if e.severity == "high")
    medium_count = sum(1 for e in all_errors if e.severity == "medium")
    low_count = sum(1 for e in all_errors if e.severity == "low")

    logger.info(
        "LLM output validation completed",
        critical=critical_count,
        high=high_count,
        medium=medium_count,
        low=low_count,
        total=len(all_errors),
    )

    # Remove items with critical errors
    cleaned_data = _remove_critical_errors(data, all_errors)

    return cleaned_data, all_errors


def _remove_critical_errors(
    data: Dict[str, Any],
    errors: List[ValidationError],
) -> Dict[str, Any]:
    """Remove KPIs/charts/joins with critical validation errors."""
    critical_fields = {e.field for e in errors if e.severity == "critical" and e.field}

    cleaned = data.copy()

    # Filter KPIs
    valid_kpis = []
    for kpi in data.get("kpis", []):
        label = kpi.get("label", "unnamed")
        if not any(f"kpis.{label}" in field for field in critical_fields):
            valid_kpis.append(kpi)
        else:
            logger.warning(f"Removing KPI '{label}' due to critical validation errors")
    cleaned["kpis"] = valid_kpis

    # Filter charts
    valid_charts = []
    for chart in data.get("charts", []):
        title = chart.get("title", "untitled")
        if not any(f"charts.{title}" in field for field in critical_fields):
            valid_charts.append(chart)
        else:
            logger.warning(f"Removing chart '{title}' due to critical validation errors")
    cleaned["charts"] = valid_charts

    # Filter joins
    valid_joins = []
    for join in data.get("joins", []):
        left = join.get("left_sheet", "")
        right = join.get("right_sheet", "")
        if not any(f"joins.{left}+{right}" in field for field in critical_fields):
            valid_joins.append(join)
        else:
            logger.warning(f"Removing join '{left}+{right}' due to critical validation errors")
    cleaned["joins"] = valid_joins

    return cleaned


# === Helper Functions ===


def _is_valid_sheet_reference(sheet: str, all_sheets: Set[str]) -> bool:
    """Check if sheet name or joined sheet name (A+B) is valid."""
    if not sheet:
        return False
    if sheet in all_sheets:
        return True
    # Check if it's a valid joined sheet (A+B)
    parts = [p.strip() for p in sheet.split("+")]
    return len(parts) > 1 and all(p in all_sheets for p in parts)


def _resolve_sheet_columns(
    sheet: str,
    all_sheets: Set[str],
    sheet_columns: Dict[str, Set[str]],
) -> Set[str]:
    """Get available columns for a sheet (including joined sheets)."""
    if sheet in sheet_columns:
        return sheet_columns[sheet]

    # Handle joined sheets (A+B)
    parts = [p.strip() for p in sheet.split("+")]
    if len(parts) > 1 and all(p in all_sheets for p in parts):
        cols = set()
        for p in parts:
            cols.update(sheet_columns.get(p, set()))
        return cols

    return set()


def _extract_column_references(formula: str) -> List[str]:
    """Extract column names from formula, excluding function names."""
    if not formula:
        return []

    # Find all word tokens
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_\s]*\b", formula)

    # Filter out known functions and keywords
    excluded = ALLOWED_FUNCTIONS | {"AND", "OR", "NOT", "TRUE", "FALSE"}

    columns = []
    for token in tokens:
        token_clean = token.strip().upper()
        if token_clean not in excluded:
            columns.append(token.strip())

    return columns


def _extract_functions(formula: str) -> List[str]:
    """Extract function names from formula."""
    if not formula:
        return []

    # Match function calls: FUNC_NAME(
    pattern = r"\b([A-Z_]+)\s*\("
    matches = re.findall(pattern, formula.upper())
    return list(set(matches))


def _is_formula(text: str) -> bool:
    """Check if text looks like a formula (contains functions or operators)."""
    if not text:
        return False
    return bool(re.search(r"[+\-*/()]|[A-Z_]+\(", text))


def _check_formula_syntax(formula: str) -> Optional[str]:
    """Basic syntax check for formulas. Returns error message or None."""
    if not formula:
        return "Empty formula"

    # Check balanced parentheses
    open_count = formula.count("(")
    close_count = formula.count(")")
    if open_count != close_count:
        return f"Unbalanced parentheses: {open_count} open, {close_count} close"

    # Check for empty parentheses
    if re.search(r"\(\s*\)", formula):
        return "Empty parentheses found"

    # Check for double operators
    if re.search(r"[+\-*/]{2,}", formula):
        return "Consecutive operators found"

    return None


def _check_type_compatibility(
    formula: str,
    column_types: Dict[str, str],
) -> Optional[str]:
    """Basic type checking for formulas. Returns error message or None."""
    # Extract columns
    columns = _extract_column_references(formula)

    # Check if numeric operations on text columns
    has_numeric_op = bool(re.search(r"[+\-*/]", formula))
    functions = _extract_functions(formula)
    has_numeric_func = bool(set(functions) & {"SUM", "AVG", "MEDIAN", "STDEV", "VAR"})

    if has_numeric_op or has_numeric_func:
        for col in columns:
            if col in column_types:
                col_type = column_types[col].lower()
                if "str" in col_type or "utf" in col_type or "text" in col_type:
                    return f"Numeric operation on text column '{col}'"

    return None


def _types_compatible(type1: str, type2: str) -> bool:
    """Check if two types are compatible for joins."""
    t1 = type1.lower()
    t2 = type2.lower()

    # Exact match
    if t1 == t2:
        return True

    # Numeric types are compatible with each other
    numeric = {"int", "float", "decimal", "number", "int32", "int64", "float32", "float64"}
    if any(n in t1 for n in numeric) and any(n in t2 for n in numeric):
        return True

    # String types are compatible with each other
    string = {"str", "utf", "string", "text"}
    if any(s in t1 for s in string) and any(s in t2 for s in string):
        return True

    return False


def _find_sheet_with_column(
    column: str,
    sheet_columns: Dict[str, Set[str]],
) -> Optional[str]:
    """Find which sheet contains a given column."""
    for sheet, cols in sheet_columns.items():
        if column in cols:
            return sheet
    return None


def _suggest_column_name(query: str, available: Set[str]) -> Optional[str]:
    """Suggest a column name using fuzzy matching."""
    if not query or not available:
        return None

    query_lower = query.lower().replace("_", "").replace(" ", "")

    # Try exact match (case-insensitive)
    for col in available:
        if col.lower() == query.lower():
            return col

    # Try substring match
    matches = [col for col in available if query_lower in col.lower().replace("_", "").replace(" ", "")]
    if matches:
        return matches[0]

    # Try reverse substring
    matches = [col for col in available if col.lower().replace("_", "").replace(" ", "") in query_lower]
    if matches:
        return matches[0]

    return None


def _suggest_sheet_name(query: str, available: Set[str]) -> Optional[str]:
    """Suggest a sheet name using fuzzy matching."""
    return _suggest_column_name(query, available)
