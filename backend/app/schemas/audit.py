from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
    # User Actions
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_DEACTIVATE = "user.deactivate"
    
    # Organization Actions
    ORG_CREATE = "org.create"
    ORG_UPDATE = "org.update"
    ORG_DELETE = "org.delete"
    
    # Clinic Actions
    CLINIC_CREATE = "clinic.create"
    CLINIC_UPDATE = "clinic.update"
    CLINIC_DELETE = "clinic.delete"
    
    # Lead Actions
    LEAD_CREATE = "lead.create"
    LEAD_UPDATE = "lead.update"
    LEAD_DELETE = "lead.delete"
    LEAD_ASSIGN = "lead.assign"
    LEAD_STATUS_CHANGE = "lead.status_change"
    
    # Appointment Actions
    APPOINTMENT_CREATE = "appointment.create"
    APPOINTMENT_UPDATE = "appointment.update"
    APPOINTMENT_CANCEL = "appointment.cancel"
    APPOINTMENT_CHECKIN = "appointment.checkin"
    APPOINTMENT_COMPLETE = "appointment.complete"
    
    # Revenue Actions
    REVENUE_CREATE = "revenue.create"
    REVENUE_UPDATE = "revenue.update"
    PAYMENT_RECEIVED = "payment.received"
    REFUND_PROCESSED = "refund.processed"
    
    # Call Actions
    CALL_LOG = "call.log"
    
    # Note Actions
    NOTE_CREATE = "note.create"
    NOTE_UPDATE = "note.update"
    NOTE_DELETE = "note.delete"
    
    # Task Actions
    TASK_CREATE = "task.create"
    TASK_UPDATE = "task.update"
    TASK_COMPLETE = "task.complete"
    
    # Security Actions
    PERMISSION_CHANGE = "security.permission_change"
    ROLE_CHANGE = "security.role_change"
    SETTINGS_CHANGE = "settings.change"
    
    # System Actions
    DATA_EXPORT = "system.data_export"
    INTEGRATION_CHANGE = "system.integration_change"


class AuditLogBase(BaseModel):
    action: AuditAction
    entity_type: str  # user, organization, clinic, lead, appointment, revenue, etc.
    entity_id: str
    description: str
    changes: Optional[Dict[str, Any]] = None  # Before/after values
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLog(AuditLogBase):
    id: str
    user_id: str
    user_email: str
    user_role: str
    organization_id: Optional[str] = None
    clinic_id: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
