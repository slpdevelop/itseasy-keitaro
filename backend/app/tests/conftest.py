"""Test fixtures for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from app.main import get_app


@pytest.fixture(scope="module")
def app() -> TestClient:
    """Create test FastAPI application."""
    client = TestClient(get_app())
    return client
