from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..schemas.clinic import Clinic, ClinicCreate, ClinicUpdate
from ..schemas.user import User
from ..services.clinic import ClinicService
from ..services.auth import get_current_user
from ..core.cache import CacheManager

router = APIRouter(prefix="/clinics", tags=["Clinics"])


@router.get("/", response_model=List[Clinic])
async def get_clinics(
    organization_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Get clinics based on permissions
    - Super Admin: All clinics
    - Org Admin: All clinics in their organization
    - Clinic Manager: Assigned clinics
    - Others: Assigned clinic
    """
    if organization_id:
        return await ClinicService.get_clinics_by_organization(organization_id, current_user)
    elif current_user.role.value in ["clinic_manager", "agent", "reception", "finance"]:
        return await ClinicService.get_assigned_clinics(current_user)
    else:
        # Super Admin or Org Admin
        return await ClinicService.get_clinics_by_organization(
            organization_id or current_user.organization_id, 
            current_user
        )


@router.get("/{clinic_id}", response_model=Clinic)
async def get_clinic(clinic_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific clinic by ID with 5-minute Redis caching.
    """
    cached = CacheManager.get("clinics", clinic_id)
    if cached is not None:
        return cached

    clinic = await ClinicService.get_clinic(clinic_id, current_user)
    serializable = clinic.model_dump(mode="json") if hasattr(clinic, "model_dump") else clinic
    CacheManager.set("clinics", clinic_id, serializable, ttl=300)
    return clinic


@router.post("/", response_model=Clinic)
async def create_clinic(
    clinic_data: ClinicCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new clinic
    - Super Admin: Can create in any organization
    - Org Admin: Can create in their organization
    """
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
    result = await ClinicService.update_clinic(clinic_id, clinic_data, current_user)
    CacheManager.invalidate("clinics", clinic_id)
    return result
