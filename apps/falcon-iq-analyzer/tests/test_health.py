import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from falcon_iq_analyzer.main import app

    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "llm_provider" in data
    assert "storage_type" in data
    assert "storage_healthy" in data
