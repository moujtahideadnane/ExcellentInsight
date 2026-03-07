from dataclasses import asdict, dataclass
from typing import Dict, List

import polars as pl

from app.pipeline import formula_engine


@dataclass
class ColumnSchema:
    name: str
    inferred_type: str
    null_count: int
    unique_count: int
    is_primary_key: bool


@dataclass
class SheetSchema:
    name: str
    columns: List[ColumnSchema]
    row_count: int


@dataclass
class Relationship:
    from_sheet: str
    from_col: str
    to_sheet: str
    to_col: str
    type: str  # 'one_to_many' | 'one_to_one'


@dataclass
class DetectedSchema:
    sheets: List[SheetSchema]
    relationships: List[Relationship]

    def to_dict(self):
        return {"sheets": [asdict(s) for s in self.sheets], "relationships": [asdict(r) for r in self.relationships]}


def detect_schema(dataframes: Dict[str, pl.DataFrame]) -> DetectedSchema:
    sheets_schema = []

    # 1. Individual Sheet Analysis
    for name, df in dataframes.items():
        columns_schema = []
        for col in df.columns:
            series = df[col]
            dtype = str(series.dtype)
            null_count = series.null_count()
            unique_count = series.n_unique()

            # Date inference: String or numeric column with date/time in name
            inferred_type = dtype
            name_suggests_date = "date" in col.lower() or "time" in col.lower()
            if name_suggests_date:
                try:
                    sample = df.select([col]).head(200)
                    parsed = formula_engine.robust_date_parse(sample, col)
                    if parsed[col].dtype.is_temporal():
                        inferred_type = "Datetime"
                except Exception:
                    pass

            # Simple PK heuristic: unique and no nulls
            is_pk = (unique_count == len(df)) and (null_count == 0) and (len(df) > 0)

            columns_schema.append(
                ColumnSchema(
                    name=col,
                    inferred_type=inferred_type,
                    null_count=null_count,
                    unique_count=unique_count,
                    is_primary_key=is_pk,
                )
            )

        sheets_schema.append(SheetSchema(name=name, columns=columns_schema, row_count=len(df)))

    # 2. Relationship Detection (Optimized via Column Index)
    relationships = []
    # col_map: lowercase_name -> List of (sheet_name, ColumnSchema)
    col_index: dict[str, list[tuple[str, ColumnSchema]]] = {}

    for sheet in sheets_schema:
        for col in sheet.columns:
            name_lower = col.name.lower()
            if name_lower not in col_index:
                col_index[name_lower] = []

            # Check for matches with previously indexed sheets
            for other_sheet_name, other_col in col_index[name_lower]:
                # Determine relationship type
                if col.is_primary_key and not other_col.is_primary_key:
                    relationships.append(
                        Relationship(
                            from_sheet=other_sheet_name,
                            from_col=other_col.name,
                            to_sheet=sheet.name,
                            to_col=col.name,
                            type="many_to_one",
                        )
                    )
                elif not col.is_primary_key and other_col.is_primary_key:
                    relationships.append(
                        Relationship(
                            from_sheet=sheet.name,
                            from_col=col.name,
                            to_sheet=other_sheet_name,
                            to_col=other_col.name,
                            type="many_to_one",
                        )
                    )
                elif col.is_primary_key and other_col.is_primary_key:
                    relationships.append(
                        Relationship(
                            from_sheet=sheet.name,
                            from_col=col.name,
                            to_sheet=other_sheet_name,
                            to_col=other_col.name,
                            type="one_to_one",
                        )
                    )

            col_index[name_lower].append((sheet.name, col))

    return DetectedSchema(sheets=sheets_schema, relationships=relationships)
