import os
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """General project metadata and path configurations."""

    PROJECT_NAME: str = "Nebula System"
    VERSION: str = "3.0.0"
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = r"E:\log"

    # Current file: app/core/config/base.py (4 levels up to nebula-api root)
    ROOT_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
