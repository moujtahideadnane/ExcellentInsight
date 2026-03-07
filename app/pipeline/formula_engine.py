import re
from typing import Optional

import polars as pl


def robust_date_parse(df: pl.DataFrame, col: str) -> pl.DataFrame:
    """Try multiple formats to parse a column into Datetime by coalescing results."""
    if col not in df.columns:
        return df

    s = df[col]
    if s.dtype.is_temporal():
        return df

    # Handle numeric (Excel serial) dates
    if s.dtype.is_numeric():
        try:
            # Heuristic: Excel dates for 1970-2050 fall between 25000 and 55000
            # We check the mean to see if it's in this ballpark before committing to this conversion
            mean_val = s.mean()
            if mean_val and 15000 < mean_val < 70000:
                return df.with_columns(
                    (pl.datetime(1899, 12, 30) + pl.duration(days=pl.col(col).cast(pl.Int64))).alias(col)
                )
        except Exception:
            pass
        # If numeric but not looking like Excel dates, cast to string and continue with regex parsing
        s = s.cast(pl.String)
    elif s.dtype != pl.String:
        s = s.cast(pl.String)

    # List of formats to try (None = auto)
    formats = [
        None,
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%d-%b-%Y",
        "%b %d %Y",
        "%B %d %Y",
    ]

    final_parsed = None

    for fmt in formats:
        try:
            if fmt is None:
                # Automatic detection
                current = s.str.to_datetime(strict=False)
            else:
                current = s.str.to_datetime(fmt, strict=False)

            if final_parsed is None:
                final_parsed = current
            else:
                # Fill nulls in our best guess with results from this newly tried format
                final_parsed = pl.coalesce([final_parsed, current])

            # If we reached 100% coverage (excluding already invalid/empty strings), we can stop
            if final_parsed.null_count() == 0:
                break
        except Exception:
            continue

    if final_parsed is None:
        # No format worked — return df unchanged to avoid crashing the pipeline
        return df

    return df.with_columns(final_parsed.alias(col))


def apply_formula(df: pl.DataFrame, formula: str, target_col: str) -> pl.DataFrame:
    """Parses formula and applies Polars logic. Case-insensitive and underscore-insensitive."""
    formula = formula.strip()

    # Create case-insensitive and fuzzy column maps.  Strip punctuation,
    # spaces and underscores to allow matching columns like 'Delivery Date',
    # 'delivery_date' or 'DeliveryDate'.
    import re as _re

    def _normalize_name(n: str) -> str:
        return _re.sub(r"[^a-z0-9]", "", n.lower() if n else "")

    col_map = {c.lower(): c for c in df.columns}
    fuzzy_map = {_normalize_name(c): c for c in df.columns}

    def get_real_col(name: str) -> Optional[str]:
        if not name:
            return None

        # Direct exact match first (handles pure-numeric column names like "2024",
        # which survive lowercasing unchanged but may not appear in a fuzzy map).
        if name in df.columns:
            return name

        # Support sheet-qualified references like "Orders.orderdate"
        # by trying both the full token and the last segment.
        candidates = [name]
        if "." in name:
            tail = name.split(".")[-1]
            if tail and tail != name:
                candidates.append(tail)

        for cand in candidates:
            low = cand.lower()
            if low in col_map:
                return col_map[low]
            # Try fuzzy normalization (remove spaces, underscores, punctuation)
            key = _normalize_name(cand)
            real = fuzzy_map.get(key)
            if real:
                return real
        return None

    # 1. DATEDIFF(col1, col2) -> Result in Days (Float)
    datediff_match = re.search(r"DATEDIFF\s*\(\s*([\w\.-]+)\s*,\s*([\w\.-]+)\s*\)", formula, re.IGNORECASE)
    if datediff_match:
        c1_raw, c2_raw = datediff_match.groups()
        start_col = get_real_col(c1_raw)
        end_col = get_real_col(c2_raw)
        if start_col and end_col:
            df = robust_date_parse(df, start_col)
            df = robust_date_parse(df, end_col)
            # Ensure both are temporal after parsing
            if df[start_col].dtype.is_temporal() and df[end_col].dtype.is_temporal():
                return df.with_columns(
                    [((pl.col(end_col) - pl.col(start_col)).dt.total_seconds() / (3600 * 24)).alias(target_col)]
                )

    # 2. IS_BEFORE(A, B) or LT(A, B) or GT(A, B) -> Binary 0/1 (Float for averaging)
    comp_match = re.search(r"(IS_BEFORE|LT|GT)\s*\(\s*([\w\.-]+)\s*,\s*([\w\.-]+)\s*\)", formula, re.IGNORECASE)
    if comp_match:
        op, c1_raw, c2_raw = comp_match.groups()
        col_a = get_real_col(c1_raw)
        col_b = get_real_col(c2_raw)
        if col_a and col_b:
            # If names suggest dates or they are already dates, parse them
            if any(k in n.lower() for k in ["date", "time", "at"] for n in [col_a, col_b, c1_raw, c2_raw]):
                df = robust_date_parse(df, col_a)
                df = robust_date_parse(df, col_b)

            expr = pl.col(col_a) < pl.col(col_b) if op.upper() in ["IS_BEFORE", "LT"] else pl.col(col_a) > pl.col(col_b)
            return df.with_columns([pl.when(expr).then(1.0).otherwise(0.0).alias(target_col)])

    # 3. Arithmetic RATIO(col1, col2)
    ratio_match = re.search(r"RATIO\s*\(\s*([\w\.-]+)\s*,\s*([\w\.-]+)\s*\)", formula, re.IGNORECASE)
    if ratio_match:
        c1_raw, c2_raw = ratio_match.groups()
        nominator = get_real_col(c1_raw)
        denominator = get_real_col(c2_raw)
        if nominator and denominator:
            return df.with_columns(
                [(pl.col(nominator).cast(pl.Float64) / pl.col(denominator).cast(pl.Float64)).alias(target_col)]
            )

    # 4. Simple DIFF(col1, col2)
    diff_match = re.search(r"DIFF\s*\(\s*([\w\.-]+)\s*,\s*([\w\.-]+)\s*\)", formula, re.IGNORECASE)
    if diff_match:
        c1_raw, c2_raw = diff_match.groups()
        col1 = get_real_col(c1_raw)
        col2 = get_real_col(c2_raw)
        if col1 and col2:
            return df.with_columns([(pl.col(col1).cast(pl.Float64) - pl.col(col2).cast(pl.Float64)).alias(target_col)])

    # 5. Plain aggregation wrappers
    agg_match = re.search(
        r"^(SUM|AVG|COUNT|MIN|MAX|MEDIAN|STDEV|VAR)\s*\(\s*([\w\s\*\d\.-]+?)\s*\)$", formula.strip(), re.IGNORECASE
    )
    if agg_match:
        agg_fn = agg_match.group(1).upper()
        raw_col = agg_match.group(2).strip()
        real_col = get_real_col(raw_col)

        if real_col:
            return df.with_columns(pl.col(real_col).alias(target_col))
        elif agg_fn == "COUNT":
            # If counting and column not found (e.g. COUNT(*) or COUNT(SheetName)),
            # use a dummy column of 1s to count rows.
            return df.with_columns(pl.lit(1.0).alias(target_col))

    # 6. PERCENTILE(col, p)
    pct_match = re.search(r"PERCENTILE\s*\(\s*([\w\.-]+)\s*,\s*([\d.]+)\s*\)", formula, re.IGNORECASE)
    if pct_match:
        c_raw, p_val = pct_match.groups()
        col = get_real_col(c_raw)
        if col:
            return df.with_columns(pl.col(col).alias(target_col))

    # 7. COUNTIF(col, value) -> 0/1
    countif_match = re.search(r'COUNTIF\s*\(\s*([\w\.-]+)\s*,\s*[\'"]?(.+?)[\'"]?\s*\)', formula, re.IGNORECASE)
    if countif_match:
        c_raw, val = countif_match.groups()
        col = get_real_col(c_raw)
        if col:
            try:
                numeric_val = float(val)
                expr = pl.col(col).cast(pl.Float64) == numeric_val
            except ValueError:
                expr = pl.col(col).cast(pl.String).str.to_lowercase() == val.lower()

            return df.with_columns([pl.when(expr).then(1.0).otherwise(0.0).alias(target_col)])

    return df
