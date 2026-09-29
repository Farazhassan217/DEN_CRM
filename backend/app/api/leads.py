from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional
from uuid import UUID
from ..schemas.lead import Lead, LeadCreate, LeadUpdate, LeadStatus, LeadSource
from ..schemas.user import User
from ..schemas.pagination import PaginatedResponse
from ..schemas.common import ActionSuccessResponse
# Rename the standalone service function import to prevent shadowing the route function name
from ..services.lead import LeadService
import app.services.lead as lead_service_module
from ..services.auth import get_current_user
from ..models.lead import LeadModel

router = APIRouter(prefix="/leads", tags=["Leads"])


def get_user_role_str(user: User) -> str:
    """Helper function to safely extract role string regardless of Enum or str."""
    if hasattr(user.role, "value"):
        return str(user.role.value).lower()
    return str(user.role).lower()

@router.get("/", response_model=PaginatedResponse[Lead])
async def get_leads(
    clinic_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    lead_status: Optional[LeadStatus] = Query(None, alias="status"),
    assigned_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=1000, description="Items per page"),
    offset: Optional[int] = Query(None, ge=0, description="Optional manual offset"),
    current_user: User = Depends(get_current_user)
):
    role_str = get_user_role_str(current_user)

    effective_offset = offset if offset is not None else (page - 1) * limit
    effective_page = (effective_offset // limit) + 1 if offset is not None else page

    # 1. Agent Scope
    if role_str == "agent":
        leads, total = await LeadModel.get_by_assigned_user(
            current_user.id, limit=limit, offset=effective_offset, return_count=True
        )
        return PaginatedResponse.create(items=leads, total=total, page=effective_page, limit=limit)

    # 2. Org Admin Scope (Strict Tenant Isolation)
    if role_str == "org_admin":
        if clinic_id:
            leads, total = await LeadService.get_leads_by_clinic(
                clinic_id, current_user, limit=limit, offset=effective_offset, return_count=True
            )
        else:
            leads, total = await LeadService.get_leads_by_organization(
                current_user.organization_id, current_user, limit=limit, offset=effective_offset, return_count=True
            )
        return PaginatedResponse.create(items=leads, total=total, page=effective_page, limit=limit)

    # 3. Clinic Manager / Reception Scope
    if role_str in ["clinic_manager", "reception"]:
        target_clinic_id = clinic_id or (
            current_user.assigned_clinics[0] if getattr(current_user, "assigned_clinics", None) else None
        )
        if not target_clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clinic manager must have at least one assigned clinic to view leads"
            )
        leads, total = await LeadService.get_leads_by_clinic(
            target_clinic_id, current_user, limit=limit, offset=effective_offset, return_count=True
        )
        return PaginatedResponse.create(items=leads, total=total, page=effective_page, limit=limit)

    # 4. Super Admin or Fallback
    if clinic_id:
        leads, total = await LeadService.get_leads_by_clinic(
            clinic_id, current_user, limit=limit, offset=effective_offset, return_count=True
        )
        return PaginatedResponse.create(items=leads, total=total, page=effective_page, limit=limit)
    
    selected_org = organization_id or current_user.organization_id if role_str == "super_admin" else current_user.organization_id
    leads, total = await LeadService.get_leads_by_organization(
        selected_org,
        current_user,
        limit=limit,
        offset=effective_offset,
        return_count=True
    )
    return PaginatedResponse.create(items=leads, total=total, page=effective_page, limit=limit)


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: UUID, current_user: User = Depends(get_current_user)):
    return await LeadService.get_lead(lead_id, current_user)


@router.post("/", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    current_user: User = Depends(get_current_user)
):
    role_str = get_user_role_str(current_user)

    allowed_roles = ["super_admin", "org_admin", "clinic_manager", "agent", "reception", "finance"]
    if role_str not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create leads."
        )

    if role_str != "super_admin":
        if not lead_data.organization_id:
            lead_data.organization_id = current_user.organization_id
        elif str(lead_data.organization_id) != str(current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot create leads for another organization."
            )

    if role_str in ["agent", "clinic_manager", "reception"] and not lead_data.clinic_id:
        lead_data.clinic_id = current_user.assigned_clinics[0] if current_user.assigned_clinics else None

    for field in ["assigned_to", "clinic_id", "organization_id"]:
        if hasattr(lead_data, field) and getattr(lead_data, field) == "":
            setattr(lead_data, field, None)

    return await LeadService.create_lead(lead_data, current_user)


@router.put("/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    current_user: User = Depends(get_current_user)
):
    for field in ["assigned_to", "clinic_id", "organization_id"]:
        if hasattr(lead_data, field) and getattr(lead_data, field) == "":
            setattr(lead_data, field, None)

    return await LeadService.update_lead(lead_id, lead_data, current_user)


@router.patch("/{lead_id}", response_model=Lead)
async def patch_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    current_user: User = Depends(get_current_user)
):
    for field in ["assigned_to", "clinic_id", "organization_id"]:
        if hasattr(lead_data, field) and getattr(lead_data, field) == "":
            setattr(lead_data, field, None)

    return await LeadService.update_lead(lead_id, lead_data, current_user)


@router.post("/{lead_id}/assign", response_model=ActionSuccessResponse)
async def assign_lead(
    lead_id: UUID,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    role_str = get_user_role_str(current_user)
    if role_str not in ["super_admin", "org_admin", "clinic_manager", "reception"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to assign leads."
        )
    updated_lead = await LeadService.assign_lead(lead_id, user_id, current_user)
    return ActionSuccessResponse(
        success=True,
        message=f"Lead successfully assigned to user {user_id}",
        data={"lead_id": str(updated_lead.id), "assigned_to": str(user_id)}
    )

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a lead (soft delete) returning 204 No Content
    """
    role_str = get_user_role_str(current_user)
    
    # Super Admin & Org Admin can delete any lead directly (relies on service/mock)
    if role_str in ["super_admin", "org_admin"]:
        await lead_service_module.delete_lead(lead_id, current_user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    # Clinic Manager / Reception need lead existence and clinic validation
    if role_str in ["clinic_manager", "reception"]:
        lead = await LeadModel.get_by_id(lead_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        if lead.clinic_id not in (current_user.assigned_clinics or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete leads from your assigned clinics"
            )
        await lead_service_module.delete_lead(lead_id, current_user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    # Agent and other roles cannot delete leads
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to delete leads."
    )