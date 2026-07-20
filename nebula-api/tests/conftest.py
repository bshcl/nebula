"""Shared pytest fixtures for nebula-api."""

import os
import tempfile

# Set test env before any app imports (settings loads at import time).
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "test-maps-key")
os.environ.setdefault("LOG_DIR", os.path.join(tempfile.gettempdir(), "nebula-test-logs"))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import chat, inventory
from app.core.database import get_db
from app.models.db_models import Base


@pytest.fixture()
def client() -> TestClient:
    """API test client with in-memory SQLite (no MCP / full app lifespan)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(inventory.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(client: TestClient):
    """Yield a DB session bound to the same in-memory engine as `client`."""
    gen = client.app.dependency_overrides[get_db]()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
