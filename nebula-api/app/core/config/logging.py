import logging
import os
import sys

from app.core.request_context import get_trace


class RequestContextFilter(logging.Filter):
    """Inject request_id / session_id from the active RequestTrace."""

    def filter(self, record: logging.LogRecord) -> bool:
        trace = get_trace()
        record.request_id = trace.request_id if trace else "-"
        record.session_id = trace.session_id if trace else "-"
        return True


def setup_logging(level: str = "INFO", log_dir: str = r"E:\log") -> logging.Logger:
    """Configure application-wide logging to console and a log file."""

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "nebula-api.log")

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - "
        "rid=%(request_id)s sid=%(session_id)s - %(message)s"
    )

    context_filter = RequestContextFilter()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    logging.basicConfig(
        level=numeric_level,
        handlers=[stream_handler, file_handler],
        force=True,
    )

    logger = logging.getLogger("nebula")
    logger.info("Logging to console and %s", log_path)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger under the 'nebula' namespace."""
    return logging.getLogger(f"nebula.{name}")
