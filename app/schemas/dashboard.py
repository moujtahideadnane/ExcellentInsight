import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class KPIWidget(BaseModel):
    label: str
    value: Any
    unit: Optional[str] = None
    change: Optional[float] = None
    priority: Optional[Literal["high", "medium", "low"]] = "medium"
    format: str
    coverage: Optional[float] = None
    formula: Optional[str] = None
    description: Optional[str] = None


class KPIUpdateRequest(BaseModel):
    formula: str


class ChartWidget(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    unit: Optional[str] = None
    sheet: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    data: List[Dict[str, Any]]
    x_key: str
    y_key: str
    series_keys: Optional[List[str]] = None
    coverage: Optional[float] = None


class InsightWidget(BaseModel):
    type: str
    severity: Literal["high", "medium", "low", "info", "warning"]
    text: str
    title: Optional[str] = None


class DashboardResponse(BaseModel):
    job_id: uuid.UUID
    overview: Dict[str, Any]
    kpis: List[KPIWidget]
    charts: List[ChartWidget]
    insights: List[InsightWidget]
    relationships: List[Dict[str, Any]] = []
    joins: List[Dict[str, Any]] = []
    data_preview: Dict[str, List[Dict[str, Any]]]
    stats: Optional[List[Dict[str, Any]]] = None
    dataset_profile: Optional[Dict[str, Any]] = None
    created_at: datetime
    processing_time_ms: Optional[int] = None
    schema_summary: Optional[Dict[str, Any]] = None
    llm_usage: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)
