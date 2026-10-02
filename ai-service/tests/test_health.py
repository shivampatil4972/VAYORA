"""
Module 0 — AI Service health check tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Health endpoint must return 200 with status UP."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "vayora-ai-service"
    assert "timestamp" in data
    assert data["uptime_seconds"] >= 0
