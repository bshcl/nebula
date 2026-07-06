import logging
import os
import sys


def setup_logging(level: str = "INFO", log_dir: str = r"E:\log") -> logging.Logger:
    """Configure application-wide logging to console and a log file."""

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "nebula-api.log")

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

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
