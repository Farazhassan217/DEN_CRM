import pytest
from app.services.auth import create_access_token, decode_access_token, revoke_token, is_token_revoked
from app.core.roles import UserRole
import uuid

def test_jwt_revocation_lifecycle():
    """Verify that tokens have unique JTIs and can be revoked server-side."""
    user_id = str(uuid.uuid4())
    data = {
        "sub": user_id,
        "email": "doctor@example.com",
        "role": UserRole.SUPER_ADMIN.value,
        "organization_id": str(uuid.uuid4()),
        "assigned_clinics": []
    }
    
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert str(decoded.user_id) == user_id
    assert decoded.jti is not None
    
    # Token should not be revoked yet
    assert not is_token_revoked(decoded.jti)
    
    # Revoke token
    success = revoke_token(token)
    assert success is True
    
    # Now token should be marked revoked
    assert is_token_revoked(decoded.jti) is True
    
    # decode_access_token should now reject the token
    assert decode_access_token(token) is None


def test_logout_endpoint_revokes_token(client, monkeypatch):
    """Verify that calling /auth/logout actively revokes the token."""
    user_id = str(uuid.uuid4())
    token = create_access_token({
        "sub": user_id,
        "email": "admin@example.com",
        "role": UserRole.SUPER_ADMIN.value,
        "organization_id": str(uuid.uuid4()),
        "assigned_clinics": []
    })
    
    # Mock UserModel.get_by_id so get_current_user succeeds
    from app.schemas.user import User
    from app.models.user import UserModel
    from datetime import datetime
    
    dummy_user = User(
        id=uuid.UUID(user_id),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        assigned_clinics=[]
    )
    
    async def mock_get_by_id(uid):
        return dummy_user
        
    monkeypatch.setattr(UserModel, "get_by_id", mock_get_by_id)
    
    # Logout with valid token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
    
    # Decoded token must now be None
    assert decode_access_token(token) is None
    
    # Accessing /auth/me with revoked token must fail with 401
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 401
