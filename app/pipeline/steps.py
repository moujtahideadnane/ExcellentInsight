"""Implementations of registered pipeline steps.

Wraps the existing pipeline logic (parser, schema_detector, etc.) into
reusable PipelineStep classes registered with the StepRegistry.
"""

from __future__ import annotations

from app.pipeline import (
    dashboard_builder,
    llm_enricher,
    parser,
    schema_detector,
    stats_engine,
)
from app.pipeline.step_base import PipelineContext, StepTelemetry
from app.pipeline.step_registry import register_step


@register_step("parsing")
class ParsingStep:
    name = "parsing"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        telemetry = StepTelemetry(step_name=self.name)
        try:
            parsed_data = await parser.parse_excel(context.file_path, job_id=context.job_id)
            context.dataframes = parsed_data.dataframes

            # Record metrics
            telemetry.rows_processed = sum(df.height for df in parsed_data.dataframes.values())
            telemetry.columns_processed = sum(len(df.columns) for df in parsed_data.dataframes.values())
            telemetry.finish()
        except Exception as e:
            telemetry.finish(error=str(e))
            raise
        finally:
            context.telemetry.append(telemetry)

        return context


@register_step("schema")
class SchemaStep:
    name = "schema"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        telemetry = StepTelemetry(step_name=self.name)
        try:
            context.schema = schema_detector.detect_schema(context.dataframes)

            telemetry.columns_processed = sum(len(s.columns) for s in context.schema.sheets)
            telemetry.finish()
        except Exception as e:
            telemetry.finish(error=str(e))
            raise
        finally:
            context.telemetry.append(telemetry)

        return context


@register_step("stats")
class StatsStep:
    name = "stats"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        telemetry = StepTelemetry(step_name=self.name)
        try:
            context.stats = stats_engine.compute_stats(context.dataframes, context.schema)
            telemetry.finish()
        except Exception as e:
            telemetry.finish(error=str(e))
            raise
        finally:
            context.telemetry.append(telemetry)

        return context


@register_step("llm")
class LLMStep:
    name = "llm"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        telemetry = StepTelemetry(step_name=self.name)
        try:
            # Pass options (e.g. temperature) if present
            options = context.step_options.get(self.name, {})
            context.enrichment = await llm_enricher.enrich_data(context.schema, context.stats, **options)
            telemetry.finish()
        except Exception as e:
            telemetry.finish(error=str(e))
            raise
        finally:
            context.telemetry.append(telemetry)

        return context


@register_step("dashboard")
class DashboardStep:
    name = "dashboard"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        telemetry = StepTelemetry(step_name=self.name)
        try:
            context.dashboard = dashboard_builder.build_dashboard(
                context.dataframes, context.schema, context.stats, context.enrichment
            )
            telemetry.finish()
        except Exception as e:
            telemetry.finish(error=str(e))
            raise
        finally:
            context.telemetry.append(telemetry)

        return context
