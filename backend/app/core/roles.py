from enum import Enum
from typing import Dict, List, Set


class UserRole(str, Enum):
    """User roles in the Dental CRM system"""
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    CLINIC_MANAGER = "clinic_manager"
    AGENT = "agent"
    RECEPTION = "reception"
    FINANCE = "finance"


class Permission(str, Enum):
    """All available permissions in the system"""
    # Organization Permissions
    ORG_VIEW = "org:view"
    ORG_MANAGE = "org:manage"
    ORG_CREATE = "org:create"
    ORG_DELETE = "org:delete"
    
    # Clinic Permissions
    CLINIC_VIEW = "clinic:view"
    CLINIC_MANAGE = "clinic:manage"
    CLINIC_CREATE = "clinic:create"
    CLINIC_DELETE = "clinic:delete"
    
    # Lead Permissions
    LEAD_VIEW = "lead:view"
    LEAD_MANAGE = "lead:manage"
    LEAD_CREATE = "lead:create"
    LEAD_DELETE = "lead:delete"
    LEAD_ASSIGN = "lead:assign"
    
    # Appointment Permissions
    APPOINTMENT_VIEW = "appointment:view"
    APPOINTMENT_MANAGE = "appointment:manage"
    APPOINTMENT_CREATE = "appointment:create"
    APPOINTMENT_CANCEL = "appointment:cancel"
    APPOINTMENT_CHECKIN = "appointment:checkin"
    
    # Revenue Permissions
    REVENUE_VIEW = "revenue:view"
    REVENUE_MANAGE = "revenue:manage"
    REVENUE_CREATE = "revenue:create"
    PAYMENT_PROCESS = "payment:process"
    REFUND_PROCESS = "refund:process"
    
    # User Permissions
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"
    USER_CREATE = "user:create"
    USER_DELETE = "user:delete"
    ROLE_ASSIGN = "role:assign"
    
    # Report Permissions
    REPORT_VIEW = "report:view"
    REPORT_SYSTEM = "report:system"
    REPORT_ORG = "report:org"
    REPORT_CLINIC = "report:clinic"
    REPORT_PERSONAL = "report:personal"
    REPORT_FINANCE = "report:finance"
    
    # Task Permissions
    TASK_VIEW = "task:view"
    TASK_MANAGE = "task:manage"
    TASK_CREATE = "task:create"
    
    # Call Permissions
    CALL_LOG = "call:log"
    CALL_VIEW = "call:view"
    
    # Note Permissions
    NOTE_CREATE = "note:create"
    NOTE_VIEW = "note:view"
    
    # Settings Permissions
    SETTINGS_SYSTEM = "settings:system"
    SETTINGS_ORG = "settings:org"
    SETTINGS_CLINIC = "settings:clinic"
    
    # Audit & Security
    AUDIT_VIEW = "audit:view"
    SECURITY_MANAGE = "security:manage"


# Role to Permissions Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions
    
    UserRole.ORG_ADMIN: {
        # Organization
        Permission.ORG_VIEW, Permission.ORG_MANAGE,
        # Clinic
        Permission.CLINIC_VIEW, Permission.CLINIC_MANAGE, 
        Permission.CLINIC_CREATE, Permission.CLINIC_DELETE,
        # Lead
        Permission.LEAD_VIEW, Permission.LEAD_MANAGE,
        Permission.LEAD_CREATE, Permission.LEAD_DELETE,
        Permission.LEAD_ASSIGN,
        # Appointment
        Permission.APPOINTMENT_VIEW, Permission.APPOINTMENT_MANAGE,
        Permission.APPOINTMENT_CREATE, Permission.APPOINTMENT_CANCEL,
        # Revenue
        Permission.REVENUE_VIEW, Permission.REVENUE_MANAGE,
        # User
        Permission.USER_VIEW, Permission.USER_MANAGE,
        Permission.USER_CREATE, Permission.USER_DELETE,
        Permission.ROLE_ASSIGN,
        # Reports
        Permission.REPORT_VIEW, Permission.REPORT_ORG,
        # Tasks
        Permission.TASK_VIEW, Permission.TASK_MANAGE,
        # Settings
        Permission.SETTINGS_ORG,
    },
    
    UserRole.CLINIC_MANAGER: {
        # Clinic (assigned only)
        Permission.CLINIC_VIEW, Permission.CLINIC_MANAGE,
        # Lead (assigned clinic only)
        Permission.LEAD_VIEW, Permission.LEAD_MANAGE,
        Permission.LEAD_CREATE, Permission.LEAD_ASSIGN,
        # Appointment (assigned clinic only)
        Permission.APPOINTMENT_VIEW, Permission.APPOINTMENT_MANAGE,
        Permission.APPOINTMENT_CREATE, Permission.APPOINTMENT_CANCEL,
        # Revenue (own clinic only)
        Permission.REVENUE_VIEW, Permission.REVENUE_MANAGE,
        # User (clinic team view only)
        Permission.USER_VIEW,
        # Reports (clinic specific)
        Permission.REPORT_VIEW, Permission.REPORT_CLINIC,
        # Tasks (all tasks for assigned clinic)
        Permission.TASK_VIEW, Permission.TASK_MANAGE, Permission.TASK_CREATE,
        # Settings (limited)
        Permission.SETTINGS_CLINIC,
    },
    
    UserRole.AGENT: {
        # Lead (assigned leads only)
        Permission.LEAD_VIEW, Permission.LEAD_MANAGE,
        # Appointment (assigned leads only)
        Permission.APPOINTMENT_VIEW, Permission.APPOINTMENT_CREATE,
        # Revenue (own commission only)
        Permission.REVENUE_VIEW,
        # Call
        Permission.CALL_LOG, Permission.CALL_VIEW,
        # Task (own tasks)
        Permission.TASK_VIEW, Permission.TASK_CREATE,
        # Note
        Permission.NOTE_CREATE, Permission.NOTE_VIEW,
        # Reports (personal only)
        Permission.REPORT_VIEW, Permission.REPORT_PERSONAL,
    },
    
    UserRole.RECEPTION: {
        # Appointment (full calendar access)
        Permission.APPOINTMENT_VIEW, Permission.APPOINTMENT_MANAGE,
        Permission.APPOINTMENT_CREATE, Permission.APPOINTMENT_CANCEL,
        Permission.APPOINTMENT_CHECKIN,
        # Lead (create + update — reception can register walk-in patients)
        Permission.LEAD_VIEW, Permission.LEAD_CREATE, Permission.LEAD_MANAGE,
        Permission.LEAD_ASSIGN,
        # Clinic (view own organization's clinics)
        Permission.CLINIC_VIEW,
        # Task (schedule related)
        Permission.TASK_VIEW,
        # Reports (schedule only)
        Permission.REPORT_VIEW,
    },
    
    UserRole.FINANCE: {
        # Revenue (full access)
        Permission.REVENUE_VIEW, Permission.REVENUE_MANAGE,
        Permission.REVENUE_CREATE, Permission.PAYMENT_PROCESS,
        Permission.REFUND_PROCESS,
        # Lead (limited - revenue related only)
        Permission.LEAD_VIEW,
        # Appointment (view for reconciliation)
        Permission.APPOINTMENT_VIEW,
        # Reports (finance dashboards)
        Permission.REPORT_VIEW, Permission.REPORT_FINANCE,
        # Settings (limited)
        Permission.SETTINGS_CLINIC,
    },
}


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission"""
    return permission in get_role_permissions(role)


def get_role_hierarchy() -> List[UserRole]:
    """Get roles in order of hierarchy (highest to lowest)"""
    return [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.CLINIC_MANAGER,
        UserRole.AGENT,
        UserRole.RECEPTION,
        UserRole.FINANCE,
    ]
