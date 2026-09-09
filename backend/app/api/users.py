from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional
from ..schemas.user import User, UserCreate, UserUpdate
from ..schemas.pagination import PaginatedResponse
from ..services.user import UserService
from ..services.clinic import ClinicService
from ..services.auth import get_current_user
from ..core.roles import UserRole

router = APIRouter(prefix="/users", tags=["Users"])

# Roles that Org Admin is allowed to create according to RBAC docs
ALLOWED_ORG_ADMIN_ROLES = ["clinic_manager", "reception", "agent", "finance"]
# Roles that Clinic Manager is allowed to create within their assigned clinics
ALLOWED_CLINIC_MANAGER_ROLES = ["reception", "agent", "finance"]


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
    """
    Get users with standardized pagination and permission checks:
    - Super Admin: All users
    - Org Admin: Users in their organization
    - Clinic Manager: Users in assigned clinics
    - Others: Only self
    Soft-deleted users are excluded by default unless include_deactivated=True is requested by an admin.
    """
    role_str = get_role_value(current_user.role)

    # Only admins can explicitly request deactivated users
    if include_deactivated and role_str not in ["super_admin", "org_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view deactivated users."
        )

    effective_offset = offset if offset is not None else (page - 1) * limit
    effective_page = (effective_offset // limit) + 1 if offset is not None else page

    if clinic_id:
        users, total = await UserService.get_users_by_clinic(
            clinic_id, current_user, include_deactivated=include_deactivated, limit=limit, offset=effective_offset, return_count=True
        )
    elif organization_id:
        users, total = await UserService.get_users_by_organization(
            organization_id, current_user, limit=limit, offset=effective_offset, include_deactivated=include_deactivated, return_count=True
        )
    else:
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
    """
    Create a new user with strict role restrictions.
    Finance, Agent, and Reception users are strictly restricted from creating users.
    """
    current_role = get_role_value(current_user.role)

    # ==================================================================
    # EXPLICIT BLOCK: Finance, Agent, and Reception cannot create users
    # ==================================================================
    if current_role in ["finance", "agent", "reception"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Finance, Agent, and Reception users do not have permission to create users."
        )

    target_role = get_role_value(user_data.role)
    target_org_id = user_data.organization_id

    # ------------------------------------------------------------------
    # CHECK 1: Role Authorization & Multi-Tenant Boundary
    # ------------------------------------------------------------------
    if current_role == "super_admin":
        pass  # Unrestricted
    elif current_role == "org_admin":
        # Multi-Tenant Check
        if not target_org_id or str(target_org_id) != str(current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to create users for another organization."
            )
        
        # Privilege Escalation Protection
        if target_role not in ALLOWED_ORG_ADMIN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Org Admin can only create: {', '.join(ALLOWED_ORG_ADMIN_ROLES)}"
            )
    elif current_role == "clinic_manager":
        # Clinic Manager Multi-Tenant Check
        if not target_org_id or str(target_org_id) != str(current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to create users for another organization."
            )
        
        # Privilege Escalation Protection for Clinic Manager
        if target_role not in ALLOWED_CLINIC_MANAGER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Clinic Manager can only create: {', '.join(ALLOWED_CLINIC_MANAGER_ROLES)}"
            )
        
        # Ensure the user being created is assigned to clinics the manager has access to
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
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create users."
        )

    # ------------------------------------------------------------------
    # CHECK 2: Assigned Clinics Ownership Validation
    # ------------------------------------------------------------------
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
            
            if str(clinic.organization_id) != str(target_org_id):
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
    """
    Update user profile. Finance, Agent, and Reception users are strictly restricted from managing users.
    """
    current_role = get_role_value(current_user.role)
    
    # ==================================================================
    # EXPLICIT BLOCK: Finance, Agent, and Reception cannot update users
    # ==================================================================
    if current_role in ["finance", "agent", "reception"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Finance, Agent, and Reception users do not have permission to update or manage users."
        )

    return await UserService.update_user(user_id, user_data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate user returning 204 No Content (Concept #4).
    Finance, Agent, and Reception users are strictly restricted from managing users.
    """
    current_role = get_role_value(current_user.role)
    
    # ==================================================================
    # EXPLICIT BLOCK: Finance, Agent, and Reception cannot deactivate users
    # ==================================================================
    if current_role in ["finance", "agent", "reception"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Finance, Agent, and Reception users do not have permission to deactivate or manage users."
        )

    await UserService.deactivate_user(user_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)