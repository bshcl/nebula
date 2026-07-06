import os

from pydantic import computed_field
from pydantic_settings import SettingsConfigDict

from .ai_settings import AISettings
from .base import BaseConfig
from .logging import setup_logging, get_logger


class Settings(BaseConfig, AISettings):
    """Unified settings container for the entire application."""

    model_config = SettingsConfigDict(
        # Ignore extra env variables
        env_file=".env",
        extra="ignore",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DB_PATH(self) -> str:
        """Absolute path to the SQLite database file."""
        return os.path.join(self.ROOT_DIR, "app", "data", "nebula.db")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy database URL for the SQLite database."""
        return f"sqlite:///{self.DB_PATH}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """Parse CORS_ORIGINS into a list for FastAPI middleware."""
        raw = self.CORS_ORIGINS.strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
logger = setup_logging(settings.LOG_LEVEL, settings.LOG_DIR)

__all__ = ["settings", "get_logger", "logger"]
