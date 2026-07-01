import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure application-wide logging once at startup."""

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    return logging.getLogger("nebula")

def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger under the 'nebula' namespace."""
    return logging.getLogger(f"nebula.{name}")

