from typing import Optional, List
from fastapi import HTTPException, status
from ..core.roles import UserRole, Permission, has_permission
from ..schemas.lead import Lead, LeadCreate, LeadUpdate, LeadStatus
from ..schemas.user import User
from ..models.lead import LeadModel
from ..services.audit import AuditService


def get_role_str(role) -> str:
    """Helper to safely extract lowercase role string."""
    if hasattr(role, "value"):
        return str(role.value).lower()
    return str(role).lower()


class LeadService:
    """Lead management service with role-based access control"""
    
    @staticmethod
    async def create_lead(lead_data: LeadCreate, current_user: User) -> Lead:
        """Create a new lead with permission checks"""
        
        user_role_str = get_role_str(current_user.role)

        # 1. Permission check (handles both Enum and string)
        if not has_permission(current_user.role, Permission.LEAD_CREATE) and user_role_str not in ["super_admin", "org_admin", "clinic_manager", "agent", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create leads"
            )
        
        # 2. Scope checks
        if user_role_str == "agent":
            # Agent can only create leads in assigned clinics
            if lead_data.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create leads in assigned clinics"
                )
            # Auto-assign to self
            lead_data.assigned_to = current_user.id
        
        elif user_role_str in ["clinic_manager", "reception"]:
            # Clinic Manager / Reception scope
            if lead_data.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create leads in assigned clinics"
                )
        
        elif user_role_str == "org_admin":
            # Auto-fill organization_id if missing
            if not lead_data.organization_id:
                lead_data.organization_id = current_user.organization_id
            # Safe String Comparison for Tenant Security
            elif str(lead_data.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create leads in your organization"
                )

        # Sanitize empty string fields
        if hasattr(lead_data, "assigned_to") and lead_data.assigned_to == "":
            lead_data.assigned_to = None
        
        lead = await LeadModel.create(lead_data)
        
        # Log audit
        user_role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        await AuditService.log_action(
            action="lead.create",
            entity_type="lead",
            entity_id=lead.id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=user_role_val,
            description=f"Created lead: {lead.first_name} {lead.last_name}",
            organization_id=lead.organization_id,
            clinic_id=lead.clinic_id
        )
        
        return lead
    
    @staticmethod
    async def get_lead(lead_id: str, current_user: User) -> Lead:
        """Get lead by ID with permission checks"""
        
        lead = await LeadModel.get_by_id(lead_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        user_role_str = get_role_str(current_user.role)

        # Super Admin
        if user_role_str == "super_admin":
            return lead
        
        # Org Admin
        if user_role_str == "org_admin":
            if str(lead.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view leads in your organization"
                )
            return lead
        
        # Clinic Manager / Reception
        if user_role_str in ["clinic_manager", "reception"]:
            if lead.clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view leads in assigned clinics"
                )
            return lead
        
        # Agent
        if user_role_str == "agent":
            if str(lead.assigned_to) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view leads assigned to you"
                )
            return lead
        
        # Finance
        if user_role_str == "finance":
            return lead
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view leads"
        )
    
    @staticmethod
    async def update_lead(lead_id: str, lead_data: LeadUpdate, current_user: User) -> Lead:
        """Update lead with permission checks"""
        
        lead = await LeadModel.get_by_id(lead_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Access check
        await LeadService.get_lead(lead_id, current_user)
        
        user_role_str = get_role_str(current_user.role)
        
        if user_role_str == "agent":
            if str(lead.assigned_to) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update leads assigned to you"
                )
            if lead_data.status == LeadStatus.WON:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Agents cannot mark leads as won. Manager approval required."
                )
        
        if hasattr(lead_data, "assigned_to") and lead_data.assigned_to == "":
            lead_data.assigned_to = None

        updated_lead = await LeadModel.update(lead_id, lead_data)
        
        user_role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        await AuditService.log_action(
            action="lead.update",
            entity_type="lead",
            entity_id=lead_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=user_role_val,
            description=f"Updated lead: {lead.first_name} {lead.last_name}",
            clinic_id=lead.clinic_id,
            changes=lead_data.model_dump(exclude_unset=True)
        )
        
        return updated_lead
    
    @staticmethod
    async def assign_lead(lead_id: str, user_id: str, current_user: User) -> Lead:
        """Assign a lead to a user"""
        
        lead = await LeadModel.get_by_id(lead_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        user_role_str = get_role_str(current_user.role)
        if user_role_str not in ["super_admin", "org_admin", "clinic_manager", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to assign leads"
            )
        
        lead_data = LeadUpdate(assigned_to=user_id)
        updated_lead = await LeadModel.update(lead_id, lead_data)
        
        user_role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        await AuditService.log_action(
            action="lead.assign",
            entity_type="lead",
            entity_id=lead_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=user_role_val,
            description=f"Assigned lead to user: {user_id}",
            clinic_id=lead.clinic_id,
            changes={"assigned_to": user_id}
        )
        
        return updated_lead
    
    @staticmethod
    async def get_leads_by_clinic(
        clinic_id: str,
        current_user: User,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ):
        """Get leads for a clinic with count support"""
        user_role_str = get_role_str(current_user.role)
        
        if user_role_str in ["super_admin", "org_admin"]:
            return await LeadModel.get_by_clinic(clinic_id, limit, offset, return_count=return_count)
        
        if user_role_str in ["clinic_manager", "reception"]:
            if clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view leads in assigned clinics"
                )
            return await LeadModel.get_by_clinic(clinic_id, limit, offset, return_count=return_count)
        
        if user_role_str == "agent":
            return await LeadModel.get_by_assigned_user(current_user.id, limit, offset, return_count=return_count)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view leads"
        )
    
    @staticmethod
    async def get_leads_by_organization(
        org_id: str,
        current_user: User,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ):
        """Get leads for an organization with count support"""
        user_role_str = get_role_str(current_user.role)
        
        if user_role_str not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view organization leads"
            )
        
        if user_role_str == "org_admin":
            if str(org_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view leads in your organization"
                )
        
        return await LeadModel.get_by_organization(org_id, limit, offset, return_count=return_count)

    @staticmethod
    async def delete_lead(lead_id: str, current_user: User) -> bool:
        """Soft delete lead with tenant authorization checks and audit logging"""
        lead = await LeadModel.get_by_id(lead_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        user_role_str = get_role_str(current_user.role)
        if user_role_str not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete lead"
            )
        
        if user_role_str == "org_admin":
            if str(lead.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete lead from another organization"
                )

        result = await LeadModel.delete(lead_id)
        
        user_role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        await AuditService.log_action(
            action="lead.delete",
            entity_type="lead",
            entity_id=lead_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=user_role_val,
            description=f"Soft deleted lead: {lead.first_name} {lead.last_name}",
            organization_id=lead.organization_id,
            clinic_id=lead.clinic_id
        )
        return result