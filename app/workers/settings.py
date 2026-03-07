import structlog

from app.config import get_settings
from app.pipeline.orchestrator import run_analysis_pipeline
from app.workers.queue_config import QUEUE_SETTINGS

settings = get_settings()
logger = structlog.get_logger()


async def startup(ctx):
    logger.info("Worker starting up...")


async def shutdown(ctx):
    logger.info("Worker shutting down...")


class WorkerSettings:
    functions = [run_analysis_pipeline]
    redis_settings = QUEUE_SETTINGS["redis_settings"]

    # Advanced arq settings
    max_jobs = QUEUE_SETTINGS["max_jobs"]
    job_timeout = QUEUE_SETTINGS["job_timeout"]
    result_ttl = QUEUE_SETTINGS["result_ttl"]

    on_startup = startup
    on_shutdown = shutdown
