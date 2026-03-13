import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import polars as pl
import structlog

from app.pipeline import formula_engine
from app.pipeline.llm_enricher import LLMEnrichment
from app.pipeline.schema_detector import DetectedSchema
from app.pipeline.stats_engine import FileStats
from app.utils.columns import get_valid_column

logger = structlog.get_logger()


# Removed local get_valid_column (moved to app.utils.columns)


def find_date_columns(schema: DetectedSchema, sheet_name: str) -> List[str]:
    """Extract list of date/time column names for a given sheet."""
    # Optimization: Use O(1) sheet lookup
    sheet = next((s for s in schema.sheets if s.name == sheet_name), None)
    if not sheet:
        return []

    date_cols = [c.name for c in sheet.columns if "Date" in c.inferred_type or "Time" in c.inferred_type]
    # Fallback: column name suggests date/time when inferred_type is String
    if not date_cols:
        date_cols = [
            c.name for c in sheet.columns if "date" in (c.name or "").lower() or "time" in (c.name or "").lower()
        ]
    return date_cols


def detect_correlation_insights(
    dataframes: Dict[str, pl.DataFrame],
    schema: DetectedSchema,
    threshold: float = 0.7,
) -> List[Dict[str, Any]]:
    """Detect interesting correlations between numeric columns and generate insights.

    Args:
        dataframes: Dictionary of sheet_name -> DataFrame
        schema: Detected schema with column information
        threshold: Minimum absolute correlation value to report (default 0.7)

    Returns:
        List of insight dictionaries with correlation findings
    """
    insights = []

    for sheet in schema.sheets:
        if sheet.name not in dataframes:
            continue

        df = dataframes[sheet.name]

        # Find numeric columns
        numeric_cols = []
        for col in sheet.columns:
            col_type = (col.inferred_type or "").lower()
            if any(t in col_type for t in ["int", "float", "decimal", "number"]) and col.name in df.columns:
                numeric_cols.append(col.name)

        # Need at least 2 numeric columns for correlation
        if len(numeric_cols) < 2:
            continue

        # Check pairs of numeric columns
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1 :]:
                try:
                    # Compute correlation
                    corr_value = df.select(pl.corr(col1, col2)).item()

                    if corr_value is None or abs(corr_value) < threshold:
                        continue

                    # Generate insight based on correlation strength and direction
                    if corr_value > 0:
                        direction = "positive"
                        interpretation = "increase together"
                    else:
                        direction = "negative"
                        interpretation = "move in opposite directions"

                    if abs(corr_value) >= 0.9:
                        strength = "very strong"
                        severity = "high"
                    elif abs(corr_value) >= 0.7:
                        strength = "strong"
                        severity = "medium"
                    else:
                        strength = "moderate"
                        severity = "info"

                    insights.append(
                        {
                            "type": "correlation",
                            "severity": severity,
                            "title": f"{strength.title()} {direction.title()} Correlation Detected",
                            "text": f"{col1} and {col2} show a {strength} {direction} correlation ({corr_value:.2f}) in '{sheet.name}' - they {interpretation}.",
                            "metadata": {
                                "sheet": sheet.name,
                                "column1": col1,
                                "column2": col2,
                                "correlation": round(corr_value, 3),
                                "direction": direction,
                            },
                        }
                    )

                except Exception as e:
                    logger.debug(f"Could not compute correlation between {col1} and {col2}: {e}")
                    continue

    return insights


def smart_format_value(val: Optional[float], unit: Optional[str], fmt: Optional[str]) -> tuple:
    """
    Abbreviate large numbers and round time values.
    Returns (formatted_value, final_unit).
    """
    if val is None:
        return val, unit

    # Units that already encode a magnitude — applying M/K prefixes would double-scale.
    MAGNITUDE_UNITS = {
        "billions",
        "billion",
        "millions",
        "million",
        "milliards",
        "milliard",
        "trillions",
        "trillion",
        "thousands",
        "thousand",
        "k",
        "m",
        "b",
        "t",
    }
    unit_norm = unit.strip().lower() if unit else None
    # Skip magnitude prefix when unit itself already encodes scale
    is_magnitude_unit = unit_norm in MAGNITUDE_UNITS

    try:
        f_val = float(val)
        abs_val = abs(f_val)
        sign = 1.0 if f_val >= 0 else -1.0
    except (ValueError, TypeError):
        return val, unit

    # Improved magnitude detection: check if the unit itself already implies a magnitude
    is_scale_in_unit = any(m in unit_norm for m in MAGNITUDE_UNITS) if unit_norm else False

    if not (is_magnitude_unit or is_scale_in_unit):
        if abs_val >= 1_000_000:
            if unit:
                return round(sign * abs_val / 1_000_000, 2), f"M {unit}"
        elif abs_val >= 10_000:
            if unit:
                return round(sign * abs_val / 1_000, 1), f"K {unit}"

    if unit_norm in ("min", "h", "days", "hours", "minutes"):
        return round(f_val, 1), unit

    return val, unit


def infer_agg_type(df: pl.DataFrame, col_name: str, suggested_agg: Optional[str]) -> str:
    """Intelligently infer aggregation if missing or invalid for the data type."""
    if suggested_agg:
        return suggested_agg.lower()

    if col_name not in df.columns:
        return "count"
    dtype = df[col_name].dtype

    # If the column is already numeric type, prefer sum
    if dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32, pl.Decimal]:
        return "sum"

    # If column is a string but looks numeric (common when CSV imports numeric as strings),
    # attempt a quick sample parse to decide.
    try:
        if dtype == pl.Utf8 or str(dtype).lower().startswith("data_type::str") or str(dtype).lower().startswith("utf8"):
            sample = df[col_name].drop_nulls().head(200).to_series().to_list()
            if sample:
                numeric_hits = 0
                total = 0
                for v in sample:
                    total += 1
                    s = str(v).strip()
                    # empty or common placeholders are non-numeric
                    if s in ("", "None", "null", "-"):
                        continue
                    # Remove thousands separators and trailing currency symbols
                    s_clean = s.replace(",", "").replace(" ", "")
                    # strip common currency symbols
                    s_clean = s_clean.strip().lstrip("€$£¥").rstrip("€$£¥%")
                    try:
                        float(s_clean)
                        numeric_hits += 1
                    except Exception:
                        continue

                # If a majority of the sample looks numeric, treat as numeric
                if total > 0 and (numeric_hits / total) >= 0.6:
                    return "sum"
    except Exception:
        pass

    return "count"


def smart_convert_time_values(values: List[float], base_unit: str = "sec") -> tuple[str, List[float]]:
    """
    Intelligently convert time values to appropriate units.
    The input values are expressed in *base_unit* which defaults to seconds.
    Supported base units: "sec", "min", "h" (hours), "days".
    The function first normalizes everything to seconds, then chooses a
    friendly display unit (ms/sec/min/h/days) based on the range of the
    data and returns the converted values along with the unit label.
    """
    if not values or all(v is None for v in values):
        return "sec", values

    # multiplier to convert from base_unit to seconds
    mult_map = {"sec": 1, "min": 60, "h": 3600, "days": 86400}
    mult = mult_map.get(base_unit.lower(), 1)

    # Convert to seconds for uniform processing
    secs = [(v * mult) if v is not None else None for v in values]

    # Filter out None/null values for analysis
    valid_values = [v for v in secs if v is not None and isinstance(v, (int, float))]
    if not valid_values:
        return "sec", values

    # Get maximum magnitude (absolute value) in seconds to determine display unit
    max_val = max(abs(v) for v in valid_values)

    # Decide unit based on magnitude of the maximum value in seconds
    if max_val < 1:
        # Less than 1 second → milliseconds
        unit = "ms"
        converted_secs = [v * 1000 if v is not None else None for v in secs]
    elif max_val < 60:
        # Less than 60 seconds → seconds
        unit = "sec"
        converted_secs = secs
    elif max_val < 3600:
        # Less than 1 hour → minutes
        unit = "min"
        converted_secs = [v / 60 if v is not None else None for v in secs]
    elif max_val < 86400:
        # Less than 1 day → hours
        unit = "h"
        converted_secs = [v / 3600 if v is not None else None for v in secs]
    else:
        # Greater than 1 day → days
        unit = "days"
        converted_secs = [v / 86400 if v is not None else None for v in secs]

    # converted_secs are in the chosen unit already (e.g. hours)
    return unit, converted_secs


def normalize_boolean_column(df: pl.DataFrame, col_name: str) -> pl.DataFrame:
    """
    Detects if a string column behaves like a boolean and normalizes it.
    """
    if df[col_name].dtype != pl.String:
        return df

    try:
        # Performance: Head(20) unique is enough for boolean detection
        unique_vals = df[col_name].drop_nulls().unique().head(20).to_list()
        if not unique_vals:
            return df

        unique_vals_norm = [str(v).strip().lower() for v in unique_vals]

        bool_true = {
            "yes",
            "true",
            "1",
            "oui",
            "y",
            "o",
            "vrai",
            "v",
            "ok",
            "pass",
            "success",
            "valide",
            "returned",
            "retour",
            "bille",
            "billed",
            "paye",
            "paid",
            "complete",
            "termine",
            "dangereux",
            "dangerous",
            "empty",
            "vide",
        }
        bool_false = {
            "no",
            "false",
            "0",
            "non",
            "n",
            "faux",
            "f",
            "ko",
            "fail",
            "failed",
            "echoue",
            "not returned",
            "non bille",
            "unbilled",
            "impaye",
            "unpaid",
            "pending",
            "en cours",
            "non dangereux",
            "secure",
            "full",
            "plein",
        }

        if all(v in bool_true or v in bool_false for v in unique_vals_norm):
            true_list = list(bool_true)
            false_list = list(bool_false)
            return df.with_columns(
                pl.when(pl.col(col_name).str.strip_chars().str.to_lowercase().is_in(true_list))
                .then(1.0)
                .when(pl.col(col_name).str.strip_chars().str.to_lowercase().is_in(false_list))
                .then(0.0)
                .otherwise(None)
                .alias(col_name)
            )
    except Exception:
        pass

    return df


def align_fk_types(dataframes: Dict[str, pl.DataFrame], schema: DetectedSchema) -> None:
    """Align FK column types to PK types for relationships. Mutates dataframes in place."""
    numeric_dtypes = (pl.Int64, pl.Int32, pl.Float64, pl.Float32, pl.Decimal)
    for rel in getattr(schema, "relationships", []) or []:
        left_df = dataframes.get(rel.from_sheet)
        right_df = dataframes.get(rel.to_sheet)
        if left_df is None or right_df is None:
            continue
        fk_col, pk_col = rel.from_col, rel.to_col
        if fk_col not in left_df.columns or pk_col not in right_df.columns:
            continue
        if left_df[fk_col].dtype == right_df[pk_col].dtype:
            continue
        try:
            pk_dtype = right_df[pk_col].dtype
            fk_dtype = left_df[fk_col].dtype
            new_type_str = None
            if pk_dtype in numeric_dtypes and fk_dtype == pl.Utf8:
                aligned = left_df.with_columns(pl.col(fk_col).cast(pk_dtype, strict=False))
                if aligned[fk_col].null_count() < len(aligned):
                    dataframes[rel.from_sheet] = aligned
                    new_type_str = str(pk_dtype)
            elif pk_dtype == pl.Utf8 and fk_dtype in numeric_dtypes:
                dataframes[rel.from_sheet] = left_df.with_columns(pl.col(fk_col).cast(pl.Utf8))
                new_type_str = "Utf8"
            if new_type_str:
                for s in schema.sheets:
                    if s.name == rel.from_sheet:
                        for c in s.columns:
                            if c.name == fk_col:
                                c.inferred_type = new_type_str
                                break
                        break
        except Exception as e:
            logger.debug("align_fk_types skipped", from_sheet=rel.from_sheet, col=fk_col, error=str(e))


def build_dashboard(
    dataframes: Dict[str, pl.DataFrame], schema: DetectedSchema, stats: FileStats, enrichment: LLMEnrichment
) -> Dict[str, Any]:
    """
    Final assembly of the dashboard configuration.
    Actually computes the suggested KPIs and downsamples chart data.
    """
    align_fk_types(dataframes, schema)

    dashboard: Dict[str, Any] = {
        "overview": {
            "domain": enrichment.domain,
            "summary": enrichment.summary,
            "sheet_count": len(schema.sheets),
            "total_rows": sum(s.row_count for s in schema.sheets),
        },
        "kpis": [],
        "charts": [],
        "insights": enrichment.insights,
        "data_preview": {},
    }

    # Expose dataset_profile so the frontend and any downstream tooling
    # can understand how the engine/LLM perceived the dataset.
    if getattr(enrichment, "dataset_profile", None) is not None:
        try:
            dashboard["dataset_profile"] = enrichment.dataset_profile.model_dump()
        except Exception:
            # Be defensive – if anything goes wrong here, don't break dashboard build.
            logger.exception("Failed to serialise dataset_profile into dashboard")

    # 0. Join Engine: Create virtual joined sheets
    all_dfs = {**dataframes}
    if enrichment.joins:
        for join in enrichment.joins:

            def get_j(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)

            left_sheet = get_j(join, "left_sheet")
            right_sheet = get_j(join, "right_sheet")
            # Support either a single 'on' column or explicit left_on/right_on
            on_col = get_j(join, "on")
            left_on = get_j(join, "left_on")
            right_on = get_j(join, "right_on")
            how_val = get_j(join, "how", "inner")

            left_df = all_dfs.get(left_sheet)
            right_df = all_dfs.get(right_sheet)
            if left_df is None or right_df is None:
                continue

            joined_name = f"{left_sheet}+{right_sheet}"
            try:
                l_cols = set(left_df.columns)
                r_cols = set(right_df.columns)

                # Determine join keys
                if left_on and right_on:
                    use_left_on, use_right_on = left_on, right_on
                elif on_col:
                    # If same name exists on both sides, use it
                    if on_col in l_cols and on_col in r_cols:
                        use_left_on = use_right_on = on_col
                    else:
                        # Try to find matching column by case-insensitive name
                        lower_l = {c.lower(): c for c in l_cols}
                        lower_r = {c.lower(): c for c in r_cols}
                        if on_col.lower() in lower_l and on_col.lower() in lower_r:
                            use_left_on = lower_l[on_col.lower()]
                            use_right_on = lower_r[on_col.lower()]
                        else:
                            # Fallback: pick any common column name if present
                            common = l_cols.intersection(r_cols)
                            if common:
                                use_left_on = use_right_on = sorted(common)[0]
                            else:
                                # Try to match by lowercase intersection
                                common_lower = set(c.lower() for c in l_cols).intersection(c.lower() for c in r_cols)
                                if common_lower:
                                    # Map to actual names
                                    cl = {c.lower(): c for c in l_cols}
                                    cr = {c.lower(): c for c in r_cols}
                                    key = sorted(common_lower)[0]
                                    use_left_on = cl[key]
                                    use_right_on = cr[key]
                                else:
                                    # No plausible join key found
                                    logger.warning(
                                        "Join skipped - no matching join keys", left=left_sheet, right=right_sheet
                                    )
                                    continue
                else:
                    # No join keys provided at all: try common columns
                    common = l_cols.intersection(r_cols)
                    if common:
                        use_left_on = use_right_on = sorted(common)[0]
                    else:
                        logger.warning(
                            "Join skipped - no join keys and no common columns", left=left_sheet, right=right_sheet
                        )
                        continue

                # Ensure types align (prefer PK/numeric type; fallback to String)
                if use_left_on in left_df.columns and use_right_on in right_df.columns:
                    lt, rt = left_df[use_left_on].dtype, right_df[use_right_on].dtype
                    if lt != rt:
                        numeric = (pl.Int64, pl.Int32, pl.Float64, pl.Float32)
                        if rt in numeric and lt == pl.Utf8:
                            left_df = left_df.with_columns(pl.col(use_left_on).cast(rt, strict=False))
                            all_dfs[left_sheet] = left_df
                        elif lt in numeric and rt == pl.Utf8:
                            right_df = right_df.with_columns(pl.col(use_right_on).cast(lt, strict=False))
                            all_dfs[right_sheet] = right_df
                        else:
                            left_df = left_df.with_columns(pl.col(use_left_on).cast(pl.String))
                            right_df = right_df.with_columns(pl.col(use_right_on).cast(pl.String))
                            all_dfs[left_sheet] = left_df
                            all_dfs[right_sheet] = right_df

                # Perform join using explicit left_on/right_on when names differ
                if use_left_on == use_right_on:
                    joined_df = left_df.join(right_df, on=use_left_on, how=how_val)
                else:
                    joined_df = left_df.join(right_df, left_on=use_left_on, right_on=use_right_on, how=how_val)

                all_dfs[joined_name] = joined_df
            except Exception as e:
                logger.error("Join failed", left=left_sheet, right=right_sheet, error=str(e))

    def _get_or_build_df(sheet_name: str) -> Optional[pl.DataFrame]:
        """Return a real or virtual DataFrame; supports chained joined sheets (A+B+C)."""
        if not sheet_name:
            return None
        existing = all_dfs.get(sheet_name)
        if existing is not None:
            return existing
        if "+" not in sheet_name:
            return None

        parts = [p.strip() for p in sheet_name.split("+") if p and p.strip()]
        if len(parts) < 2:
            return None

        # Build progressively and cache intermediate names, e.g. A+B, A+B+C
        cur_df = all_dfs.get(parts[0])
        if cur_df is None:
            return None
        joined_parts: list[str] = [parts[0]]
        joined_set: set[str] = {parts[0]}

        # Helper to access join attributes or dict keys safely
        def get_j(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        for next_part in parts[1:]:
            right_df = all_dfs.get(next_part)
            if right_df is None:
                return None

            how_val = "inner"
            use_left_on = None
            use_right_on = None

            # Prefer a join recommendation connecting any already-joined part to the next part.
            joins = getattr(enrichment, "joins", []) or []
            preferred_left = joined_parts[-1] if joined_parts else None
            candidate_lefts = [preferred_left] + [p for p in joined_parts if p != preferred_left]
            chosen = None
            for left_candidate in candidate_lefts:
                if not left_candidate:
                    continue
                for j in joins:
                    l = get_j(j, "left_sheet")
                    r = get_j(j, "right_sheet")
                    if {l, r} == {left_candidate, next_part}:
                        chosen = j
                        break
                if chosen:
                    break

            cur_cols = set(cur_df.columns)
            right_cols = set(right_df.columns)
            if chosen is not None:
                how_val = get_j(chosen, "how", "inner")
                on_col = get_j(chosen, "on")
                left_on = get_j(chosen, "left_on")
                right_on = get_j(chosen, "right_on")

                if left_on and right_on:
                    # Determine orientation: which side is the current joined df?
                    l = get_j(chosen, "left_sheet")
                    r = get_j(chosen, "right_sheet")
                    if l in joined_set and r == next_part:
                        use_left_on, use_right_on = left_on, right_on
                    elif r in joined_set and l == next_part:
                        use_left_on, use_right_on = right_on, left_on
                elif on_col:
                    # Use on_col if present on both sides; otherwise attempt case-insensitive match.
                    if on_col in cur_cols and on_col in right_cols:
                        use_left_on = use_right_on = on_col
                    else:
                        lower_l = {c.lower(): c for c in cur_cols}
                        lower_r = {c.lower(): c for c in right_cols}
                        if on_col.lower() in lower_l and on_col.lower() in lower_r:
                            use_left_on = lower_l[on_col.lower()]
                            use_right_on = lower_r[on_col.lower()]

            # Fallback: first common column name if we still don't have join keys
            if not use_left_on or not use_right_on:
                common = cur_cols.intersection(right_cols)
                if common:
                    k = sorted(common)[0]
                    use_left_on = use_right_on = k
                else:
                    common_lower = set(c.lower() for c in cur_cols).intersection(c.lower() for c in right_cols)
                    if common_lower:
                        cl = {c.lower(): c for c in cur_cols}
                        cr = {c.lower(): c for c in right_cols}
                        key = sorted(common_lower)[0]
                        use_left_on = cl[key]
                        use_right_on = cr[key]
                    else:
                        logger.warning(
                            "Chained join skipped - no matching join keys", left="+".join(joined_parts), right=next_part
                        )
                        return None

            # Ensure types align for join keys (prefer numeric; fallback to String)
            try:
                if use_left_on in cur_df.columns and use_right_on in right_df.columns:
                    lt, rt = cur_df[use_left_on].dtype, right_df[use_right_on].dtype
                    if lt != rt:
                        numeric = (pl.Int64, pl.Int32, pl.Float64, pl.Float32)
                        if rt in numeric and lt == pl.Utf8:
                            cur_df = cur_df.with_columns(pl.col(use_left_on).cast(rt, strict=False))
                        elif lt in numeric and rt == pl.Utf8:
                            right_df = right_df.with_columns(pl.col(use_right_on).cast(lt, strict=False))
                        else:
                            cur_df = cur_df.with_columns(pl.col(use_left_on).cast(pl.String))
                            right_df = right_df.with_columns(pl.col(use_right_on).cast(pl.String))
            except Exception:
                pass

            try:
                if use_left_on == use_right_on:
                    cur_df = cur_df.join(right_df, on=use_left_on, how=how_val)
                else:
                    cur_df = cur_df.join(right_df, left_on=use_left_on, right_on=use_right_on, how=how_val)
            except Exception as e:
                logger.error("Chained join failed", left="+".join(joined_parts), right=next_part, error=str(e))
                return None

            joined_parts.append(next_part)
            joined_set.add(next_part)
            virtual_name = "+".join(joined_parts)
            all_dfs[virtual_name] = cur_df

        return all_dfs.get(sheet_name)

    # 1. Compute actual values for suggested KPIs
    # Deduplicate KPIs to avoid showing repeated metrics when the LLM emits
    # the same formula under different labels/titles.
    def _normalize_formula(s: Any) -> str:
        try:
            import re as _re

            out = str(s or "").strip().lower()
            out = _re.sub(r"\s+", " ", out)
            while out.startswith("(") and out.endswith(")"):
                out = out[1:-1].strip()
            return out
        except Exception:
            return ""

    seen_kpi_signatures: set[str] = set()
    for kpi in enrichment.kpis:

        def get_k(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        kpi_sheet = get_k(kpi, "sheet")
        kpi_formula = get_k(kpi, "formula")
        kpi_label = get_k(kpi, "label", "unnamed")
        kpi_unit = get_k(kpi, "unit")
        kpi_format = get_k(kpi, "format", "number")
        kpi_priority = get_k(kpi, "priority", "medium")
        kpi_desc = get_k(kpi, "description")
        kpi_group_by = get_k(kpi, "group_by")

        # Fallback: infer group_by from "per X" label when missing (any file: match suffix to actual columns)
        if not kpi_group_by and kpi_label and " per " in kpi_label.lower():
            suffix = kpi_label.lower().split(" per ")[-1].strip().replace(" ", "")
            df_for_infer = _get_or_build_df(kpi_sheet)
            if df_for_infer is not None:
                cols_lower = {c.lower(): c for c in df_for_infer.columns}
                # Prefer exact match, then suffix+id, then column containing suffix
                candidates = [f"{suffix}id", suffix] if suffix else []
                for cand in candidates:
                    if get_valid_column(cand, df_for_infer.columns):
                        kpi_group_by = get_valid_column(cand, df_for_infer.columns)
                        break
                if not kpi_group_by:
                    for low, real in cols_lower.items():
                        if low == suffix or low.endswith(suffix) or suffix in low:
                            kpi_group_by = real
                            break

        # Normalize signature (sheet + formula) and skip duplicates
        norm_formula = _normalize_formula(kpi_formula)
        sig = f"{str(kpi_sheet or '').strip().lower()}::{norm_formula}" if norm_formula else ""
        if sig and sig in seen_kpi_signatures:
            logger.info("Skipping duplicate KPI", label=kpi_label, sheet=kpi_sheet)
            continue
        if sig:
            seen_kpi_signatures.add(sig)

        df = _get_or_build_df(kpi_sheet)
        if df is None or not kpi_formula:
            continue

        try:
            # Feature Engineering Layer: Apply computed column if needed
            temp_col = f"__kpi_{kpi_label.replace(' ', '_').lower()}"
            df = formula_engine.apply_formula(df, kpi_formula, temp_col)

            # Performance: Cache columns
            df_cols = df.columns
            col_name = get_valid_column(temp_col if temp_col in df_cols else kpi_formula, df_cols)

            if not col_name:
                logger.warning(f"KPI '{kpi_label}' formula '{kpi_formula}' could not be evaluated - column not found")
                continue

            # Smart Aggregation Fallback
            kpi_agg = infer_agg_type(df, col_name, get_k(kpi, "aggregation"))

            # Normalize boolean-like string columns
            df = normalize_boolean_column(df, col_name)

            # Ensure numeric for sum/avg
            if kpi_agg in ["sum", "avg"]:
                if df[col_name].dtype == pl.String:
                    df = df.with_columns(pl.col(col_name).str.replace(",", ".").cast(pl.Float64, strict=False))
                else:
                    df = df.with_columns(pl.col(col_name).cast(pl.Float64, strict=False))

            df_len = len(df)
            if df_len == 0:
                continue

            # Calculate coverage
            non_null_count = df[col_name].is_not_null().sum()
            coverage = non_null_count / df_len

            val = None

            # Optional support for “per X” KPIs via group_by
            group_col = get_valid_column(kpi_group_by, df.columns) if kpi_group_by else None

            if non_null_count > 0:
                if group_col:
                    # Compute metric per entity (group_col) then average across entities,
                    # e.g. Orders per Salesperson, Orders per Customer.
                    base = df.select(
                        [
                            pl.col(group_col).alias("_group"),
                            pl.col(col_name).alias("_value"),
                        ]
                    )
                    aggr_expr = pl.col("_value")
                    agg_type = (kpi_agg or "avg").lower()
                    # Per-entity KPIs: use sum per group then mean across entities (count → sum per group)
                    if agg_type == "count":
                        agg_type = "sum"
                    if agg_type == "sum":
                        aggr_expr = aggr_expr.sum()
                    elif agg_type == "avg":
                        aggr_expr = aggr_expr.mean()
                    elif agg_type == "median":
                        aggr_expr = aggr_expr.median()
                    elif agg_type in ["stddev", "stdev"]:
                        aggr_expr = aggr_expr.std()
                    elif agg_type == "var":
                        aggr_expr = aggr_expr.var()
                    elif agg_type == "mode":
                        aggr_expr = aggr_expr.mode().first()
                    elif agg_type == "count":
                        aggr_expr = aggr_expr.count()
                    else:
                        aggr_expr = aggr_expr.mean()

                    per_entity = (
                        base.group_by("_group").agg(aggr_expr.alias("_value")).filter(pl.col("_value").is_not_null())
                    )
                    if len(per_entity) > 0:
                        val = per_entity["_value"].mean()
                else:
                    if kpi_agg == "sum":
                        val = df[col_name].sum()
                    elif kpi_agg == "avg":
                        val = df[col_name].mean()
                    elif kpi_agg == "median":
                        val = df[col_name].median()
                    elif kpi_agg in ["stddev", "stdev"]:
                        val = df[col_name].std()
                    elif kpi_agg == "var":
                        val = df[col_name].var()
                    elif kpi_agg == "mode":
                        mode_result = df[col_name].mode()
                        val = mode_result[0] if len(mode_result) > 0 else None
                    elif kpi_agg == "count":
                        val = df[col_name].count()
                    elif "percentile" in kpi_formula.lower():
                        try:
                            p_val = re.search(
                                r"PERCENTILE\s*\(\s*[\w-]+\s*,\s*([\d.]+)\s*\)", kpi_formula, re.IGNORECASE
                            ).group(1)
                            val = df[col_name].quantile(float(p_val) / 100.0)
                        except Exception:
                            val = df[col_name].median()
                    else:
                        val = df[col_name].count()

            # Comparison logic (Real growth calculation)
            growth_pct = None
            date_cols = find_date_columns(schema, kpi_sheet)

            if date_cols and val is not None:
                try:
                    date_col = date_cols[0]
                    df_dates = formula_engine.robust_date_parse(df, date_col)
                    # Get latest month and previous month
                    months = df_dates[date_col].dt.truncate("1mo").unique().sort(descending=True)
                    if len(months) >= 2:
                        latest_m, prev_m = months[0], months[1]

                        # Filter and aggregate for growth calculation
                        latest_filter = pl.col(date_col).dt.truncate("1mo") == latest_m
                        prev_filter = pl.col(date_col).dt.truncate("1mo") == prev_m

                        if kpi_agg == "avg":
                            val_latest = df_dates.filter(latest_filter).select(pl.col(col_name)).mean().item()
                            val_prev = df_dates.filter(prev_filter).select(pl.col(col_name)).mean().item()
                        else:
                            val_latest = df_dates.filter(latest_filter).select(pl.col(col_name)).sum().item()
                            val_prev = df_dates.filter(prev_filter).select(pl.col(col_name)).sum().item()

                        if val_prev and val_prev != 0:
                            growth_pct = round(((val_latest - val_prev) / abs(val_prev)) * 100, 1)
                except Exception:
                    pass

            # --- Adaptive Unit Intelligence ---
            final_unit, final_val = kpi_unit, val
            is_datediff = "datediff" in kpi_formula.lower()
            if is_datediff and final_val is not None and final_unit:
                abs_f = abs(float(final_val))
                sign = 1 if float(final_val) >= 0 else -1
                if abs_f < 0.0416:  # < 1h
                    final_val, final_unit = sign * abs_f * 1440, "min"
                elif abs_f < 0.5:  # < 12h
                    final_val, final_unit = sign * abs_f * 24, "h"
                else:
                    final_unit = "days"
            elif final_unit and final_unit.lower() in ("min", "minutes") and final_val is not None:
                abs_f = abs(float(final_val))
                sign = 1 if float(final_val) >= 0 else -1
                if abs_f >= 720:  # >= 12h
                    final_val, final_unit = sign * abs_f / 1440, "days"
                elif abs_f >= 60:  # >= 1h
                    final_val, final_unit = sign * abs_f / 60, "h"

            # --- Rate Normalization ---
            if kpi_format == "percentage" and final_val is not None:
                # If val is already in [0-1], keep it as-is.
                # If val is in (1, 100], it was expressed as a percentage —
                # convert to 0-1 fraction for consistent display.
                # Values > 100 are raw ratios (e.g. growth multiples): leave them
                # unchanged so the frontend can render them correctly rather than
                # clamping them to 1.0 and losing all meaningful information.
                try:
                    fv = float(final_val)
                    if 1.0 < fv <= 100.0:
                        final_val = fv / 100.0
                except (ValueError, TypeError):
                    pass

            # --- Smart Number Formatting ---
            final_val, final_unit = smart_format_value(final_val, final_unit, kpi_format)

            dashboard["kpis"].append(
                {
                    "label": kpi_label,
                    "value": final_val,
                    "unit": final_unit,
                    "priority": kpi_priority,
                    "format": kpi_format,
                    "change": growth_pct,
                    "coverage": round(float(coverage), 4),
                    "formula": kpi_formula,
                    "description": kpi_desc or f"Calculated using {kpi_agg.upper()} on {kpi_formula}",
                }
            )
        except Exception as e:
            logger.error("KPI calculation failed", label=kpi_label, error=str(e))
            # Still add the KPI to dashboard with null value and error description
            dashboard["kpis"].append(
                {
                    "label": kpi_label,
                    "value": None,
                    "unit": kpi_unit,
                    "priority": kpi_priority,
                    "format": kpi_format,
                    "change": None,
                    "coverage": 0.0,
                    "formula": kpi_formula,
                    "description": f"⚠️ Error calculating metric: {str(e)[:100]}",
                }
            )

    # 2. Extract data for suggested charts
    for chart in enrichment.charts:
        df = _get_or_build_df(chart.sheet)
        if df is None:
            continue

        try:
            # Helper to access attributes or dict keys safely
            def get_val(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)

            chart_agg = get_val(chart, "aggregation")
            chart_type = get_val(chart, "type", "bar")
            chart_title = get_val(chart, "title", "Untitled Chart")
            chart_x = get_val(chart, "x_axis")
            chart_y = get_val(chart, "y_axis")
            chart_split = get_val(chart, "split_by")
            chart_unit = get_val(chart, "unit")
            chart_format = get_val(chart, "format", "number")
            chart_desc = get_val(chart, "description", "")

            # --- Normalization Middleware ---
            if chart_agg and any(fn in str(chart_agg).upper() for fn in ["DATEDIFF", "RATIO", "DIFF"]):
                chart_y = chart_agg
                chart_agg = "sum"

            df_cols = df.columns

            # ── Wide-format / y_columns melt ──────────────────────────────────
            # When the LLM specifies y_columns (multi-year budget tables), melt
            # DataFrame from: (label_col, 2024, 2025 … 2074)
            # into:           (label_col, __year__, __value__)
            # so the normal chart aggregation path works without modification.
            chart_y_columns = get_val(chart, "y_columns")
            if chart_y_columns and isinstance(chart_y_columns, list):
                available_y_cols = [c for c in chart_y_columns if c in df_cols]
                if available_y_cols and chart_x and chart_x in df_cols:
                    try:
                        id_col_melt = chart_x
                        df = df.select([pl.col(id_col_melt)] + [pl.col(c) for c in available_y_cols]).melt(
                            id_vars=[id_col_melt],
                            value_vars=available_y_cols,
                            variable_name="__year__",
                            value_name="__value__",
                        )
                        # Rewrite x/y/split to work with the melted shape.
                        # For time-series, we want the Years on the X-axis.
                        chart_x = "__year__"
                        chart_split = id_col_melt  # original x (e.g. description) becomes the legend
                        chart_y = "__value__"
                        df_cols = df.columns
                        logger.info(
                            "Applied y_columns melt (Time on X-axis)",
                            sheet=get_val(chart, "sheet"),
                            x_axis=chart_x,
                            split_by=chart_split,
                        )
                    except Exception as _melt_err:
                        logger.warning(
                            "y_columns melt failed, falling back to single y_axis",
                            error=str(_melt_err),
                        )

            # Determine real column for Y to check its type
            y_col_candidate = get_valid_column(str(chart_y), df_cols)
            # Smart Aggregation Fallback
            chart_agg = infer_agg_type(df, y_col_candidate if y_col_candidate else "", chart_agg)

            if chart_agg and chart_title:
                temp_y = f"__chart_y_{str(chart_title).replace(' ', '_').lower()}"
                df = formula_engine.apply_formula(df, chart_y, temp_y)
                # Performance: get columns again after modification
                df_cols = df.columns

                x_col = get_valid_column(chart_x, df_cols)
                y_col = get_valid_column(temp_y if temp_y in df_cols else chart_y, df_cols)

                if not x_col and df_cols:
                    x_col = df_cols[0]
                if not y_col and len(df_cols) > 1:
                    y_col = df_cols[1]

                if not x_col or not y_col:
                    continue

                # Heuristic date parsing for label axis based on column name,
                # so that time-bucketing works even if the raw data is string.
                try:
                    if isinstance(x_col, str) and any(tok in x_col.lower() for tok in ["date", "time"]):
                        df = formula_engine.robust_date_parse(df, x_col)
                except Exception:
                    pass

                if chart_agg.lower() in ["sum", "avg", "max", "min"]:
                    base_df = df.with_columns(
                        [pl.col(x_col).alias("label"), pl.col(y_col).cast(pl.Float64, strict=False).alias("value")]
                    )
                else:
                    base_df = df.select([pl.col(x_col).alias("label"), pl.col(y_col).alias("value")])

                # Temporal Scaling
                if df[x_col].dtype in [pl.Date, pl.Datetime]:
                    try:
                        time_stats = df.select(
                            [pl.col(x_col).min().alias("min"), pl.col(x_col).max().alias("max")]
                        ).to_dicts()[0]
                        min_d, max_d = time_stats["min"], time_stats["max"]
                        if max_d and min_d:
                            delta_days = (max_d - min_d).days
                            trunc, fmt = (
                                ("1h", "%H:%M")
                                if delta_days <= 1
                                else (("1d", "%m-%d") if delta_days <= 31 else ("1mo", "%Y-%m"))
                            )
                            base_df = base_df.with_columns(
                                [
                                    pl.col("label")
                                    .cast(df[x_col].dtype)
                                    .dt.truncate(trunc)
                                    .dt.to_string(fmt)
                                    .alias("label")
                                ]
                            )
                    except Exception:
                        pass

                # Define aggregation
                aggr_expr = pl.col("value")
                agg_type = chart_agg.lower()
                if agg_type == "sum":
                    aggr_expr = aggr_expr.sum()
                elif agg_type == "avg":
                    aggr_expr = aggr_expr.mean()
                elif agg_type == "median":
                    aggr_expr = aggr_expr.median()
                elif agg_type in ("stddev", "stdev"):
                    aggr_expr = aggr_expr.std()
                elif agg_type == "var":
                    aggr_expr = aggr_expr.var()
                elif agg_type == "count":
                    aggr_expr = aggr_expr.count()
                elif agg_type == "max":
                    aggr_expr = aggr_expr.max()
                elif agg_type == "min":
                    aggr_expr = aggr_expr.min()
                elif agg_type == "mode":
                    # Mode: most frequent value
                    aggr_expr = aggr_expr.mode().first()
                else:
                    aggr_expr = aggr_expr.sum()

                # --- Handle Split-By (Legends) ---
                split_col = get_valid_column(chart_split, df_cols)
                series_keys: list = []
                if split_col:
                    # Multi-series data: group by [label, split_col]
                    series_df = base_df.with_columns(df[split_col].alias("series"))
                    chart_data_raw = (
                        series_df.group_by(["label", "series"])
                        .agg(aggr_expr)
                        .filter(pl.col("value").is_not_null())
                        .sort("label")
                        .to_dicts()
                    )
                    pivoted = {}
                    all_series_keys = set()
                    for row in chart_data_raw:
                        l = row["label"]
                        s = str(row["series"])
                        v = row["value"]
                        if l not in pivoted:
                            pivoted[l] = {"label": l}
                        pivoted[l][s] = v
                        all_series_keys.add(s)
                    series_keys = sorted(all_series_keys)
                    for row in pivoted.values():
                        for sk in series_keys:
                            if sk not in row:
                                row[sk] = None
                    chart_data = sorted(list(pivoted.values()), key=lambda x: str(x["label"]))[:30]
                else:
                    # Sort by value descending for rankings; by label for time-series (line/area)
                    limit = 30
                    top_n_match = re.search(r"top\s*(\d+)", chart_title, re.IGNORECASE)
                    if top_n_match:
                        limit = min(int(top_n_match.group(1)), 100)
                    grouped = base_df.group_by("label").agg(aggr_expr).filter(pl.col("value").is_not_null())
                    is_time_chart = chart_type in ["line", "area"] and any(
                        t in (chart_x or "").lower() for t in ["date", "time"]
                    )
                    if is_time_chart:
                        grouped = grouped.sort("label")
                    else:
                        grouped = grouped.sort(pl.col("value"), descending=True)
                    chart_data = grouped.head(limit).to_dicts()

                if not chart_data:
                    continue

                # Ensure numeric values for front-end: single-series uses "value", multi-series uses series keys
                for row in chart_data:
                    if series_keys:
                        for k in series_keys:
                            try:
                                v = row.get(k)
                                if v is None:
                                    row[k] = None
                                elif isinstance(v, (int, float)):
                                    row[k] = float(v)
                                else:
                                    s = str(v).strip().replace(",", "")
                                    row[k] = float(s) if s not in ("", "None", "null") else None
                            except Exception:
                                row[k] = None
                    else:
                        try:
                            v = row.get("value")
                            if v is None:
                                row["value"] = None
                            elif isinstance(v, (int, float)):
                                row["value"] = float(v)
                            else:
                                s = str(v).strip().replace(",", "")
                                row["value"] = float(s) if s not in ("", "None", "null") else None
                        except Exception:
                            row["value"] = None

                final_type = chart_type
                if final_type in ["line", "area"] and len(chart_data) < 2:
                    final_type = "bar"
                if not series_keys and final_type == "pie" and len(chart_data) > 7:
                    sorted_data = sorted(chart_data, key=lambda x: x.get("value") or 0, reverse=True)
                    top_n = sorted_data[:6]
                    other_sum = sum(x["value"] for x in sorted_data[6:] if isinstance(x.get("value"), (int, float)))
                    top_n.append({"label": "Autres", "value": other_sum})
                    chart_data = top_n
            else:
                x_col = get_valid_column(str(chart_x), df_cols) or chart_x
                y_col = get_valid_column(str(chart_y), df_cols)
                if not y_col:
                    continue
                chart_data = df.select([pl.col(x_col).alias("label"), pl.col(y_col).alias("value")]).head(50).to_dicts()
                final_type = chart_type

            coverage = (df[y_col].is_not_null().sum() / len(df)) if len(df) > 0 else 0
            if series_keys:
                nums = []
                for p in chart_data:
                    for k in series_keys:
                        v = p.get(k)
                        if isinstance(v, (int, float)):
                            nums.append(float(v))
            else:
                nums = [p["value"] for p in chart_data if isinstance(p.get("value"), (int, float))]
            ref_val = round(sum(nums) / len(nums), 2) if nums else None

            # Smart time unit conversion for charts that likely represent time durations
            final_unit = chart_unit
            final_chart_data = chart_data

            # Check if the y-axis formula or description suggests this is a time measurement
            is_time_metric = any(
                keyword in str(chart_y).lower() for keyword in ["datediff", "duration", "time", "processing", "elapsed"]
            )

            if is_time_metric and nums and not series_keys:
                # Decide base unit for the incoming numbers.  The LLM may
                # have signaled a unit itself or used DATEDIFF which returns
                # days; otherwise default to seconds as before.
                base_unit = "sec"
                if chart_unit:
                    cu = str(chart_unit).lower()
                    if cu in ("day", "days"):
                        base_unit = "days"
                    elif cu in ("h", "hour", "hours"):
                        base_unit = "h"
                    elif cu in ("min", "minute", "minutes"):
                        base_unit = "min"
                    elif cu in ("ms", "millisecond", "milliseconds"):
                        # values already in ms, treat as seconds and allow
                        # the conversion logic to scale down if needed
                        base_unit = "sec"
                if "datediff" in str(chart_y).lower():
                    # formula_engine returns days for DATEDIFF
                    base_unit = "days"

                unit_label, converted_vals = smart_convert_time_values(nums, base_unit)
                final_unit = unit_label

                # Update chart data with converted values
                final_chart_data = []
                for i, row in enumerate(chart_data):
                    new_row = row.copy()
                    if isinstance(row.get("value"), (int, float)) and i < len(converted_vals):
                        new_row["value"] = round(converted_vals[i], 2) if converted_vals[i] is not None else None
                    final_chart_data.append(new_row)

                # Update reference value with converted unit
                if ref_val is not None and nums:
                    _, converted_ref = smart_convert_time_values([ref_val], base_unit)
                    ref_val = round(converted_ref[0], 2) if converted_ref[0] is not None else None

            chart_payload = {
                "type": final_type,
                "title": chart_title,
                "description": chart_desc,
                "unit": final_unit,
                "sheet": get_val(chart, "sheet"),
                "x_axis": str(x_col),
                "y_axis": str(y_col),
                "split_by": chart_split,
                "data": final_chart_data,
                "x_key": "label",
                "y_key": "value",
                "reference": ref_val,
                "reference_label": get_val(chart, "reference_label") or "Avg",
                "coverage": round(float(coverage), 4),
                "format": chart_format,
            }
            if series_keys:
                chart_payload["series_keys"] = series_keys
            dashboard["charts"].append(chart_payload)
        except Exception as e:
            logger.error("Chart build failed", title=chart_title, error=str(e))

    # 3. Data Preview & Relationships
    for name, df in all_dfs.items():
        dashboard["data_preview"][name] = df.head(10).to_dicts()

    dashboard["relationships"] = [asdict(r) for r in schema.relationships]
    dashboard["joins"] = [j.model_dump() if hasattr(j, "model_dump") else j for j in enrichment.joins]

    # Add correlation insights (CORR function moved from KPI formulas to insights pipeline)
    try:
        correlation_insights = detect_correlation_insights(all_dfs, schema, threshold=0.7)
        if correlation_insights:
            dashboard["insights"].extend(correlation_insights)
            logger.info(f"Added {len(correlation_insights)} correlation insights")
    except Exception:
        logger.exception("Failed to generate correlation insights, continuing without them")

    return dashboard
