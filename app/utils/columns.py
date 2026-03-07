import re
from typing import List, Optional


def get_valid_column(expression: str, available_columns: List[str]) -> Optional[str]:
    """Robustly find an existing column name within an expression string (case-insensitive)."""
    if not expression or not available_columns:
        return None

    expr_lower = expression.strip().lower()
    col_map = {c.lower(): c for c in available_columns}

    if expr_lower in col_map:
        return col_map[expr_lower]

    # Handle SQL-like COUNT patterns (COUNT(*), COUNT(1), COUNT(SheetName))
    if "count(" in expr_lower:
        match = re.search(r"count\s*\(\s*(.*?)\s*\)", expr_lower)
        if match:
            inner = match.group(1).strip().strip("'").strip('"')
            if inner in col_map:
                return col_map[inner]
        return available_columns[0]  # Just need any column to count rows

    # Try common extractions (inside parentheses)
    match = re.search(r"\((.*?)\)", expression)
    if match:
        inner = match.group(1).split(",")[0].strip().strip("'").strip('"').lower()
        if inner in col_map:
            return col_map[inner]

    # Fallback: Find any word that is a column
    # Sorted by length descending to avoid partial matches (e.g., 'ID' matching in 'OrderID')
    sorted_cols = sorted(available_columns, key=len, reverse=True)
    for col in sorted_cols:
        if col.lower() in expr_lower:
            return col

    # Last resort fallback for charts: if it's a count, just pick the first column
    if "count" in expr_lower:
        return available_columns[0]

    return None
