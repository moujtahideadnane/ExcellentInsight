from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import polars as pl

from app.pipeline.schema_detector import DetectedSchema


@dataclass
class ColumnStats:
    name: str
    type: str
    mean: Optional[float] = None
    median: Optional[float] = None
    p25: Optional[float] = None
    p75: Optional[float] = None
    std_dev: Optional[float] = None
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    null_count: int = 0
    unique_count: int = 0
    top_categories: Optional[List[Dict[str, Any]]] = None


@dataclass
class SheetStats:
    name: str
    row_count: int
    columns: List[ColumnStats]
    correlations: Optional[Dict[str, Dict[str, float]]] = None


@dataclass
class FileStats:
    sheets: List[SheetStats]

    def to_dict(self):
        return [asdict(s) for s in self.sheets]


def compute_stats(dataframes: Dict[str, pl.DataFrame], schema: DetectedSchema) -> FileStats:
    # Build O(1) lookup map for schema sheets — avoids O(n) generator scan per iteration
    schema_map: Dict[str, Any] = {s.name: s for s in schema.sheets}

    all_sheet_stats: List[SheetStats] = []

    for sheet_name, df in dataframes.items():
        # O(1) lookup instead of next(generator)
        sheet_schema = schema_map.get(sheet_name)
        if sheet_schema is None:
            continue

        col_stats_list: List[ColumnStats] = []
        # Group numeric columns for one-pass vectorization
        numeric_cols: List[str] = [
            c.name for c in sheet_schema.columns 
            if c.name in df.columns and ("Int" in c.inferred_type or "Float" in c.inferred_type)
        ]
        
        # Cache column count for length check
        df_len = len(df)
        
        # 1. Vectorized computation of all numeric aggregations concurrently
        numeric_stats_results = {}
        if numeric_cols:
            exprs = []
            for c in numeric_cols:
                exprs.extend([
                    pl.col(c).drop_nulls().mean().alias(f"{c}_mean"),
                    pl.col(c).drop_nulls().median().alias(f"{c}_median"),
                    pl.col(c).drop_nulls().quantile(0.25).alias(f"{c}_p25"),
                    pl.col(c).drop_nulls().quantile(0.75).alias(f"{c}_p75"),
                    pl.col(c).drop_nulls().std().alias(f"{c}_std_dev"),
                    pl.col(c).drop_nulls().min().alias(f"{c}_min_val"),
                    pl.col(c).drop_nulls().max().alias(f"{c}_max_val"),
                ])
            try:
                # Polars executes all these in parallel using available CPU cores
                row_result = df.select(exprs).row(0)
                keys = [e.meta.output_name() for e in exprs]
                numeric_stats_results = dict(zip(keys, row_result))
            except Exception:
                pass

        for col_schema in sheet_schema.columns:
            col_name = col_schema.name
            # Early exit if column missing from df (shouldn't happen but defensive)
            if col_name not in df.columns:
                continue

            series = df[col_name]
            dtype = col_schema.inferred_type

            c_stats = ColumnStats(
                name=col_name,
                type=dtype,
                null_count=col_schema.null_count,
                unique_count=col_schema.unique_count,
            )

            if col_name in numeric_cols:
                c_stats.mean = numeric_stats_results.get(f"{col_name}_mean")
                c_stats.median = numeric_stats_results.get(f"{col_name}_median")
                c_stats.p25 = numeric_stats_results.get(f"{col_name}_p25")
                c_stats.p75 = numeric_stats_results.get(f"{col_name}_p75")
                c_stats.std_dev = numeric_stats_results.get(f"{col_name}_std_dev")
                c_stats.min_val = numeric_stats_results.get(f"{col_name}_min_val")
                c_stats.max_val = numeric_stats_results.get(f"{col_name}_max_val")

            # Categorical stats only for low-cardinality columns
            if col_schema.unique_count < 50:
                try:
                    top = series.value_counts().sort("count", descending=True).head(10)
                    c_stats.top_categories = top.to_dicts()
                except Exception:
                    pass

            col_stats_list.append(c_stats)

        # Correlation matrix (numeric only, only when >1 numeric column)
        corrs: Optional[Dict[str, Dict[str, float]]] = None
        n_num = len(numeric_cols)
        if n_num > 1:
            try:
                corr_df = df.select(numeric_cols).corr()
                # Build dict with cached row access — avoids repeated indexing
                corrs = {
                    col: {other: corr_df.row(i)[j] for j, other in enumerate(numeric_cols)}
                    for i, col in enumerate(numeric_cols)
                }
            except Exception:
                pass

        all_sheet_stats.append(
            SheetStats(
                name=sheet_name,
                row_count=df_len,
                columns=col_stats_list,
                correlations=corrs,
            )
        )

    return FileStats(sheets=all_sheet_stats)
