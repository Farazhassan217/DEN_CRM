import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..schemas.clinic import Clinic, ClinicCreate, ClinicUpdate
from ..schemas.user import User
from ..services.clinic import ClinicService
from ..services.auth import get_current_user
from ..core.cache import CacheManager

router = APIRouter(prefix="/clinics", tags=["Clinics"])


def is_valid_uuid(val: Optional[str]) -> bool:
    """Validate if string is a valid UUID and not None/empty/'None'."""
    if not val or str(val).strip().lower() == "none":
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


@router.get("/", response_model=List[Clinic])
async def get_clinics(
    organization_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get clinics based on permissions:
    - Super Admin: All clinics (or filtered by org_id if valid)
    - Org Admin / Reception: All clinics in their organization
    - Clinic Manager, Agent, Finance: Assigned clinics
    """
    role_str = current_user.role.value.lower() if hasattr(current_user.role, "value") else str(current_user.role).lower()

    # 1. Handle Explicit organization_id Query Parameter
    if organization_id:
        if not is_valid_uuid(organization_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format for organization_id: '{organization_id}'"
            )
        return await ClinicService.get_clinics_by_organization(organization_id, current_user)

    # 2. Super Admin without org_id gets all clinics
    if role_str == "super_admin":
        if hasattr(ClinicService, "get_all_clinics"):
            return await ClinicService.get_all_clinics(current_user)
        return []

    # 3. Roles scoped to user's Organization (Reception, Org Admin)
    if role_str in ["reception", "org_admin"]:
        user_org_id = getattr(current_user, "organization_id", None)
        
        # Guard: If user has no assigned organization, return empty list instead of DB Crash
        if not is_valid_uuid(user_org_id):
            return []

        return await ClinicService.get_clinics_by_organization(str(user_org_id), current_user)

    # 4. Roles scoped to Assigned Clinics (Clinic Manager, Agent, Finance, Doctor)
    if role_str in ["clinic_manager", "agent", "finance", "doctor"]:
        return await ClinicService.get_assigned_clinics(current_user)

    return []


@router.get("/{clinic_id}", response_model=Clinic)
async def get_clinic(clinic_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific clinic by ID with 5-minute Redis caching.
    """
    if not is_valid_uuid(clinic_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format for clinic_id: '{clinic_id}'"
        )

    cached = CacheManager.get("clinics", clinic_id)
    if cached is not None:
        return cached

    clinic = await ClinicService.get_clinic(clinic_id, current_user)
    serializable = clinic.model_dump(mode="json") if hasattr(clinic, "model_dump") else clinic
    CacheManager.set("clinics", clinic_id, serializable, ttl=300)
    return clinic


@router.post("/", response_model=Clinic, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    clinic_data: ClinicCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new clinic
    - Super Admin: Can create in any organization
    - Org Admin: Can create in their organization
    """
    if clinic_data.organization_id and not is_valid_uuid(str(clinic_data.organization_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format for organization_id: '{clinic_data.organization_id}'"
        )
        
    return await ClinicService.create_clinic(clinic_data, current_user)


@router.put("/{clinic_id}", response_model=Clinic)
async def update_clinic(
    clinic_id: str,
    clinic_data: ClinicUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update a clinic and invalidate cached clinic metadata.
    """
    if not is_valid_uuid(clinic_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format for clinic_id: '{clinic_id}'"
        )

    result = await ClinicService.update_clinic(clinic_id, clinic_data, current_user)
    CacheManager.invalidate("clinics", clinic_id)
    return result