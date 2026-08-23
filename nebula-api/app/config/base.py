import os
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """General project metadata and path configurations."""

    PROJECT_NAME: str = "Nebula System"
    VERSION: str = "3.0.0"
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = r"E:\log"
    # Comma-separated origins, or "*" for allow-all (development only)
    CORS_ORIGINS: str = "*"

    # Current file: app/config/base.py (3 levels up to nebula-api root)
    ROOT_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
