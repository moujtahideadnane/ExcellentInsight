import json
import re
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

from app.llm.openrouter_client import OpenRouterClient
from app.pipeline.schema_detector import DetectedSchema
from app.pipeline.stats_engine import FileStats
from app.utils.columns import get_valid_column
from app.utils.llm_validation import validate_llm_output
from app.utils.sanitization import (
    sanitize_for_llm,
    sanitize_sheet_name,
)

logger = structlog.get_logger()


class LLMCache:
    """Simple pluggable cache interface used by `enrich_data`.

    Production implementations can back this with Redis or similar. Tests
    patch this class to control cache behaviour.
    """

    def __init__(self):
        self._store = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value):
        self._store[key] = value

    async def close(self):
        return None


class KPISuggestion(BaseModel):
    label: str
    formula: str
    sheet: str
    aggregation: str
    format: str
    description: Optional[str] = Field(
        default=None, description="A concise, non-technical business description of what this metric represents."
    )
    unit: Optional[str] = None
    priority: Optional[str] = "medium"
    # Optional dimension used for “per X” style metrics,
    # e.g. Orders per Salesperson, Orders per Customer.
    group_by: Optional[str] = Field(
        default=None,
        description="Optional dimension column for per-entity KPIs (e.g. SalespersonId, CustomerId).",
    )


class ChartRecommendation(BaseModel):
    type: str  # Must be one of: 'bar', 'line', 'area', 'pie'
    title: str
    description: str
    sheet: str
    x_axis: str
    y_axis: str
    # For wide-format (budget/projection) tables: multiple year columns to melt
    y_columns: Optional[List[str]] = Field(
        default=None,
        description="For wide-format tables only: list of numeric columns to melt into a single value series (e.g. year columns 2024..2074).",
    )
    unit: Optional[str] = None
    aggregation: str = Field(default="sum")
    format: str = Field(default="number")
    split_by: Optional[str] = Field(default=None)


class JoinRecommendation(BaseModel):
    """One join: left_sheet + right_sheet. Use either 'on' (same column name) or left_on+right_on (different names)."""

    left_sheet: str
    right_sheet: str
    on: Optional[str] = None
    left_on: Optional[str] = None
    right_on: Optional[str] = None
    how: str = "inner"


class DatasetProfile(BaseModel):
    """Lightweight profile of the uploaded dataset used to guide LLM and sub-pipelines.

    This is intentionally generic so that specialised domain adapters can
    extend it via additional sections without breaking the core contract.
    """

    total_rows: Optional[int] = Field(
        default=None,
        description="Approximate total number of rows across all sheets.",
    )
    total_columns: Optional[int] = Field(
        default=None,
        description="Approximate total number of columns across all sheets.",
    )
    has_dates: bool = Field(
        default=False,
        description="True if at least one column looks like a date/time.",
    )
    has_amounts: bool = Field(
        default=False,
        description="True if at least one column looks like a monetary or numeric amount.",
    )
    candidate_table_types: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Optional scored guesses of table types, e.g. financial_transactions, sales_pipeline.",
    )

    # compatibility helper for callers that expect a ``dict``
    # method (the orchestrator used this prior to refactoring
    # json_ready).  Keeping it here means third-party extensions can
    # safely call ``to_dict()`` without worrying about the concrete
    # type of the profile object.
    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Robustly get a value from an object (attr) or dict (key)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _has_year_columns(sheet_columns) -> bool:
    """Return True when a significant portion of column names are 4-digit years (e.g. 2024..2074)."""
    import re as _re

    year_pattern = _re.compile(r"^\d{4}$")
    col_list = sheet_columns if isinstance(sheet_columns, list) else []
    year_count = sum(1 for c in col_list if year_pattern.match(str(_get_val(c, "name") or "")))
    return year_count >= 3


def _dataset_profile_from_schema(schema: DetectedSchema) -> DatasetProfile:
    """Build DatasetProfile from schema only (for cache hit and orchestrator)."""
    total_rows = 0
    total_columns = 0
    has_dates = False
    has_amounts = False
    for s in schema.sheets:
        total_rows += getattr(s, "row_count", 0) or 0
        total_columns += len(s.columns)
        for c in s.columns:
            it = (c.inferred_type or "").lower()
            name_lower = (c.name or "").lower()
            if "date" in it or "time" in it or "date" in name_lower or "time" in name_lower:
                has_dates = True
            if any(tok in it for tok in ("float", "decimal", "double", "amount", "money", "currency")):
                has_amounts = True
        # Year-named columns (2024, 2025, …) count as a temporal dimension
        if not has_dates and _has_year_columns(s.columns):
            has_dates = True
    return DatasetProfile(
        total_rows=total_rows or None,
        total_columns=total_columns or None,
        has_dates=has_dates,
        has_amounts=has_amounts,
        candidate_table_types=classify_table_types(schema),
    )


def classify_table_types(schema: DetectedSchema) -> List[Dict[str, Any]]:
    """Heuristic classifier that guesses table types (financial, sales, etc.) from schema.

    This is intentionally conservative: it surfaces *candidates* with scores
    rather than making hard decisions. Sub-pipelines can then decide whether
    to activate based on these scores.
    """
    import re as _re

    _year_pat = _re.compile(r"^\d{4}$")
    candidates: Dict[str, float] = {}

    for sheet in getattr(schema, "sheets", []):
        col_names = [c.name.lower() for c in sheet.columns]
        raw_col_names = [c.name or "" for c in sheet.columns]
        inferred_types = [str(c.inferred_type or "").lower() for c in sheet.columns]

        has_date = any("date" in it or "time" in it for it in inferred_types)
        has_amount = any(
            any(tok in it for tok in ("amount", "price", "revenue", "cost", "float", "decimal"))
            for it in inferred_types
        )
        has_id = any("id" in name for name in col_names)

        # Detect year-column pattern (columns named 2024, 2025 … = budget projection style)
        year_col_count = sum(1 for n in raw_col_names if _year_pat.match(n))
        has_year_columns = year_col_count >= 3

        # Treat year columns as valid time dimensions for all subsequent classifiers
        if has_year_columns:
            has_date = True

        # Budget / government finance projection tables (wide-format with year columns)
        score_budget = 0.0
        if has_year_columns:
            score_budget += 0.7  # High baseline for wide-format
        if has_amount or any(
            tok in " ".join(col_names)
            for tok in (
                "budget",
                "depense",
                "recette",
                "financement",
                "pib",
                "gdp",
                "projetions",
                "projection",
                "prevision",
                "montant",
                "variable",
            )
        ):
            score_budget += 0.2
        if any(
            tok in " ".join(col_names)
            for tok in ("gouvernement", "government", "public", "etat", "ministere", "ministry")
        ):
            score_budget += 0.1
        if score_budget > 0:
            candidates["budget_projection"] = max(candidates.get("budget_projection", 0.0), score_budget)

        # Financial-like tables: transaction logs with dates + numeric amounts
        score_financial = 0.0
        # Expanded keywords to be more specific to transactions vs general finance
        fin_keywords = (
            "invoice",
            "transaction",
            "payment",
            "expense",
            "salary",
            "payroll",
            "receipt",
            "account",
            "virement",
            "achat",
            "vente",
            "billing",
        )
        has_fin_keywords = any(tok in " ".join(col_names) for tok in fin_keywords)

        # Temporal headers: columns actually NAMED "Date", "Year", "Month", etc.
        has_explicit_time_header = any(tok in " ".join(col_names) for tok in ("date", "jour", "trimestre", "quarter"))
        # We exclude "year" from the high-score trigger if it looks like a budget projection table
        if not has_year_columns:
            has_explicit_time_header = (
                has_explicit_time_header or "year" in " ".join(col_names) or "annee" in " ".join(col_names)
            )

        if has_date and has_amount:
            if has_fin_keywords:
                score_financial += 0.8  # High confidence: keywords, amounts, and dates
            elif has_explicit_time_header:
                score_financial += 0.3  # Low confidence: explicit "Date" header but no transaction keywords
            else:
                score_financial += 0.1  # Very low confidence: just numbers and some inferred date

        # Final safety: if it looks like a budget projection (wide format), suppress financial_transactions score
        if has_year_columns:
            score_financial = min(score_financial, 0.2)

        if score_financial > 0:
            candidates["financial_transactions"] = max(candidates.get("financial_transactions", 0.0), score_financial)

        # Sales pipeline-like tables
        score_sales = 0.0
        if any(tok in " ".join(col_names) for tok in ("stage", "pipeline", "opportunity", "deal", "lead")):
            score_sales += 0.6
        if has_amount and has_date:
            score_sales += 0.2
        if any(tok in " ".join(col_names) for tok in ("status", "probability", "forecast")):
            score_sales += 0.2
        if score_sales > 0:
            candidates["sales_pipeline"] = max(candidates.get("sales_pipeline", 0.0), score_sales)

        # SaaS usage / events-like tables
        score_saas = 0.0
        if any(tok in " ".join(col_names) for tok in ("event", "usage", "session", "pageview", "login")):
            score_saas += 0.6
        if has_date and has_id:
            score_saas += 0.2
        if score_saas > 0:
            candidates["saas_usage"] = max(candidates.get("saas_usage", 0.0), score_saas)

        # Sales / orders / distribution-like tables
        sheet_name_lower = sheet.name.lower() if getattr(sheet, "name", None) else ""
        all_names = " ".join(col_names) + " " + sheet_name_lower
        score_sales_orders = 0.0
        if any(tok in all_names for tok in ("order", "salesperson", "sales", "customer", "delivery", "return", "team")):
            score_sales_orders += 0.6
        if has_id and (has_date or any(tok in all_names for tok in ("date", "delivery"))):
            score_sales_orders += 0.3
        if any(tok in all_names for tok in ("city", "region", "channel")):
            score_sales_orders += 0.2
        if score_sales_orders > 0:
            candidates["sales_distribution"] = max(candidates.get("sales_distribution", 0.0), score_sales_orders)

    # Normalise scores to [0, 1] and convert to sorted list
    out: List[Dict[str, Any]] = []
    for name, score in candidates.items():
        norm = min(max(score, 0.0), 1.0)
        out.append({"type": name, "score": round(norm, 2)})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


class LLMEnrichment(BaseModel):
    # Schema / contract metadata
    schema_version: str = Field(
        default="1.0",
        description="Version of the enrichment contract used to interpret this payload.",
    )
    dataset_profile: Optional[DatasetProfile] = Field(
        default=None,
        description="High-level profile of the dataset used to steer LLM prompts and sub-pipelines.",
    )

    # Core enrichment content
    domain: str
    summary: str
    kpis: List[KPISuggestion] = Field(default_factory=list)
    insights: List[Dict[str, Any]] = Field(default_factory=list)
    charts: List[ChartRecommendation] = Field(default_factory=list)
    joins: List[JoinRecommendation] = Field(default_factory=list)
    usage: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self):
        return self.model_dump()


def auto_inject_joins(enrichment: LLMEnrichment, schema: DetectedSchema) -> LLMEnrichment:
    """Ensure any referenced joined sheet names like 'A+B' have corresponding join recommendations.

    - Looks for KPIs and Charts that reference joined sheet names (containing '+').
    - If a required join is missing, attempts to infer the join 'on' column from detected relationships
      or from common column names between sheets.
    - Appends a JoinRecommendation when a plausible on-column is found.
    """
    if not enrichment or not schema:
        return enrichment

    existing = {f"{j.left_sheet}+{j.right_sheet}" for j in enrichment.joins}
    sheet_map = {s.name: s for s in schema.sheets}
    rels = schema.relationships or []

    # Collect referenced joined sheet names from KPIs and charts
    referenced = set()
    for k in enrichment.kpis:
        s = getattr(k, "sheet", None) if hasattr(k, "sheet") else (k.get("sheet") if isinstance(k, dict) else None)
        if s and "+" in s:
            referenced.add(s)
    for c in enrichment.charts:
        s = getattr(c, "sheet", None) if hasattr(c, "sheet") else (c.get("sheet") if isinstance(c, dict) else None)
        if s and "+" in s:
            referenced.add(s)

    for joined_name in referenced:
        if joined_name in existing:
            continue
        parts = [p.strip() for p in joined_name.split("+")]
        if len(parts) != 2:
            continue
        left, right = parts
        if left not in sheet_map or right not in sheet_map:
            continue

        left_cols = {c.name for c in sheet_map[left].columns}
        right_cols = {c.name for c in sheet_map[right].columns}
        on_col = None
        left_on_col = None
        right_on_col = None

        for r in rels:
            if {r.from_sheet, r.to_sheet} != {left, right}:
                continue
            if r.from_sheet == left and r.to_sheet == right:
                lcol, rcol = r.from_col, r.to_col
            else:
                lcol, rcol = r.to_col, r.from_col
            if lcol in left_cols and rcol in right_cols:
                if lcol == rcol:
                    on_col = lcol
                else:
                    left_on_col, right_on_col = lcol, rcol
                break

        if on_col is None and left_on_col is None:
            common = left_cols.intersection(right_cols)
            if common:
                on_col = sorted(common)[0]

        if on_col or (left_on_col and right_on_col):
            enrichment.joins.append(
                JoinRecommendation(
                    left_sheet=left,
                    right_sheet=right,
                    on=on_col,
                    left_on=left_on_col or None,
                    right_on=right_on_col or None,
                    how="inner",
                )
            )
            existing.add(joined_name)
            logger.info("Auto-injected join", joined=joined_name, on=on_col or f"{left_on_col}+{right_on_col}")

    return enrichment


def _resolve_sheet_columns(sheet: str, all_sheets: set, sheet_columns: Dict[str, set]) -> set:
    """Return the available columns for a sheet name, including virtual joined sheets (A+B+C)."""
    if not sheet:
        return set()
    if sheet in sheet_columns:
        return sheet_columns[sheet]
    # Handle LLM-suggested joined sheet names like "Orders+Salesperson"
    parts = [p.strip() for p in sheet.split("+")]
    if len(parts) > 1 and all(p in all_sheets for p in parts):
        # Return union of all constituent sheets' columns
        union_cols: set = set()
        for p in parts:
            union_cols |= sheet_columns.get(p, set())
        return union_cols
    return set()


def _normalize_joined_sheet_name(sheet: str, all_sheets: set) -> Optional[str]:
    """If sheet looks like a joined name (A+B) but with wrong spelling (e.g. plural), return corrected name using actual sheet names, or None."""
    if not sheet or "+" not in sheet:
        return None
    parts = [p.strip() for p in sheet.split("+")]
    if len(parts) < 2:
        return None
    corrected = []
    for p in parts:
        if p in all_sheets:
            corrected.append(p)
            continue
        low = p.lower()
        found = None
        for s in all_sheets:
            if s.lower() == low:
                found = s
                break
            if low.endswith("s") and len(low) > 1 and s.lower() == low[:-1]:
                found = s
                break
        if found is not None:
            corrected.append(found)
        else:
            return None
    return "+".join(corrected)


def _is_valid_sheet(sheet: str, all_sheets: set) -> bool:
    """Return True if sheet is real OR a valid A+B+C joined-sheet pattern."""
    if not sheet:
        return False
    if sheet in all_sheets:
        return True
    parts = [p.strip() for p in sheet.split("+")]
    return len(parts) > 1 and all(p in all_sheets for p in parts)


def validate_kpi(kpi: Dict[str, Any], all_sheets: set, sheet_columns: Dict[str, set]) -> bool:
    """Validate a KPI suggestion against the schema."""
    sheet = kpi.get("sheet")
    if not _is_valid_sheet(sheet, all_sheets):
        corrected = _normalize_joined_sheet_name(sheet, all_sheets)
        if corrected:
            kpi["sheet"] = corrected
            sheet = corrected
        else:
            logger.warning(f"KPI references unknown sheet: {sheet}")
            return False

    # Extract words from formula that look like columns.
    formula = str(kpi.get("formula", ""))
    if not formula:
        return False

    cols_in_formula = re.findall(r"\w+", formula, flags=re.UNICODE)

    # Use robust matching from columns utility

    # Special functions that aren't columns
    excluded = {
        "SUM",
        "AVG",
        "COUNT",
        "COUNTIF",
        "MIN",
        "MAX",
        "MEDIAN",
        "STDEV",
        "VAR",
        "PERCENTILE",
        "DATEDIFF",
        "IS_BEFORE",
        "RATIO",
        "DIFF",
        "LT",
        "GT",
    }

    available_cols = list(_resolve_sheet_columns(sheet, all_sheets, sheet_columns))
    sheet_parts = {p.strip().lower() for p in sheet.split("+")}

    # Validate group_by when present
    group_by = kpi.get("group_by")
    if group_by:
        resolved = get_valid_column(group_by, available_cols)
        if resolved:
            kpi["group_by"] = resolved
        else:
            logger.warning(f"KPI '{kpi.get('label')}' group_by '{group_by}' not found in sheet '{sheet}'")
            return False

    for col in cols_in_formula:
        if col.upper() in excluded or not col:
            continue
        col_norm = col.lower()
        if not get_valid_column(col, available_cols) and col_norm not in sheet_parts:
            logger.warning(f"KPI '{kpi.get('label')}' references unknown column '{col}' in sheet '{sheet}'")
            return False

    return True


def validate_chart(chart: Dict[str, Any], all_sheets: set, sheet_columns: Dict[str, set]) -> bool:
    """Validate a chart recommendation against the schema."""
    sheet = chart.get("sheet")
    if not _is_valid_sheet(sheet, all_sheets):
        corrected = _normalize_joined_sheet_name(sheet, all_sheets)
        if corrected:
            chart["sheet"] = corrected
            sheet = corrected
        else:
            logger.warning(f"Chart references unknown sheet: {sheet}")
            return False

    x_axis = chart.get("x_axis")
    y_axis = chart.get("y_axis")
    split_by = chart.get("split_by")
    if isinstance(split_by, str) and split_by.strip().lower() in {"none", "null", "nil", "n/a", "na", ""}:
        split_by = None

    available_cols = list(_resolve_sheet_columns(sheet, all_sheets, sheet_columns))
    sheet_parts = {p.strip().lower() for p in sheet.split("+")}

    def _resolve_col(ref: str) -> Optional[str]:
        if not ref:
            return None
        return get_valid_column(ref, available_cols)

    if not x_axis:
        logger.warning(f"Chart '{chart.get('title')}' missing x_axis")
        return False

    x_resolved = _resolve_col(x_axis)
    if not x_resolved and x_axis.lower() not in sheet_parts:
        logger.warning(f"Chart '{chart.get('title')}' invalid x_axis: {x_axis}")
        return False
    if x_resolved and x_resolved != x_axis:
        chart["x_axis"] = x_resolved

    if not y_axis:
        return False

    # y_axis can be a formula expression — only reject if it looks like a bare column that doesn't exist
    import re as _re

    y_axis_clean = str(y_axis).strip()
    bare_col = _re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_ ]*", y_axis_clean)
    if bare_col:
        y_resolved = get_valid_column(y_axis_clean, available_cols)
        if not y_resolved and y_axis_clean.lower() not in sheet_parts:
            logger.warning(f"Chart '{chart.get('title')}' y_axis '{y_axis}' not found as column or sheet")
            return False

    # Validate split_by column when present
    if split_by:
        split_resolved = _resolve_col(split_by)
        if split_resolved:
            if split_resolved != split_by:
                chart["split_by"] = split_resolved
        elif split_by.lower() not in sheet_parts:
            logger.warning(f"Chart '{chart.get('title')}' invalid split_by: {split_by}")
            return False

        # Cardinality guard: drop split_by when too many distinct values
        # (avoids 100+ item legends that are unusable in the UI)
        if isinstance(sheet_columns, dict):
            # sheet_columns is passed in from the outer scope; look up stats via a
            # fallback heuristic: column appears in schema but can't be capped here.
            # The actual cardinality check happens in enrich_data via stats_lines.
            pass  # handled via stats_by_sheet below

    return True


def _normalize_kpi_formula(formula: str) -> str:
    """Normalize formula for deduplication: lowercase, collapse whitespace, strip outer parens."""
    if not formula or not isinstance(formula, str):
        return ""
    s = formula.strip().lower()
    import re

    s = re.sub(r"\s+", " ", s)
    while s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    return s


def _deduplicate_kpis_by_formula(kpis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep one KPI per normalized formula; prefer higher priority if present."""
    seen: Dict[str, Dict[str, Any]] = {}
    priority_order = {"high": 3, "medium": 2, "low": 1}
    for kpi in kpis:
        formula = kpi.get("formula") or ""
        norm = _normalize_kpi_formula(formula)
        if not norm:
            continue
        if norm not in seen:
            seen[norm] = kpi
            continue
        existing = seen[norm]
        existing_pri = priority_order.get((existing.get("priority") or "medium"), 2)
        new_pri = priority_order.get((kpi.get("priority") or "medium"), 2)
        if new_pri > existing_pri:
            logger.info(
                "Deduplicating KPI by formula", kept=kpi.get("label"), dropped=existing.get("label"), formula_norm=norm
            )
            seen[norm] = kpi
        else:
            logger.info(
                "Deduplicating KPI by formula", kept=existing.get("label"), dropped=kpi.get("label"), formula_norm=norm
            )
    return list(seen.values())


def _infer_join_keys(join: Dict[str, Any], schema: DetectedSchema) -> None:
    """Infer and set join keys (on or left_on+right_on) from schema relationships or common columns. Mutates join."""
    left = join.get("left_sheet") or ""
    right = join.get("right_sheet") or ""
    if not left or not right:
        return
    if join.get("on") or (join.get("left_on") and join.get("right_on")):
        return
    sheet_map = {s.name: s for s in schema.sheets}
    if left not in sheet_map or right not in sheet_map:
        return
    left_cols = {c.name for c in sheet_map[left].columns}
    right_cols = {c.name for c in sheet_map[right].columns}
    rels = getattr(schema, "relationships", []) or []
    for r in rels:
        if {r.from_sheet, r.to_sheet} != {left, right}:
            continue
        if r.from_sheet == left and r.to_sheet == right:
            lcol, rcol = r.from_col, r.to_col
        else:
            lcol, rcol = r.to_col, r.from_col
        if lcol in left_cols and rcol in right_cols:
            if lcol == rcol:
                join["on"] = lcol
            else:
                join["left_on"] = lcol
                join["right_on"] = rcol
            return
    common = left_cols.intersection(right_cols)
    if common:
        join["on"] = sorted(common)[0]
        return
    common_lower = set(c.lower() for c in left_cols).intersection(c.lower() for c in right_cols)
    if common_lower:
        cl = {c.lower(): c for c in left_cols}
        cr = {c.lower(): c for c in right_cols}
        k = sorted(common_lower)[0]
        join["on"] = cl[k]


def _build_budget_prompt_addendum(schema: "DetectedSchema", stats_by_sheet: Dict[str, Dict[str, Any]]) -> str:
    """
    Build a domain-specific LLM prompt addendum for wide-format budget/projection tables.

    This addendum is injected when the dataset is classified as `budget_projection`
    (score >= 0.72). It corrects several systematic LLM failure modes on this table shape:
      - LLM picks `nom_de_la_variable` (internal code) instead of `description` as x_axis
      - LLM assigns only `y_axis: "2024"` instead of spanning all years
      - LLM uses high-cardinality `description` as split_by (335-item legends)
    """
    import re as _re

    _year_pat = _re.compile(r"^\d{4}$")

    # Identify the first sheet with year columns (the main data sheet)
    main_sheet = None
    year_cols: List[str] = []
    label_col: Optional[str] = None  # human-readable name (e.g. "description")
    id_col: Optional[str] = None  # internal code (e.g. "nom_de_la_variable")

    for sheet in schema.sheets:
        raw_names = [c.name or "" for c in sheet.columns]
        yr = sorted([n for n in raw_names if _year_pat.match(n)])
        if len(yr) >= 3:
            main_sheet = sheet.name
            year_cols = yr
            # Find label (description-like) and id (variable-like) columns
            for c in sheet.columns:
                n = (c.name or "").lower()
                if any(tok in n for tok in ("description", "libelle", "label", "nom_complet", "intitule")):
                    label_col = c.name
                if any(tok in n for tok in ("variable", "code", "identifiant", "id", "nom_de")):
                    id_col = c.name
            break

    if not main_sheet or not year_cols:
        return ""  # not a wide-format table, no addendum needed

    # Pick a reasonable subset of years for examples/chart hints
    sampled_years = year_cols[:: max(1, len(year_cols) // 10)][:10]  # ~10 evenly spaced years
    years_json = json.dumps(sampled_years)

    # Pick a few representative variables from stats to show the LLM what real data looks like
    col_stats = stats_by_sheet.get(main_sheet, {})
    sample_triples: List[str] = []
    if label_col and label_col in col_stats:
        cat_stat = col_stats[label_col]
        top_cats = getattr(cat_stat, "top_categories", []) or []
        for cat in top_cats[:3]:
            var_name = cat.get(label_col) or cat.get("label") or ""
            if var_name and year_cols:
                first_yr = year_cols[0]
                yr_stat = col_stats.get(first_yr)
                if yr_stat and getattr(yr_stat, "mean", None) is not None:
                    sample_triples.append(f"  {label_col}='{var_name}', year={first_yr}, value≈{yr_stat.mean:.2g}")

    sample_block = "\n".join(sample_triples) if sample_triples else ""
    label_display = label_col if label_col else "description"
    id_display = id_col if id_col else "nom_de_la_variable"
    avoid_cols = ", ".join(filter(None, [id_col, label_col]))  # high-cardinality; never use as split_by

    addendum = f"""

=== WIDE-FORMAT BUDGET/PROJECTION TABLE — SPECIAL RULES ===

This sheet ('{main_sheet}') is a **wide-format projection table**:
  - Each ROW is one financial/demographic variable.
  - Columns {years_json!r} ... are NUMERIC values for each year.
  - Column '{label_display}' holds the human-readable label for each variable (use as x_axis or filter).
  - Column '{id_display}' holds internal codes (e.g. 'Pop_AS') — NEVER use as x_axis or split_by.

DATA SHAPE (melted preview):
{sample_block if sample_block else "  (see COLUMN STATISTICS above)"}

CHART RULES FOR THIS TABLE:
1. TIME-TREND CHARTS (line/area): Use x_axis='{label_display}' and set y_columns={years_json}.
   The engine will automatically pivot these year columns into a time series.
   Example:
   {{"type": "line", "title": "Projection trends 2024-{year_cols[-1]}",
     "sheet": "{main_sheet}", "x_axis": "{label_display}",
     "y_axis": "{year_cols[0]}", "y_columns": {years_json},
     "aggregation": "sum", "format": "number"}}

2. COMPARISON CHARTS (bar): Use x_axis='{label_display}', y_axis='<one specific year>'.
   This shows a ranking of variables at a single point in time.
   Example:
   {{"type": "bar", "title": "Top variables in {year_cols[0]}",
     "sheet": "{main_sheet}", "x_axis": "{label_display}",
     "y_axis": "{year_cols[0]}", "aggregation": "sum", "format": "number"}}

3. SPLIT_BY RULES: The columns '{avoid_cols}' have hundreds of distinct values.
   NEVER use them as split_by. Only use split_by if you have a column with ≤ 15 distinct values.
   If no such column exists, OMIT split_by entirely.

4. PIE CHARTS: Only use pie if you can group data into ≤ 6 meaningful categories.
   Do NOT use pie for time-series or for all 300+ variables.

5. FORBIDDEN x_axis values: '{id_display}', numeric IDs, codes like 'Pop_AS'.
   ALWAYS use '{label_display}' (the human-readable label column) as x_axis.
=== END WIDE-FORMAT RULES ===
"""
    return addendum


def validate_and_filter_llm_response(
    data: Dict[str, Any], schema: "DetectedSchema", stats_by_sheet: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Validate LLM response and filter out invalid references."""
    # Collect all valid sheets and columns from schema
    all_sheets = {sheet.name for sheet in schema.sheets}
    sheet_columns = {sheet.name: {col.name for col in sheet.columns} for sheet in schema.sheets}

    # Normalize joins: join_type -> how, infer on / left_on+right_on from schema; drop joins we can't resolve
    valid_joins = []
    for join in data.get("joins", []) or []:
        if not isinstance(join, dict):
            continue
        if join.get("how") is None and join.get("join_type") is not None:
            join["how"] = join["join_type"]
        if not join.get("on") and not (join.get("left_on") and join.get("right_on")):
            _infer_join_keys(join, schema)
        if join.get("on") or (join.get("left_on") and join.get("right_on")):
            valid_joins.append(join)
        else:
            logger.warning(
                "Dropping join with unresolved keys", left=join.get("left_sheet"), right=join.get("right_sheet")
            )
    data["joins"] = valid_joins

    def _coerce_none_sentinel(v: Any) -> Any:
        """Treat common LLM sentinel strings as None (e.g. 'none', 'null', '')."""
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip().lower()
            if s in {"none", "null", "nil", "n/a", "na", ""}:
                return None
        return v

    # Sanitize known sentinel values before validation (e.g. split_by: "none").
    # Also drop high-cardinality split_by columns (> 15 distinct values = unusable legend)
    for chart in data.get("charts", []) or []:
        if not isinstance(chart, dict):
            continue
        chart["split_by"] = _coerce_none_sentinel(chart.get("split_by"))
        # Cardinality guard: drop split_by when column has too many distinct values
        if chart.get("split_by") and stats_by_sheet:
            sheet = chart.get("sheet", "")
            split_col = chart["split_by"]
            col_stat = (stats_by_sheet.get(sheet) or {}).get(split_col)
            if col_stat is not None:
                unique_count = getattr(col_stat, "unique_count", None)
                if unique_count is not None and unique_count > 15:
                    logger.warning(
                        "Dropping high-cardinality split_by",
                        chart=chart.get("title"),
                        column=split_col,
                        unique_count=unique_count,
                    )
                    chart["split_by"] = None

    # Validate KPIs
    valid_kpis = []
    for kpi in data.get("kpis", []):
        if validate_kpi(kpi, all_sheets, sheet_columns):
            valid_kpis.append(kpi)
        else:
            logger.warning(f"Removing invalid KPI: {kpi.get('label', 'unknown')}")

    # Deduplicate: same formula with different titles -> keep one (prefer higher priority)
    valid_kpis = _deduplicate_kpis_by_formula(valid_kpis)

    # Validate charts
    valid_charts = []
    for chart in data.get("charts", []):
        if validate_chart(chart, all_sheets, sheet_columns):
            valid_charts.append(chart)
        else:
            logger.warning(f"Removing invalid chart: {chart.get('title', 'unknown')}")

    # Update data with validated items
    data["kpis"] = valid_kpis
    data["charts"] = valid_charts

    return data


async def enrich_data(
    schema: DetectedSchema,
    stats: FileStats,
    **options: Any,
) -> LLMEnrichment:
    usage: Dict[str, Any] = {}

    # Use cache if available to avoid calling the LLM when possible.
    cache = LLMCache()
    cache_key = str(schema.to_dict())
    cached = await cache.get(cache_key)
    if cached:
        result = LLMEnrichment.model_validate(cached)
        result.dataset_profile = _dataset_profile_from_schema(schema)
        await cache.close()
        return result

    # Sub-pipeline hints (e.g. ['financial_transactions'])
    subpipeline_types = options.get("subpipeline_types") or []
    client = OpenRouterClient()
    logger.info("Calling LLM API", subpipelines=subpipeline_types)

    # Prepare compact context for LLM
    schema_summary = []
    total_rows = 0
    total_columns = 0
    has_dates = False
    has_amounts = False

    for s in schema.sheets:
        # Consistency Fix: Use raw column names so they match the ALLOWED COLUMNS list.
        # This reduces confusion for the LLM.
        s_name = _get_val(s, "name")
        s_columns = _get_val(s, "columns") or []

        sanitized_columns = [f"{_get_val(c, 'name')} ({_get_val(c, 'inferred_type')})" for c in s_columns]
        cols = sanitized_columns
        schema_summary.append(f"Sheet '{s_name}': {', '.join(cols)}")
        total_rows += _get_val(s, "row_count") or 0
        total_columns += len(s_columns)
        for c in s_columns:
            it = (str(_get_val(c, "inferred_type") or "")).lower()
            name_lower = str(_get_val(c, "name") or "").lower()
            if "date" in it or "time" in it or "date" in name_lower or "time" in name_lower:
                has_dates = True
            if any(tok in it for tok in ("float", "decimal", "double", "amount", "money", "currency")):
                has_amounts = True
        # Year-named columns (e.g. 2024, 2025 … 2074) represent a time dimension
        if not has_dates and _has_year_columns(s_columns):
            has_dates = True

    rel_summary = []
    for r in schema.relationships:
        rel_summary.append(f"Relation: {r.from_sheet}.{r.from_col} -> {r.to_sheet}.{r.to_col} ({r.type})")

    # Build compact stats block: one line per numeric or categorical column with key measures
    stats_lines = []
    stats_by_sheet: Dict[str, Dict[str, Any]] = {}
    for sheet_stats in getattr(stats, "sheets", []):
        col_map: Dict[str, Any] = {}
        for cs in sheet_stats.columns:
            col_map[cs.name] = cs
        stats_by_sheet[sheet_stats.name] = col_map

    for s in schema.sheets:
        curr_s_name = _get_val(s, "name")
        curr_s_cols = _get_val(s, "columns") or []
        col_map = stats_by_sheet.get(curr_s_name, {})
        for c in curr_s_cols:
            c_name = _get_val(c, "name")
            cs = col_map.get(c_name)
            if cs is None:
                continue

            # Numeric columns get mean, min, max, unique count, and quartiles
            cs_mean = _get_val(cs, "mean")
            if cs_mean is not None:
                stats_lines.append(
                    f"  {curr_s_name}.{c_name}: mean={cs_mean:.2g}, min={_get_val(cs, 'min_val')}, "
                    f"max={_get_val(cs, 'max_val')}, p25={_get_val(cs, 'p25') or 'N/A'}, "
                    f"p75={_get_val(cs, 'p75') or 'N/A'}, "
                    f"unique={_get_val(cs, 'unique_count')}"
                )
            # Categorical columns get unique count and top entries
            cs_unique = _get_val(cs, "unique_count") or 0
            if cs_unique > 0:
                top_entries = []
                cs_top = _get_val(cs, "top_categories")
                if cs_top:
                    for cat in cs_top[:3]:  # Top 3 only to save tokens
                        # cat is a dict from polars value_counts().to_dicts()
                        val = cat.get(c_name) or cat.get("label") or "unknown"
                        top_entries.append(f"{val} ({cat.get('count', 0)})")

                cat_info = f", top=[{', '.join(top_entries)}]" if top_entries else ""
                stats_lines.append(f"  {curr_s_name}.{c_name}: unique={cs_unique}{cat_info}")

    # Prompt optimization: cap stats lines to avoid hitting token limits or slowing down inference
    if len(stats_lines) > 50:
        logger.info("Capping stats lines in LLM prompt", original_count=len(stats_lines))
        stats_lines = stats_lines[:50] + ["  ... (remaining columns omitted to save tokens)"]

    dataset_profile = DatasetProfile(
        total_rows=total_rows or None,
        total_columns=total_columns or None,
        has_dates=has_dates,
        has_amounts=has_amounts,
        candidate_table_types=classify_table_types(schema),
    )

    # Canonical vocabulary: exact column names per sheet for copy-paste (reduces hallucination)
    allowed_columns: Dict[str, List[str]] = {}
    for s in schema.sheets:
        allowed_columns[s.name] = [c.name for c in s.columns]
    allowed_columns_json = json.dumps(allowed_columns, indent=2)

    # Few-shot examples using THIS file's real column names (injected dynamically)
    first_sheet = schema.sheets[0] if schema.sheets else None
    example_kpi = None
    example_chart = None
    if first_sheet and len(first_sheet.columns) >= 1:
        col_names = [c.name for c in first_sheet.columns]
        num_col = None
        date_col = None
        cat_cols: List[str] = []
        for c in first_sheet.columns:
            it = (c.inferred_type or "").lower()
            if num_col is None and any(t in it for t in ("int", "float", "decimal", "number")):
                num_col = c.name
            if date_col is None and ("date" in it or "time" in it):
                date_col = c.name
            if ("str" in it or "string" in it or "utf" in it) and (num_col is None or c.name != num_col):
                cat_cols.append(c.name)
        y_col = num_col or col_names[0]
        # Maximize split_by in example: prefer (date + cat) or (cat1 + cat2) so example chart shows legend
        if len(cat_cols) >= 2:
            x_col = cat_cols[0]
            split_col = cat_cols[1]
        elif date_col and cat_cols:
            x_col = date_col
            split_col = cat_cols[0]
        else:
            x_col = date_col or (cat_cols[0] if cat_cols else (col_names[1] if len(col_names) > 1 else col_names[0]))
            split_col = cat_cols[0] if cat_cols and cat_cols[0] != x_col else None
        example_kpi = (
            f'{{"label": "Total {y_col}", "formula": "SUM({y_col})", "sheet": "{first_sheet.name}", '
            f'"aggregation": "sum", "format": "number", "unit": "", "priority": "medium", '
            f'"description": "Sum of {y_col} across the dataset."}}'
        )
        chart_extra = f', "split_by": "{split_col}"' if split_col else ""
        example_chart = (
            f'{{"type": "bar", "title": "{y_col} by {x_col}", "description": "Breakdown of {y_col} by {x_col}", '
            f'"sheet": "{first_sheet.name}", "x_axis": "{x_col}", "y_axis": "{y_col}", '
            f'"aggregation": "sum", "format": "number", "unit": ""{chart_extra}}}'
        )

    prompt = f"""
You are analyzing an Excel dataset to generate a comprehensive business dashboard. Your task is to suggest KPIs, charts, and joins that provide actionable insights.

Follow these steps in order:

STEP 1: ANALYZE THE DATA STRUCTURE
- Review the SCHEMA section to understand sheets and columns
- Review the RELATIONSHIPS section to understand connections between sheets
- Review the COLUMN STATISTICS section to understand data distribution and values
- Identify key dimensions (categorical columns with few unique values)
- Identify key measures (numeric columns with aggregatable values)
- Identify temporal columns (dates or year columns)

STEP 2: PLAN YOUR RECOMMENDATIONS
- What domain does this data represent? (Sales, Finance, Operations, etc.)
- What are the 4-6 most important business questions this data can answer?
- What joins are needed to connect related sheets?
- What KPIs will answer these business questions?
- What charts will visualize these patterns effectively?

STEP 3: VALIDATE YOUR RECOMMENDATIONS
Before suggesting anything, verify:
✓ Every sheet name exists in ALLOWED COLUMNS
✓ Every column exists in ALLOWED COLUMNS for that sheet
✓ Every function is in ALLOWED FUNCTIONS
✓ Every aggregation is in ALLOWED AGGREGATIONS
✓ Numeric columns have mean/min/max in COLUMN STATISTICS
✓ Categorical columns for split_by have ≤15 unique values
✓ You're not using ID columns (unique_count ≈ total rows) with SUM/AVG

STEP 4: PROVIDE YOUR FINAL RECOMMENDATIONS
Format your response as valid JSON with all required fields.

=== STRICT RULES ===
1. **ONLY use column and sheet names from the ALLOWED COLUMNS list below**
2. **ONLY use functions from the ALLOWED FUNCTIONS list below**
3. **ONLY use aggregations from the ALLOWED AGGREGATIONS list below**
4. **Verify every column exists in COLUMN STATISTICS before using it**

=== ALLOWED COLUMNS (COPY EXACTLY, NO VARIATIONS) ===
{allowed_columns_json}

=== ALLOWED FUNCTIONS ===
Arithmetic: SUM, AVG, COUNT, COUNTIF, MIN, MAX
Statistical: MEDIAN, STDEV, VAR, PERCENTILE, MODE
Date: DATEDIFF, IS_BEFORE
Comparison: LT, GT
Math: RATIO, DIFF
Conditional: COALESCE
Note: CORR exists but is for insights only, not KPI formulas. For range analysis, use separate MIN and MAX KPIs.
Note: ABS, ROUND, FLOOR, CEIL, IF, CONCAT, LENGTH, IS_AFTER, LTE, GTE, EQ, NEQ, QUARTILE, RANGE are not implemented in the formula engine

=== ALLOWED AGGREGATIONS ===
sum, avg, count, min, max, median, stddev, stdev, var, mode, percentile

=== DATASET PROFILE ===
- Total Rows: {dataset_profile.total_rows}
- Total Columns: {dataset_profile.total_columns}
- Has Dates: {dataset_profile.has_dates}
- Has Amounts: {dataset_profile.has_amounts}
- Table Types: {dataset_profile.candidate_table_types}
- Domain: {", ".join(subpipeline_types) if subpipeline_types else "generic"}

=== SCHEMA ===
{chr(10).join(schema_summary)}

=== RELATIONSHIPS ===
{chr(10).join(rel_summary) if rel_summary else "No relationships detected."}

=== COLUMN STATISTICS ===
Use these to understand data ranges and make informed choices:
{chr(10).join(stats_lines) if stats_lines else "No stats available."}

=== RESPONSE FORMAT ===
Respond STRICTLY in valid JSON matching this structure:

{{
  "reasoning": "STEP 1 ANALYSIS: I identified [X sheets] with [Y relationships]. Key dimensions: [categorical columns]. Key measures: [numeric columns]. Temporal columns: [date/year columns].

  STEP 2 PLANNING: Domain is [domain]. Business questions: 1) [question], 2) [question], etc. Needed joins: [joins]. Proposed KPIs: [kpis]. Proposed charts: [charts].

  STEP 3 VALIDATION: ✓ All sheets exist in ALLOWED COLUMNS. ✓ All columns verified in COLUMN STATISTICS. ✓ All functions from ALLOWED FUNCTIONS. ✓ No ID columns used with SUM/AVG. ✓ split_by columns have ≤15 unique values.",

  "domain": "e.g., Sales, HR, Finance, Operations",

  "summary": "2-sentence business summary of the dataset",

  "joins": [
    {{"left_sheet": "<exact_name>", "right_sheet": "<exact_name>", "on": "<exact_column_name>", "how": "inner"}}
  ],

  "kpis": [
    {example_kpi or '{"label": "Total Revenue", "formula": "SUM(Revenue)", "sheet": "Sales", "aggregation": "sum", "format": "currency", "unit": "$", "priority": "high", "description": "Total revenue across all transactions"}'}
  ],

  "insights": [
    {{"text": "Actionable insight based on data", "severity": "medium", "type": "kpi", "title": "Brief Title"}}
  ],

  "charts": [
    {example_chart or '{"type": "bar", "title": "Revenue by Region", "description": "Breakdown of revenue", "sheet": "Sales", "x_axis": "Region", "y_axis": "Revenue", "aggregation": "sum", "format": "currency", "unit": "$"}'}
  ]
}}

=== CRITICAL VALIDATION CHECKS (Your output will be validated) ===
Before suggesting any KPI or chart, verify:
1. ✓ Sheet name exists in ALLOWED COLUMNS
2. ✓ Every column in formula exists in that sheet's ALLOWED COLUMNS
3. ✓ Every function is in ALLOWED FUNCTIONS
4. ✓ Aggregation is in ALLOWED AGGREGATIONS
5. ✓ Column has data (check COLUMN STATISTICS unique_count > 0)
6. ✓ For SUM/AVG: column has numeric values (check mean/min/max in stats)
7. ✓ For ID columns (unique_count ≈ total rows): use COUNT, not SUM/AVG
8. ✓ split_by column has ≤15 distinct values (check unique_count in stats)

=== CHAIN-OF-THOUGHT REASONING ===
Include a "reasoning" field explaining:
- What patterns you identified in the schema
- Which columns you chose and why (reference COLUMN STATISTICS)
- Why each KPI provides business value
- How charts complement each other

This helps validate your suggestions are based on actual data, not hallucinations.

    IMPORTANT:
    - If you need data from multiple sheets for a KPI or Chart, first specify the "joins" required.
    - Joins: use ALLOWED sheet names only. Each join: left_sheet, right_sheet, "on" (one key column name when same in both sheets) or "left_on"+"right_on" when names differ, "how": "inner" or "left". For joined data use a virtual sheet name like SheetA+SheetB (e.g. Orders+Customer).
    - severity must be one of: 'high', 'medium', 'low', 'info', 'warning'.
    - type in charts must be one of: 'bar', 'line', 'area', 'pie'.
    - y_axis can be a raw column OR a formula.
    - aggregation MUST be: 'sum', 'avg', 'count', 'min', 'max', 'median', 'stddev', or 'var'.
    - format MUST be: 'number', 'percentage' or 'currency'.
    - **CRITICAL — x_axis MUST be a real column from COLUMN STATISTICS.** Never use computed values, variable IDs, or abstract names. Only pick actual columns that exist in the data.
    - **CRITICAL — y_axis MUST be a real column or formula.** For aggregate charts, ensure it references existing columns.
    - NEVER put a formula like DATEDIFF(...) inside the "aggregation" field. Put it in "y_axis".
    - formula can use:
        - DATEDIFF(StartCol, EndCol) for duration in days (Float).
        - IS_BEFORE(A, B) returns 1.0 if A <= B, else 0.0. (Perfect for "On-Time" rate with aggregation="avg").
        - RATIO(NomCol, DenomCol) for division.
        - DIFF(Col1, Col2) for subtraction.
        - LT(A, B) or GT(A, B) for numeric or date comparisons.
    - IMPORTANT: If the x_axis of a chart is a Date/Time, the system will automatically bucket it by Month. You don't need to format the date yourself.
    - To get a "Rate" (like On-Time Performance %), use IS_BEFORE(Actual, Promised) with aggregation="avg".
    - ADVANCED STATS: Use aggregation="median", "stddev" or "var" for deeper insights into volatility and distributions.
    - ADVANCED KPI FORMULAS:
        - PERCENTILE(col, 95) for top-tier analysis.
    - CRITICAL — Return/Defect/Status Rates: If a column contains Yes/No, True/False, or similar boolean-like values, use it directly in the formula field (e.g. formula="ReturnStatus") with aggregation="avg". The system will automatically map Yes→1, No→0 and compute the average. Do NOT use SUM on these columns.
    - CRITICAL — KPI Descriptions: The "description" field MUST be non-technical and business-oriented. Avoid mentioning formulas or column names. Focus on the "why" and "what" (e.g., "Measures our efficiency in converting leads" instead of "Average of conversion_flag").
    - CRITICAL — Column selection: Check COLUMN STATISTICS above before choosing a KPI formula. NEVER use aggregation="sum" or aggregation="avg" on a column whose unique_count equals (or nearly equals) the total row count — those are IDs/keys. Use aggregation="count" or pick a true measure column instead.
    - **CRITICAL — KPI Validation**: ONLY reference columns that appear in COLUMN STATISTICS. Do NOT invent column names or assume field names. If a column doesn't exist in the stats, DO NOT use it in the formula. Only suggest KPIs if you can verify the columns exist.
    - **CRITICAL — Per-entity KPIs**: For KPIs like "X per Y" (e.g. "Orders per Store", "Revenue per Region"), set "group_by" to the column that identifies each Y, from ALLOWED COLUMNS (e.g. storeid, region, department_id). Pick the actual column name that exists in the sheet.

    CHART & KPI REQUIREMENTS:
    - Suggest exactly 4-6 high-quality KPIs covering different dimensions (volume, rate, time, financial).
    - Suggest exactly 5-7 charts — this is a data-rich dashboard, make it comprehensive.
    - Each chart MUST have a unique combination of x_axis + y_axis (no duplicate charts).
    - **NEVER suggest a chart with x_axis values that look like numeric IDs, computed values, or non-human-readable data.** Examples to AVOID: "Pop_AS", "-2.18624851", "0.007772825", "PrestRP". Only use readable categorical or temporal columns.
    - Vary chart types: use a mix of 'bar', 'line', 'area', 'pie' where appropriate.
    - Keep summary to max 2 sentences.

    CHART TYPE RULES:
    - NEVER use a Pie Chart for time-series data.
    - ONLY use Pie Chart for part-to-whole with LESS THAN 6 distinct categories (Status, Region, Category, etc.).
    - If x_axis is a Date/Time column: ONLY use 'line', 'area', or 'bar'.
    - Use 'bar' for: categorical rankings, comparisons across groups, distributions. When comparing a metric across categories (e.g. Region, Status), set split_by to that category column so the chart shows stacked or grouped bars with a legend.
    - Use 'line'/'area' for: trends over time, sequential data. Add split_by (e.g. Region, Segment) when the data has a categorical dimension to show multiple series with a legend.
    - Use 'pie' for: composition/breakdown (Status split, Category share, etc.).
    - When a chart compares a measure across a dimension (e.g. Revenue by Month by Region), set split_by to the dimension column (e.g. "Region") so the engine draws one series per value and a legend.

    LEGENDS (split_by):
    - At least 2–3 of your charts MUST include a "split_by" field set to a categorical column from ALLOWED COLUMNS (e.g. Region, Status, Category, Type). This produces multi-series charts with a legend.
    - split_by MUST be a column name from ALLOWED COLUMNS; prefer string/categorical columns with a limited number of distinct values.
    - Use split_by whenever you break down a metric by a dimension (region, status, category, product type, etc.).
    - Never set split_by to "none" or "null" — omit the field instead.

    CHART DIVERSITY GUIDELINES — generate charts across these dimensions:
    1. Time trends: how key metrics evolve over time (line/area). Prefer adding split_by to a categorical column (e.g. Region, Product) when the data has such a dimension to show multiple series with a legend.
    2. Category distributions: breakdown by category, region, status (bar/pie). Use split_by when you have a second dimension (e.g. metric by Category split_by Status) so the chart has a legend.
    3. Performance rankings: top N by value (bar, sorted)
    4. Rate/ratio metrics: e.g. on-time rate, return rate by segment (bar)
    5. Volume comparison: count of transactions/orders by group (bar). Use split_by to break down by a second category (e.g. by Region split_by Status) for stacked/grouped bars with a legend.
    6. Financial overview: revenue, cost, or weight by dimension (bar/line). Use split_by (e.g. Region, Category) to get a legend and multi-series.
    7. Duration/delay analysis: average processing time by category (bar)
    8. Cross-sheet joined metrics: combine sheets to show multi-dimensional insights
    9. Multi-series and legends: At least 2–3 charts must use split_by with a categorical column from ALLOWED COLUMNS so the dashboard shows legends (stacked/grouped bars, multiple lines/areas).
    - CRITICAL — split_by cardinality: ONLY use a column with ≤ 15 distinct values for split_by.
      Never use description, nom_de_la_variable, or any ID/label column with many unique values.
    """

    # Inject domain-specific addendum for wide-format budget/projection tables
    budget_score = max(
        (ct.get("score", 0.0) for ct in dataset_profile.candidate_table_types if ct.get("type") == "budget_projection"),
        default=0.0,
    )
    if budget_score >= 0.72:
        try:
            addendum = _build_budget_prompt_addendum(schema, stats_by_sheet)
            if addendum:
                prompt = prompt + addendum
                logger.info("Injected budget_projection prompt addendum", score=budget_score)
        except Exception:
            logger.exception("Budget prompt addendum generation failed, continuing without it")

    system_prompt = (
        "You are an expert Data Analyst inside a SaaS product. "
        "Your goal is to suggest the best visualizations and KPIs based on file schema and relationships. "
        "Suggest visualizations that use legends (split_by) where a metric is broken down by a category "
        "(region, status, type, etc.), so at least 2\u20133 charts include split_by. "
        "CRITICAL: split_by must only reference columns with \u2264 15 distinct values."
    )

    response = await client.complete(prompt, system_prompt)

    usage = getattr(response, "usage", {})
    if not isinstance(usage, dict):
        usage = {}
    total = usage.get("total_tokens")
    if total is None:
        total = (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0)
    usage["total_tokens"] = total

    if not response.parsed_json:
        result = LLMEnrichment(
            domain="Unknown",
            summary="No summary available.",
            kpis=[],
            insights=[],
            charts=[],
            joins=[],
            usage=usage,
            dataset_profile=dataset_profile,
        )

        await cache.set(cache_key, result.to_dict())
        await cache.close()
        return result

    data = response.parsed_json

    # Advanced validation layer to catch hallucinations
    try:
        data, validation_errors = validate_llm_output(data, schema, stats_by_sheet=stats_by_sheet)
        if validation_errors:
            critical_errors = [e for e in validation_errors if e.severity == "critical"]
            high_errors = [e for e in validation_errors if e.severity == "high"]
            logger.warning(
                "LLM output had validation issues",
                critical_count=len(critical_errors),
                high_count=len(high_errors),
                total_errors=len(validation_errors),
            )
            # Log sample of critical errors for debugging
            for error in critical_errors[:3]:
                logger.warning(
                    "Critical validation error",
                    type=error.hallucination_type,
                    message=error.message,
                    field=error.field,
                )
    except Exception:
        logger.exception("Advanced validation failed, falling back to basic validation")

    # Validate and filter LLM response (pass stats for cardinality guard)
    data = validate_and_filter_llm_response(data, schema, stats_by_sheet=stats_by_sheet)

    # Core fix: Use Pydantic's model_validate to handle defaults and extra fields automatically
    result = LLMEnrichment.model_validate(data)
    # Persist provider usage so job.llm_tokens_used can be tracked
    result.usage = usage if isinstance(usage, dict) else {}

    # Attach dataset profile so downstream consumers (dashboard builder, sub-pipelines)
    # can reason about dataset shape and potential domain types.
    result.dataset_profile = dataset_profile

    # Auto-inject any missing join recommendations referenced by KPIs/charts
    try:
        result = auto_inject_joins(result, schema)
    except Exception:
        logger.exception("Auto-inject joins failed, continuing without injection")

    await cache.set(cache_key, result.to_dict())
    await cache.close()
    return result
