import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from ..schemas.audit import AuditLog
from ..schemas.user import User
from ..services.audit import AuditService
from ..services.auth import get_current_user
from ..core.roles import UserRole

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/security", response_model=List[AuditLog])
async def get_security_logs(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    Get security-related audit logs (Super Admin only)
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can view security logs"
        )
    
    return await AuditService.get_security_logs(limit)


# NOTE: Static route MUST be placed BEFORE the dynamic "/organization/{org_id}" route
@router.get("/organization/all", response_model=List[AuditLog])
async def get_all_or_org_logs(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    - Super Admin: Returns audit logs across all organizations.
    - Org Admin: Automatically scoped/redirected to their own organization's logs using organization_id.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return await AuditService.get_all_organization_logs(limit)
    
    elif current_user.role == UserRole.ORG_ADMIN:
        if not current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID is missing for this Org Admin account."
            )
        return await AuditService.get_organization_logs(str(current_user.organization_id), limit)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions to view organization audit logs"
    )


@router.get("/organization/{org_id}", response_model=List[AuditLog])
async def get_organization_logs(
    org_id: str,
    clinic_id: Optional[str] = Query(None, description="Optional clinic ID to filter audit logs"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs for a specific organization with optional clinic filtering
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view organization audit logs"
        )
    
    if current_user.role == UserRole.ORG_ADMIN:
        try:
            # Safe UUID comparison to prevent string vs UUID type mismatch 403 errors
            if uuid.UUID(str(org_id)) != uuid.UUID(str(current_user.organization_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view logs for your own organization"
                )
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid organization ID format: '{org_id}'"
            )
            
    # Validate clinic_id format if provided by the client
    if clinic_id:
        try:
            uuid.UUID(str(clinic_id))
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid clinic ID format: '{clinic_id}'"
            )
    
    return await AuditService.get_organization_logs(org_id, limit, clinic_id)


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLog])
async def get_entity_logs(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs for a specific entity
    - Super Admin: All entity logs
    - Org Admin: Logs for entities in their org
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view audit logs"
        )
    
    return await AuditService.get_entity_logs(entity_type, entity_id, limit)


@router.get("/user/{user_id}", response_model=List[AuditLog])
async def get_user_logs(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs for a specific user
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
        if user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view your own audit logs"
            )
    
    return await AuditService.get_user_logs(user_id, limit)