from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from ..schemas.organization import Organization, OrganizationCreate, OrganizationUpdate
from ..schemas.user import User
from ..services.organization import OrganizationService
from ..services.auth import get_current_user

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/", response_model=List[Organization])
async def get_organizations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Get organizations
    - Super Admin: All organizations
    - Org Admin: Their own organization
    """
    if current_user.role.value == "super_admin":
        return await OrganizationService.get_all_organizations(current_user, limit, offset)
    else:
        org = await OrganizationService.get_organization(current_user.organization_id, current_user)
        return [org]


@router.get("/{org_id}", response_model=Organization)
async def get_organization(org_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific organization by ID
    """
    return await OrganizationService.get_organization(org_id, current_user)


@router.post("/", response_model=Organization)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new organization (Super Admin only)
    """
    return await OrganizationService.create_organization(org_data, current_user)


@router.put("/{org_id}", response_model=Organization)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update an organization
    """
    return await OrganizationService.update_organization(org_id, org_data, current_user)
