from typing import Optional, List
from fastapi import HTTPException, status
from ..core.roles import UserRole, Permission, has_permission, get_role_permissions
from ..schemas.user import User, UserCreate, UserUpdate
from ..models.user import UserModel
from ..models.audit import AuditModel
from ..services.audit import AuditService
from .auth import get_password_hash


async def count_org_admins_by_organization(organization_id: str) -> int:
    """Count users with OrgAdmin role in a specific organization"""
    result = await UserModel.get_by_organization(
        organization_id, limit=1000, offset=0,
        include_deactivated=False, return_count=True
    )
    
    # Handle both cases: if it returns a tuple (users, total) or just users list
    if isinstance(result, (list, tuple)) and len(result) == 2 and isinstance(result[1], int):
        users = result[0]
    else:
        users = result if isinstance(result, list) else []

    org_admin_count = 0
    for user in users:
        # Safely extract role whether user is a dictionary or an object
        role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
        role_str = str(role.value if hasattr(role, "value") else role).lower()
        
        if role_str == "org_admin":
            org_admin_count += 1
            
    return org_admin_count


def get_role_str(role_obj) -> str:
    if hasattr(role_obj, "value"):
        return str(role_obj.value).lower()
    return str(role_obj).lower()


class UserService:
    """User management service with role-based access control"""

    @staticmethod
    async def create_user(
        user_data: UserCreate,
        created_by: User,
        organization_id: Optional[str] = None
    ) -> User:
        """Create a new user with permission checks"""

        created_role_str = get_role_str(created_by.role)
        target_role_str = get_role_str(user_data.role) if hasattr(user_data, "role") and user_data.role else ""

        if created_role_str in ["finance", "agent", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Finance and operational roles do not have permission to create users."
            )

        if not has_permission(created_by.role, Permission.USER_CREATE):
            if created_role_str not in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to create users"
                )

        existing_user = await UserModel.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        if created_role_str == "org_admin":
            if user_data.organization_id and str(user_data.organization_id) != str(created_by.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create users in your own organization"
                )
            user_data.organization_id = created_by.organization_id
            
            # FIX: Org Admin limit check sirf tab chalni chahiye jab naya banne wala user bhi "org_admin" ho!
            if target_role_str == "org_admin":
                admin_count = await count_org_admins_by_organization(created_by.organization_id)
                if admin_count >= 1:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Organization already has an Org Admin. Only one Org Admin allowed per organization."
                    )

        elif created_role_str == "clinic_manager":
            user_data.organization_id = created_by.organization_id
            if target_role_str in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Clinic Manager cannot create administrators or other managers"
                )
            if user_data.assigned_clinics:
                for c_id in user_data.assigned_clinics:
                    if c_id not in (created_by.assigned_clinics or []):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Can only create users for your assigned clinics"
                        )
            else:
                user_data.assigned_clinics = created_by.assigned_clinics

        hashed_password = get_password_hash(user_data.password)

        user_dict = user_data.model_dump()
        user_dict['password'] = hashed_password

        created_user = await UserModel.create(user_dict)

        try:
            entity_id = str(created_user.id) if hasattr(created_user, 'id') else "created"
            await AuditService.log_action(
                action="user.create",
                entity_type="user",
                entity_id=entity_id,
                user_id=created_by.id,
                user_email=created_by.email,
                user_role=created_role_str,
                description=f"Created new user: {user_data.email}",
                organization_id=str(user_data.organization_id) if user_data.organization_id else None
            )
        except Exception:
            pass  

        return created_user
    @staticmethod
    async def get_user(user_id: str, current_user: User) -> User:
        """Get a user by ID with permission checks"""

        if not has_permission(current_user.role, Permission.USER_VIEW):
            if get_role_str(current_user.role) not in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to view users"
                )

        user = await UserModel.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        role_str = get_role_str(current_user.role)

        if role_str == "org_admin":
            if str(user.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view users in your own organization"
                )

        if role_str == "clinic_manager":
            if not any(clinic_id in (user.assigned_clinics or []) for clinic_id in (current_user.assigned_clinics or [])):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view users in your assigned clinics"
                )

        if role_str in ["agent", "reception", "finance"]:
            if str(user.id) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your own profile"
                )

        return user

    @staticmethod
    async def get_all_users(
        limit: int = 100,
        offset: int = 0,
        include_deactivated: bool = False,
        return_count: bool = False
    ):
        """Get all users across all organizations (Super Admin use case)"""
        return await UserModel.get_all(
            limit, offset, include_deactivated=include_deactivated, return_count=return_count
        )

    @staticmethod
    async def update_user(user_id: str, user_data: UserUpdate, current_user: User) -> User:
        """Update a user with permission checks"""

        role_str = get_role_str(current_user.role)

        if role_str in ["finance", "agent", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Finance users do not have permission to update users."
            )

        if not has_permission(current_user.role, Permission.USER_MANAGE):
            if role_str not in ["super_admin", "org_admin", "clinic_manager"] and str(user_id) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to update users"
                )

        user = await UserModel.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if role_str == "clinic_manager" and str(user_id) != str(current_user.id):
            if not any(clinic_id in (user.assigned_clinics or []) for clinic_id in (current_user.assigned_clinics or [])):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update users in your assigned clinics"
                )
            target_role_str = get_role_str(user.role)
            if target_role_str in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot update administrators or other managers"
                )

        if user_data.role and user_data.role != user.role:
            if role_str not in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to change user roles"
                )

            if role_str == "org_admin":
                target_role_str = get_role_str(user_data.role)
                if target_role_str == "super_admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cannot assign Super Admin role"
                    )
                if target_role_str == "org_admin":
                    org_count = await count_org_admins_by_organization(user.organization_id)
                    if org_count >= 1:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Organization already has an Org Admin. Only one Org Admin allowed per organization."
                        )

            if role_str == "clinic_manager":
                target_role_str = get_role_str(user_data.role)
                if target_role_str not in ["doctor", "reception", "agent", "finance"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Clinic Manager can only assign doctor, reception, agent, or finance roles"
                    )

        updated_user = await UserModel.update(user_id, user_data)

        try:
            await AuditService.log_action(
                action="user.update",
                entity_type="user",
                entity_id=user_id,
                user_id=current_user.id,
                user_email=current_user.email,
                user_role=role_str,
                description=f"Updated user: {user.email}",
                changes=user_data.model_dump(exclude_unset=True)
            )
        except Exception:
            pass

        return updated_user

    @staticmethod
    async def deactivate_user(user_id: str, current_user: User) -> bool:
        """Deactivate a user with permission checks"""

        role_str = get_role_str(current_user.role)

        if role_str in ["finance", "agent", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Finance users do not have permission to deactivate users."
            )

        if not has_permission(current_user.role, Permission.USER_DELETE):
            if role_str not in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to deactivate users"
                )

        user = await UserModel.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        target_user_role = get_role_str(user.role)
        if target_user_role == "super_admin" and role_str != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot deactivate Super Admin users"
            )

        if role_str == "org_admin":
            if str(user.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only deactivate users in your own organization"
                )

        if role_str == "clinic_manager":
            if not any(clinic_id in (user.assigned_clinics or []) for clinic_id in (current_user.assigned_clinics or [])):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only deactivate users in your assigned clinics"
                )
            if target_user_role in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot deactivate administrators or other managers"
                )

        if target_user_role == "org_admin" and role_str == "org_admin":
            org_count = await count_org_admins_by_organization(user.organization_id)
            if org_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot deactivate the last Org Admin in the organization. Assign another user as Org Admin first."
                )

        result = await UserModel.delete(user_id)

        try:
            await AuditService.log_action(
                action="user.deactivate",
                entity_type="user",
                entity_id=user_id,
                user_id=current_user.id,
                user_email=current_user.email,
                user_role=role_str,
                description=f"Deactivated user: {user.email}"
            )
        except Exception:
            pass

        return result

    @staticmethod
    async def get_users_by_organization(
        org_id: str,
        current_user: User,
        limit: int = 100,
        offset: int = 0,
        include_deactivated: bool = False,
        return_count: bool = False
    ):
        """Get all users in an organization with count support"""

        role_str = get_role_str(current_user.role)

        if role_str not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view organization users"
            )

        if role_str == "org_admin":
            if str(org_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view users in your own organization"
                )

        users, total = await UserModel.get_by_organization(
            org_id, limit, offset, include_deactivated=include_deactivated, return_count=return_count
        )

        if role_str == "org_admin":
            org_admin_count = await count_org_admins_by_organization(org_id)
            if org_admin_count > 0:
                for user in users:
                    if user.role == UserRole.ORG_ADMIN:
                        return [user], 1
                return [users[0]] if users else [], 1 if users else 0

        return users, total

    @staticmethod
    async def get_users_by_clinic(
        clinic_id: str,
        current_user: User,
        include_deactivated: bool = False,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ):
        """Get all users assigned to a clinic with count support"""

        role_str = get_role_str(current_user.role)

        if role_str == "clinic_manager":
            if clinic_id not in (current_user.assigned_clinics or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view users in your assigned clinics"
                )

        return await UserModel.get_by_clinic(
            clinic_id,
            include_deactivated=include_deactivated,
            limit=limit,
            offset=offset,
            return_count=return_count
        )