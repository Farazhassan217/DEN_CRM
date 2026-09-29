from typing import Optional, List, Dict, Any
from ..core.supabase_client import get_admin_client
from ..schemas.audit import AuditLog, AuditAction


class AuditModel:
    """Model for audit log operations with Supabase"""
    
    TABLE_NAME = "audit_logs"
    
    @staticmethod
    async def create(
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        user_id: str,
        user_email: str,
        user_role: str,
        description: str,
        organization_id: Optional[str] = None,
        clinic_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry"""
        supabase = get_admin_client()
        
        data = {
            "action": action.value,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "description": description,
            "organization_id": organization_id,
            "clinic_id": clinic_id,
            "changes": changes,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        response = supabase.table(AuditModel.TABLE_NAME).insert(data).execute()
        return AuditLog(**response.data[0])
    
    @staticmethod
    async def get_by_entity(entity_type: str, entity_id: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific entity"""
        supabase = get_admin_client()
        
        response = supabase.table(AuditModel.TABLE_NAME)\
            .select("*")\
            .eq("entity_type", entity_type)\
            .eq("entity_id", entity_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [AuditLog(**log) for log in response.data]
    
    @staticmethod
    async def get_by_user(user_id: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        supabase = get_admin_client()
        
        response = supabase.table(AuditModel.TABLE_NAME)\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [AuditLog(**log) for log in response.data]
    
    @staticmethod
    async def get_by_organization(
        org_id: str, 
        limit: int = 100, 
        clinic_id: Optional[str] = None
    ) -> List[AuditLog]:
        """Get audit logs for an organization with optional clinic filtering"""
        supabase = get_admin_client()
        
        query = (
            supabase.table(AuditModel.TABLE_NAME)
            .select("*")
            .eq("organization_id", org_id)
        )
        
        # Agar clinic_id provide kiya gaya hai toh query ko refine kar dein
        if clinic_id:
            query = query.eq("clinic_id", clinic_id)
            
        response = (
            query.order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [AuditLog(**log) for log in response.data]
    
    @staticmethod
    async def get_by_action(action: AuditAction, limit: int = 100) -> List[AuditLog]:
        """Get audit logs by action type"""
        supabase = get_admin_client()
        
        response = supabase.table(AuditModel.TABLE_NAME)\
            .select("*")\
            .eq("action", action.value)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [AuditLog(**log) for log in response.data]
    
    @staticmethod
    async def get_security_logs(limit: int = 100) -> List[AuditLog]:
        """Get security-related audit logs"""
        supabase = get_admin_client()
        
        security_actions = [
            AuditAction.PERMISSION_CHANGE.value,
            AuditAction.ROLE_CHANGE.value,
            AuditAction.USER_LOGIN.value,
            AuditAction.USER_DEACTIVATE.value
        ]
        
        response = supabase.table(AuditModel.TABLE_NAME)\
            .select("*")\
            .in_("action", security_actions)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [AuditLog(**log) for log in response.data]
