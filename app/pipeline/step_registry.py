"""Pipeline step registry.

Provides a decorator-based registration system and a factory function
to build the ordered step list from configuration.

Usage::

    @register_step("parsing")
    class ParsingStep:
        name = "parsing"
        async def execute(self, context): ...

    # Later:
    steps = get_pipeline_steps()  # returns instances in configured order
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.pipeline.step_base import PipelineStep

logger = structlog.get_logger()

# ── Global registry ──────────────────────────────────────────────────────────
_REGISTRY: dict[str, type[PipelineStep]] = {}


def register_step(name: str):
    """Class decorator that registers a PipelineStep implementation."""

    def decorator(cls: type[PipelineStep]):
        if name in _REGISTRY:
            logger.warning("Overwriting pipeline step registration", step=name)
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_registered_step(name: str) -> type[PipelineStep] | None:
    """Look up a registered step class by name."""
    return _REGISTRY.get(name)


def list_registered_steps() -> list[str]:
    """Return all registered step names."""
    return list(_REGISTRY.keys())


# ── Pipeline configuration ───────────────────────────────────────────────────


@dataclass
class StepConfig:
    """Configuration for a single pipeline step."""

    name: str
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)


# Default pipeline: the order in which steps execute
DEFAULT_PIPELINE: list[StepConfig] = [
    StepConfig(name="parsing"),
    StepConfig(name="schema"),
    StepConfig(name="stats"),
    StepConfig(name="llm"),
    StepConfig(name="dashboard"),
]


def get_pipeline_steps(
    config: list[StepConfig] | None = None,
) -> list[PipelineStep]:
    """Instantiate pipeline steps from config (or the default pipeline).

    Skips disabled steps and raises ValueError for unknown step names.
    """
    cfg = config or DEFAULT_PIPELINE
    steps: list[PipelineStep] = []

    for step_cfg in cfg:
        if not step_cfg.enabled:
            continue

        cls = _REGISTRY.get(step_cfg.name)
        if cls is None:
            raise ValueError(
                f"Pipeline step '{step_cfg.name}' not found in registry. Available: {list(_REGISTRY.keys())}"
            )
        steps.append(cls())

    return steps
