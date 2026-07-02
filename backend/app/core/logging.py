import logging
import sys
from contextvars import ContextVar

# ContextVar to store the current request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class CorrelationIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_var.get()
        return super().format(record)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = CorrelationIdFormatter(
        "[%(asctime)s] [%(levelname)s] [ReqID: %(request_id)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    # Suppress noise from libraries
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger("scheduler")
