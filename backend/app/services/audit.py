from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum
from decimal import Decimal
from ..models.audit import AuditModel
from ..schemas.audit import AuditLog, AuditAction


def sanitize_audit_value(v: Any) -> Any:
    """Recursively convert non-JSON-serializable types into primitives."""
    if isinstance(v, UUID):
        return str(v)
    elif isinstance(v, Enum):
        return v.value
    elif isinstance(v, Decimal):
        return float(v)
    elif hasattr(v, "isoformat"):
        return v.isoformat()
    elif isinstance(v, dict):
        return {k: sanitize_audit_value(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [sanitize_audit_value(val) for val in v]
    return v


class AuditService:
    """Audit logging service"""
    
    @staticmethod
    async def log_action(
        action: Any,
        entity_type: str,
        entity_id: Any,
        user_id: Any,
        user_email: str,
        user_role: Any,
        description: str,
        organization_id: Optional[Any] = None,
        clinic_id: Optional[Any] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log an action to the audit trail with safety checks for UUIDs and JSON serialization"""
        try:
            # Safely map action string or Enum to AuditAction enum
            action_str = action.value if hasattr(action, "value") else str(action)
            try:
                audit_action = AuditAction(action_str)
            except ValueError:
                # Fallback action if mapping fails
                audit_action = AuditAction.USER_UPDATE
            
            # Stringify UUIDs / Enums for mandatory fields
            clean_entity_id = str(entity_id) if entity_id is not None else ""
            clean_user_id = str(user_id) if user_id is not None else ""
            clean_user_role = user_role.value if hasattr(user_role, "value") else str(user_role)
            
            # Stringify optional UUIDs
            clean_org_id = str(organization_id) if organization_id is not None else None
            clean_clinic_id = str(clinic_id) if clinic_id is not None else None
            
            # Deep clean changes dict for any nested UUIDs/Decimals/Enums
            clean_changes = sanitize_audit_value(changes) if changes is not None else None
            
            return await AuditModel.create(
                action=audit_action,
                entity_type=entity_type,
                entity_id=clean_entity_id,
                user_id=clean_user_id,
                user_email=user_email,
                user_role=clean_user_role,
                description=description,
                organization_id=clean_org_id,
                clinic_id=clean_clinic_id,
                changes=clean_changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            # Don't let audit logging failures break the main operation
            print(f"Audit logging failed: {e}")
            return None
    
    @staticmethod
    async def get_entity_logs(entity_type: str, entity_id: Any, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific entity"""
        return await AuditModel.get_by_entity(entity_type, str(entity_id), limit)
    
    @staticmethod
    async def get_user_logs(user_id: Any, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        return await AuditModel.get_by_user(str(user_id), limit)
    
    @staticmethod
    async def get_organization_logs(
        org_id: Any, 
        limit: int = 100, 
        clinic_id: Optional[str] = None
    ) -> List[AuditLog]:
        """Get audit logs for an organization, optionally filtered by clinic_id"""
        clean_clinic_id = str(clinic_id) if clinic_id else None
        return await AuditModel.get_by_organization(str(org_id), limit, clean_clinic_id)

    @staticmethod
    async def get_all_organization_logs(limit: int = 100) -> List[AuditLog]:
        """Get audit logs across all organizations (Super Admin)"""
        # Agar AuditModel mein all logs fetch karne ka method mojood hai (jaise get_all ya get_security_logs)
        return await AuditModel.get_security_logs(limit) # Ya agar AuditModel mein koi general get_all method hai toh woh use karein
    
    @staticmethod
    async def get_security_logs(limit: int = 100) -> List[AuditLog]:
        """Get security-related audit logs"""
        return await AuditModel.get_security_logs(limit)