from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from ..schemas.audit import AuditLog
from ..schemas.user import User
from ..services.audit import AuditService
from ..services.auth import get_current_user
from ..core.roles import UserRole

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


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
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view your own audit logs"
            )
    
    return await AuditService.get_user_logs(user_id, limit)


@router.get("/organization/{org_id}", response_model=List[AuditLog])
async def get_organization_logs(
    org_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs for an organization
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view organization audit logs"
        )
    
    if current_user.role == UserRole.ORG_ADMIN:
        if org_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only view logs for your own organization"
            )
    
    return await AuditService.get_organization_logs(org_id, limit)


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
