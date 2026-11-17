"""Tests for API v1 endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(app: TestClient) -> None:
    """Test health check endpoint returns 200 OK."""
    response = app.get("/api/v1/")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
