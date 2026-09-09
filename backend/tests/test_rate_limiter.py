import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_login_rate_limiting():
    """Verify that /auth/login rejects requests after exceeding 5 requests per minute per IP."""
    client = TestClient(app, raise_server_exceptions=False)
    
    # 5 attempts allowed (may fail auth with 400 or 401, but not 429)
    for i in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": f"test{i}@example.com", "password": "password123"}
        )
        assert response.status_code in [400, 401], f"Attempt {i+1} got unexpected status {response.status_code}"

    # 6th attempt MUST trigger 429 Too Many Requests
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "overflow@example.com", "password": "password123"}
    )
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "error" in data
    assert "timestamp" in data["error"]
