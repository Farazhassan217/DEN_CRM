from typing import Optional, List
from fastapi import HTTPException, status
from ..core.roles import UserRole, Permission, has_permission, get_role_permissions
from ..schemas.user import User, UserCreate, UserUpdate
from ..models.user import UserModel
from ..models.audit import AuditModel
from ..services.audit import AuditService
from .auth import get_password_hash


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

        # ==================================================================
        # EXPLICIT BLOCK: Finance, Agent, and Reception cannot create users
        # ==================================================================
        if created_role_str in ["finance", "agent", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Finance and operational roles do not have permission to create users."
            )

        # 1. Permission check: Super Admin, Org Admin, and Clinic Manager can create users
        if not has_permission(created_by.role, Permission.USER_CREATE):
            if created_role_str not in ["super_admin", "org_admin", "clinic_manager"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to create users"
                )

        # 2. Check if user already exists
        existing_user = await UserModel.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # 3. Org Admin / Clinic Manager scope rules
        if created_role_str == "org_admin":
            if user_data.organization_id and str(user_data.organization_id) != str(created_by.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create users in your own organization"
                )
            user_data.organization_id = created_by.organization_id

        elif created_role_str == "clinic_manager":
            # Clinic Manager must belong to the same organization and assign user to their assigned clinics
            user_data.organization_id = created_by.organization_id
            
            # Ensure the user being created is assigned to one of the manager's clinics
            if user_data.assigned_clinics:
                for c_id in user_data.assigned_clinics:
                    if c_id not in (created_by.assigned_clinics or []):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Can only create users for your assigned clinics"
                        )
            else:
                # Default to manager's assigned clinics if none provided
                user_data.assigned_clinics = created_by.assigned_clinics

        # 4. Hash password
        hashed_password = get_password_hash(user_data.password)

        user_dict = user_data.model_dump()
        user_dict['password'] = hashed_password

        # 5. Create user in Database
        created_user = await UserModel.create(user_dict)

        # 6. Log audit
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
            pass  # Audit logging failure should not block user creation

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

        # Scope checks
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
            if role_str not in ["super_admin", "org_admin"] and str(user_id) != str(current_user.id):
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

        # Scope checks for role changes
        if user_data.role and user_data.role != user.role:
            if role_str not in ["super_admin", "org_admin"]:
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

        updated_user = await UserModel.update(user_id, user_data)

        # Log audit
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
            if role_str not in ["super_admin", "org_admin"]:
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

        return await UserModel.get_by_organization(
            org_id, limit, offset, include_deactivated=include_deactivated, return_count=return_count
        )

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