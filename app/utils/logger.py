import structlog


def setup_logging():
    structlog.configure(processors=[structlog.processors.JSONRenderer()])


setup_logging()
logger = structlog.get_logger()
