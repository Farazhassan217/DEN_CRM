from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional
from ..schemas.user import User, UserCreate, UserUpdate
from ..schemas.pagination import PaginatedResponse
from ..services.user import UserService
from ..services.clinic import ClinicService
from ..services.auth import get_current_user
from ..core.roles import UserRole

router = APIRouter(prefix="/users", tags=["Users"])

# Doctor and Clinic Manager along with staff can be created by Org Admin
ALLOWED_ORG_ADMIN_ROLES = ["clinic_manager", "doctor", "reception", "agent", "finance"]

# Added 'doctor' so Clinic Managers can manage clinic medical staff
ALLOWED_CLINIC_MANAGER_ROLES = ["doctor", "reception", "agent", "finance"]


def get_role_value(role) -> str:
    """Safely convert Enum or String role to lowercase string."""
    if hasattr(role, "value"):
        return str(role.value).lower()
    return str(role).lower()


@router.get("/", response_model=PaginatedResponse[User])
async def get_users(
    organization_id: Optional[str] = Query(None),
    clinic_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=1000, description="Items per page"),
    offset: Optional[int] = Query(None, ge=0, description="Optional manual offset"),
    include_deactivated: bool = Query(False, description="Administrative mechanism to include deactivated users"),
    current_user: User = Depends(get_current_user)
):
    role_str = get_role_value(current_user.role)

    if include_deactivated and role_str not in ["super_admin", "org_admin", "clinic_manager", "agent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view deactivated users."
        )

    effective_offset = offset if offset is not None else (page - 1) * limit
    effective_page = (effective_offset // limit) + 1 if offset is not None else page

    # Explicit handling based on passed query params or user roles
    if clinic_id:
        users, total = await UserService.get_users_by_clinic(
            clinic_id, current_user, include_deactivated=include_deactivated, limit=limit, offset=effective_offset, return_count=True
        )
    elif organization_id:
        users, total = await UserService.get_users_by_organization(
            organization_id, current_user, limit=limit, offset=effective_offset, include_deactivated=include_deactivated, return_count=True
        )
    else:
        # Fallback hierarchy when no specific query params are provided
        if role_str == "super_admin":
            users, total = await UserService.get_all_users(
                limit=limit, offset=effective_offset, include_deactivated=include_deactivated, return_count=True
            )
        elif role_str == "org_admin" and current_user.organization_id:
            users, total = await UserService.get_users_by_organization(
                current_user.organization_id, 
                current_user, 
                limit=limit, 
                offset=effective_offset,
                include_deactivated=include_deactivated,
                return_count=True
            )
        elif role_str == "clinic_manager" and current_user.assigned_clinics:
            # FIX: Fallback to the Clinic Manager's primary assigned clinic
            primary_clinic_id = current_user.assigned_clinics[0]
            users, total = await UserService.get_users_by_clinic(
                primary_clinic_id,
                current_user,
                include_deactivated=include_deactivated,
                limit=limit,
                offset=effective_offset,
                return_count=True
            )
        else:
            users = [current_user]
            total = 1

    return PaginatedResponse.create(items=users, total=total, page=effective_page, limit=limit)


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    return await UserService.get_user(user_id, current_user)


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    current_role = get_role_value(current_user.role)
    target_role = get_role_value(user_data.role)
    target_org_id = user_data.organization_id

    # Block operational staff roles from creating any user
    if current_role in ["finance", "agent", "reception", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Staff members do not have permission to create users."
        )

    # Prevent non-Super Admins from creating administrative accounts
    if target_role in ["super_admin", "org_admin"] and current_role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can create Org Admins or Super Admins."
        )

    if current_role == "super_admin":
        pass  # Unrestricted creation rights

    elif current_role == "org_admin":
        if not target_org_id or str(target_org_id) != str(current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create users for your own organization."
            )
        
        if target_role not in ALLOWED_ORG_ADMIN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Org Admin can only create: {', '.join(ALLOWED_ORG_ADMIN_ROLES)}"
            )

    elif current_role == "clinic_manager":
        # Automatically bind new user to manager's org if missing
        if not target_org_id:
            user_data.organization_id = current_user.organization_id
            target_org_id = current_user.organization_id

        if str(target_org_id) != str(current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create users for your own organization."
            )
        
        if target_role not in ALLOWED_CLINIC_MANAGER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Clinic Manager can only create: {', '.join(ALLOWED_CLINIC_MANAGER_ROLES)}"
            )
        
        # FIX: Auto-populate assigned_clinics if frontend omits it
        if not user_data.assigned_clinics:
            user_data.assigned_clinics = current_user.assigned_clinics or []

        if not user_data.assigned_clinics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinic Manager must assign the new user to at least one clinic."
            )

        for c_id in user_data.assigned_clinics:
            if c_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You can only assign users to your own clinics. Clinic '{c_id}' is not assigned to you."
                )

    # Verify that specified clinics exist and match the target organization
    if user_data.assigned_clinics:
        for clinic_id in user_data.assigned_clinics:
            try:
                clinic = await ClinicService.get_clinic(clinic_id, current_user)
            except HTTPException:
                clinic = None

            if not clinic:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Clinic ID '{clinic_id}' does not exist or is not accessible."
                )
            
            if target_org_id and str(clinic.organization_id) != str(target_org_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Clinic '{clinic_id}' does not belong to organization '{target_org_id}'."
                )

    return await UserService.create_user(user_data, current_user)


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    current_role = get_role_value(current_user.role)
    
    if current_role in ["finance", "agent", "reception", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Staff members do not have permission to update users."
        )

    return await UserService.update_user(user_id, user_data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    current_role = get_role_value(current_user.role)
    
    if current_role in ["finance", "agent", "reception", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Staff members do not have permission to deactivate users."
        )

    await UserService.deactivate_user(user_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)