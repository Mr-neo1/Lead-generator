"""
Shared pytest fixtures for Lead Engine tests.
Uses an in-memory SQLite database so tests run without external services.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Point at an in-memory SQLite for all tests ────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)
os.environ.setdefault("USE_REDIS", "false")
os.environ.setdefault("API_KEY", "")  # auth off for unit tests

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

# Create a fresh engine/session factory for tests
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function", autouse=False)
def db_session():
    """Provide a clean database session for each test, rolled back after."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with the test DB injected via dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
