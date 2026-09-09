import pytest
import uuid
from datetime import datetime
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    AuthService
)
from app.schemas.user import User
from app.core.roles import UserRole
from app.models.user import UserModel

@pytest.mark.asyncio
async def test_refresh_token_rotation(monkeypatch):
    """Verify refresh token generation, rotation, and old token invalidation."""
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    
    dummy_user = User(
        id=uuid.UUID(user_id),
        email="doctor@example.com",
        full_name="Dr. Smith",
        role=UserRole.CLINIC_MANAGER,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        assigned_clinics=["clinic_1"]
    )
    
    async def mock_get_by_id(uid):
        return dummy_user
        
    monkeypatch.setattr(UserModel, "get_by_id", mock_get_by_id)
    
    payload = {
        "sub": user_id,
        "email": dummy_user.email,
        "role": dummy_user.role.value,
        "organization_id": org_id,
        "assigned_clinics": ["clinic_1"]
    }
    
    # 1. Create refresh token
    refresh_tok = create_refresh_token(payload)
    decoded = decode_refresh_token(refresh_tok)
    assert decoded is not None
    assert str(decoded.user_id) == user_id
    assert decoded.token_type == "refresh"
    
    # 2. Rotate tokens
    new_access, new_refresh, returned_user = await AuthService.rotate_tokens(refresh_tok)
    assert new_access is not None
    assert new_refresh is not None
    assert new_refresh != refresh_tok
    assert returned_user.email == dummy_user.email
    
    # 3. Old refresh token must be revoked and fail if reused
    old_decoded = decode_refresh_token(refresh_tok)
    assert old_decoded is None
