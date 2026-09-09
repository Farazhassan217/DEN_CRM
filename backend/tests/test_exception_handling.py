import pytest

def test_404_standardized_error(client):
    """Verify that 404 errors return the standardized error envelope."""
    response = client.get("/api/v1/non_existent_endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "timestamp" in data["error"]


def test_422_validation_standardized_error(client):
    """Verify that validation errors return the standardized envelope with details."""
    # POST to /auth/login with invalid data types
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "timestamp" in data["error"]
