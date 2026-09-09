# pyrefly: ignore [missing-import]
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.auth import create_access_token
from app.core.roles import UserRole
from app.schemas.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.common import ActionSuccessResponse
from app.core.async_runner import execute_query, run_in_thread


@pytest.fixture
def superadmin_headers():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    token = create_access_token({
        "sub": user_id,
        "email": "superadmin@example.com",
        "role": UserRole.SUPER_ADMIN.value,
        "organization_id": org_id,
        "assigned_clinics": ["clinic_main"]
    })
    return {"Authorization": f"Bearer {token}"}, user_id, org_id


def test_health_check_endpoint(client):
    """Verify enhanced health check returns diagnostic status of components."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "ai_engine" in data["components"]
    assert "timestamp" in data


def test_action_success_response_schema():
    """Verify ActionSuccessResponse schema fields and serialization."""
    resp = ActionSuccessResponse(
        success=True,
        message="Action completed",
        data={"lead_id": "lead_123"}
    )
    assert resp.success is True
    assert resp.message == "Action completed"
    assert resp.data["lead_id"] == "lead_123"


def test_leads_paginated_response_contract(client, superadmin_headers, monkeypatch):
    """Verify GET /api/v1/leads/ returns PaginatedResponse envelope."""
    headers, user_id, org_id = superadmin_headers

    from app.models.user import UserModel
    from app.models.lead import LeadModel
    from app.schemas.lead import Lead, LeadStatus, LeadSource

    dummy_admin = User(
        id=uuid.UUID(user_id),
        email="superadmin@example.com",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_main"]
    )
    monkeypatch.setattr(UserModel, "get_by_id", AsyncMock(return_value=dummy_admin))

    dummy_lead = Lead(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        clinic_id="clinic_main",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1234567890",
        status=LeadStatus.NEW,
        source=LeadSource.WEBSITE,
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    from app.services.lead import LeadService
    monkeypatch.setattr(LeadService, "get_leads_by_organization", AsyncMock(return_value=([dummy_lead], 1)))

    response = client.get("/api/v1/leads/?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


def test_patch_lead_endpoint(client, superadmin_headers, monkeypatch):
    """Verify PATCH /api/v1/leads/{id} performs partial updates (Concept #2)."""
    headers, user_id, org_id = superadmin_headers

    from app.models.user import UserModel
    from app.services.lead import LeadService
    from app.schemas.lead import Lead, LeadStatus, LeadSource

    dummy_admin = User(
        id=uuid.UUID(user_id),
        email="superadmin@example.com",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_main"]
    )
    monkeypatch.setattr(UserModel, "get_by_id", AsyncMock(return_value=dummy_admin))

    lead_id = str(uuid.uuid4())
    updated_lead = Lead(
        id=lead_id,
        organization_id=org_id,
        clinic_id="clinic_main",
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+1234567890",
        status=LeadStatus.CONTACTED,
        source=LeadSource.WEBSITE,
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    monkeypatch.setattr(LeadService, "update_lead", AsyncMock(return_value=updated_lead))

    response = client.patch(
        f"/api/v1/leads/{lead_id}",
        json={"first_name": "Jane", "status": "contacted"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Jane"
    assert response.json()["status"] == "contacted"


def test_delete_lead_status_204(client, superadmin_headers, monkeypatch):
    """Verify DELETE /api/v1/leads/{id} returns 204 No Content (Concept #4)."""
    headers, user_id, org_id = superadmin_headers

    from app.models.user import UserModel
    from app.services.lead import LeadService

    dummy_admin = User(
        id=uuid.UUID(user_id),
        email="superadmin@example.com",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_main"]
    )
    monkeypatch.setattr(UserModel, "get_by_id", AsyncMock(return_value=dummy_admin))
    monkeypatch.setattr(LeadService, "delete_lead", AsyncMock(return_value=True))

    lead_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/leads/{lead_id}", headers=headers)
    assert response.status_code == 204
    assert response.text == ""


def test_delete_user_status_204(client, superadmin_headers, monkeypatch):
    """Verify DELETE /api/v1/users/{id} returns 204 No Content (Concept #4)."""
    headers, user_id, org_id = superadmin_headers

    from app.models.user import UserModel
    from app.services.user import UserService

    dummy_admin = User(
        id=uuid.UUID(user_id),
        email="superadmin@example.com",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_main"]
    )
    monkeypatch.setattr(UserModel, "get_by_id", AsyncMock(return_value=dummy_admin))
    monkeypatch.setattr(UserService, "deactivate_user", AsyncMock(return_value=True))

    target_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/users/{target_id}", headers=headers)
    assert response.status_code == 204
    assert response.text == ""


def test_delete_appointment_status_204(client, superadmin_headers, monkeypatch):
    """Verify DELETE /api/v1/appointments/{id} returns 204 No Content (Concept #4)."""
    headers, user_id, org_id = superadmin_headers

    from app.models.user import UserModel
    from app.services.appointment import AppointmentService

    dummy_admin = User(
        id=uuid.UUID(user_id),
        email="superadmin@example.com",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_main"]
    )
    monkeypatch.setattr(UserModel, "get_by_id", AsyncMock(return_value=dummy_admin))
    monkeypatch.setattr(AppointmentService, "cancel_appointment", AsyncMock(return_value=True))

    apt_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/appointments/{apt_id}", headers=headers)
    assert response.status_code == 204
    assert response.text == ""


def test_assign_lead_action_success_response(client, superadmin_headers, monkeypatch):
    """Verify POST /api/v1/leads/{id}/assign returns typed ActionSuccessResponse (Concept #3)."""
    headers, user_id, org_id = superadmin_headers

    from app.models.user import UserModel
    from app.services.lead import LeadService
    from app.schemas.lead import Lead, LeadStatus, LeadSource

    dummy_admin = User(
        id=uuid.UUID(user_id),
        email="superadmin@example.com",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        organization_id=uuid.UUID(org_id),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_main"]
    )
    monkeypatch.setattr(UserModel, "get_by_id", AsyncMock(return_value=dummy_admin))

    lead_id = str(uuid.uuid4())
    assigned_lead = Lead(
        id=lead_id,
        organization_id=org_id,
        clinic_id="clinic_main",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1234567890",
        status=LeadStatus.NEW,
        source=LeadSource.WEBSITE,
        assigned_to=user_id,
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    monkeypatch.setattr(LeadService, "assign_lead", AsyncMock(return_value=assigned_lead))

    response = client.post(
        f"/api/v1/leads/{lead_id}/assign?user_id={user_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "successfully assigned" in data["message"]
    assert data["data"]["assigned_to"] == user_id


@pytest.mark.asyncio
async def test_async_runner_non_blocking():
    """Verify async_runner.execute_query executes queries asynchronously."""
    mock_query = MagicMock()
    mock_query.execute.return_value = "query_result"

    result = await execute_query(mock_query)
    assert result == "query_result"
    mock_query.execute.assert_called_once()


def test_google_oauth_url(client):
    """Verify GET /api/v1/auth/oauth/google/url returns valid authorization URL (Concept #9)."""
    response = client.get("/api/v1/auth/oauth/google/url")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "accounts.google.com" in data["auth_url"]
    assert "client_id" in data


def test_google_oauth_login_flow(client, monkeypatch):
    """Verify POST /api/v1/auth/oauth/google authenticates user and returns tokens (Concept #9)."""
    from app.models.user import UserModel
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    dummy_user = User(
        id=user_id,
        email="doctor@example.com",
        full_name="Dr. Google User",
        role=UserRole.AGENT,
        is_active=True,
        organization_id=org_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        assigned_clinics=["clinic_1"]
    )
    monkeypatch.setattr(UserModel, "get_by_email", AsyncMock(return_value=dummy_user))

    response = client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "mock_google_doctor@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "doctor@example.com"
