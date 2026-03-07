"""Domain-specific sub-pipeline registry.

This module provides a small abstraction layer for \"child\" pipelines that
augment the generic parent pipeline when a dataset looks like a known table type
e.g. financial_transactions, sales_pipeline, saas_usage.

The selection is based on DatasetProfile.candidate_table_types populated by
llm_enricher.classify_table_types().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

import structlog

from app.pipeline.llm_enricher import DatasetProfile

logger = structlog.get_logger()


@dataclass
class SubPipelineConfig:
    """Configuration for a domain-specific child pipeline.

    - type_name: the logical table type (e.g. 'financial_transactions').
    - min_score: minimum candidate_table_types score required to activate.
    - steps: logical step names to run in addition to the parent pipeline.
    - options: optional per-step options (e.g. LLM prompt ids).
    """

    type_name: str
    min_score: float = 0.6
    steps: List[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


SUBPIPELINES: dict[str, SubPipelineConfig] = {
    "financial_transactions": SubPipelineConfig(
        type_name="financial_transactions",
        min_score=0.6,
        steps=[
            # These are *logical* step names; concrete implementations can be
            # introduced incrementally as the product evolves.
            # Examples: 'financial_time_agg', 'financial_variance', 'financial_outliers'
        ],
        options={
            "llm_prompt_id": "financial_enrichment_v1",
        },
    ),
    "sales_pipeline": SubPipelineConfig(
        type_name="sales_pipeline",
        min_score=0.6,
        steps=[
            # e.g. 'sales_stage_conversion', 'sales_cycle_time'
        ],
        options={
            "llm_prompt_id": "sales_enrichment_v1",
        },
    ),
    "saas_usage": SubPipelineConfig(
        type_name="saas_usage",
        min_score=0.6,
        steps=[
            # e.g. 'saas_retention', 'saas_feature_usage'
        ],
        options={
            "llm_prompt_id": "saas_enrichment_v1",
        },
    ),
    "budget_projection": SubPipelineConfig(
        type_name="budget_projection",
        min_score=0.7,
        steps=[],
        options={
            "llm_prompt_id": "budget_projection_v1",
        },
    ),
}


def select_subpipelines(profile: DatasetProfile | None) -> list[SubPipelineConfig]:
    """Select sub-pipelines to activate based on DatasetProfile.

    For now this simply matches profile.candidate_table_types against the
    SUBPIPELINES registry and keeps those whose score exceeds min_score.
    """

    if profile is None or not profile.candidate_table_types:
        return []

    active: list[SubPipelineConfig] = []
    for candidate in profile.candidate_table_types:
        t = candidate.get("type")
        score = float(candidate.get("score", 0.0) or 0.0)
        cfg = SUBPIPELINES.get(t)
        if not cfg:
            continue
        if score >= cfg.min_score:
            logger.info("Activating sub-pipeline", type=t, score=score)
            active.append(cfg)

    return active
