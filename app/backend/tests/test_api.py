import pytest
from fastapi.testclient import TestClient
from ..main import app
import time

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "EdgeCine" in response.json()["app"]

def test_health_check_logic():
    response = client.get("/health")
    # Even if it returns 503 (unhealthy due to no DB), we check the structure
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "onnx_model" in data["services"] or "neural_engine" in data["services"]

def test_recommend_validation():
    # Test that short queries or missing params trigger validation
    response = client.get("/films/recommend")
    assert response.status_code == 422 # Unprocessable Entity
