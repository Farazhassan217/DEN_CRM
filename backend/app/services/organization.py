from typing import Optional, List
from fastapi import HTTPException, status
from ..core.roles import UserRole, has_permission
from ..schemas.organization import Organization, OrganizationCreate, OrganizationUpdate
from ..schemas.user import User
from ..models.organization import OrganizationModel
from ..services.audit import AuditService


class OrganizationService:
    """Organization management service"""
    
    @staticmethod
    async def create_organization(org_data: OrganizationCreate, created_by: User) -> Organization:
        """Create a new organization (Super Admin only)"""
        
        # Only Super Admin can create organizations
        if created_by.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Super Admin can create organizations"
            )
        
        org = await OrganizationModel.create(org_data)
        
        # Log audit
        await AuditService.log_action(
            action="org.create",
            entity_type="organization",
            entity_id=org.id,
            user_id=created_by.id,
            user_email=created_by.email,
            user_role=created_by.role.value,
            description=f"Created organization: {org.name}"
        )
        
        return org
    
    @staticmethod
    async def get_organization(org_id: str, current_user: User) -> Organization:
        """Get organization by ID with permission checks"""
        
        # Permission check
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view organizations"
            )
        
        org = await OrganizationModel.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Org Admin can only view their own org
        if current_user.role == UserRole.ORG_ADMIN:
            if org_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your own organization"
                )
        
        return org
    
    @staticmethod
    async def update_organization(org_id: str, org_data: OrganizationUpdate, current_user: User) -> Organization:
        """Update organization with permission checks"""
        
        # Permission check
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update organizations"
            )
        
        org = await OrganizationModel.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Org Admin can only update their own org
        if current_user.role == UserRole.ORG_ADMIN:
            if org_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update your own organization"
                )
        
        updated_org = await OrganizationModel.update(org_id, org_data)
        
        # Log audit
        await AuditService.log_action(
            action="org.update",
            entity_type="organization",
            entity_id=org_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role.value,
            description=f"Updated organization: {org.name}",
            changes=org_data.model_dump(exclude_unset=True)
        )
        
        return updated_org
    
    @staticmethod
    async def get_all_organizations(current_user: User, limit: int = 100, offset: int = 0) -> List[Organization]:
        """Get all organizations (Super Admin only)"""
        
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Super Admin can view all organizations"
            )
        
        return await OrganizationModel.get_all(limit, offset)
