import uuid
from typing import Optional, List
from fastapi import HTTPException, status
from ..core.roles import UserRole, has_permission
from ..schemas.clinic import Clinic, ClinicCreate, ClinicUpdate
from ..schemas.user import User
from ..models.clinic import ClinicModel
from ..services.audit import AuditService


def get_role_str(role_obj) -> str:
    if hasattr(role_obj, "value"):
        return str(role_obj.value).lower()
    return str(role_obj).lower()


def is_valid_uuid(val: Optional[str]) -> bool:
    """Check if value is a non-empty valid UUID string."""
    if not val or str(val).strip().lower() in ["none", "null", ""]:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


class ClinicService:
    """Clinic management service"""

    @staticmethod
    async def get_all_clinics(current_user: User) -> List[Clinic]:
        """Fetch all clinics in the system (Super Admin only)."""
        role_str = get_role_str(current_user.role)

        if role_str != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view all clinics"
            )

        # Call model layer to fetch all clinic records
        if hasattr(ClinicModel, "get_all"):
            return await ClinicModel.get_all()
        elif hasattr(ClinicModel, "get_all_clinics"):
            return await ClinicModel.get_all_clinics()
        
        # Fallback query if your model uses raw queries
        return await ClinicModel.query().execute()

    @staticmethod
    async def create_clinic(clinic_data: ClinicCreate, current_user: User) -> Clinic:
        """Create a new clinic with permission checks"""
        role_str = get_role_str(current_user.role)

        if role_str not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create clinics"
            )

        if role_str == "org_admin":
            if str(clinic_data.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only create clinics in your own organization"
                )

        clinic = await ClinicModel.create(clinic_data)

        # Audit logging
        try:
            await AuditService.log_action(
                action="clinic.create",
                entity_type="clinic",
                entity_id=str(clinic.id),
                user_id=str(current_user.id),
                user_email=current_user.email,
                user_role=role_str,
                description=f"Created clinic: {clinic.name}",
                organization_id=str(clinic.organization_id)
            )
        except Exception:
            pass

        return clinic

    @staticmethod
    async def get_clinic(clinic_id: str, current_user: User) -> Clinic:
        """Get clinic by ID with permission checks"""
        if not is_valid_uuid(clinic_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid clinic UUID: '{clinic_id}'"
            )

        clinic = await ClinicModel.get_by_id(clinic_id)
        if not clinic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic not found"
            )

        role_str = get_role_str(current_user.role)

        if role_str == "super_admin":
            return clinic

        if role_str in ["org_admin", "reception"]:
            if str(clinic.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view clinics in your own organization"
                )
            return clinic

        if role_str in ["clinic_manager", "agent", "finance"]:
            assigned = [str(c) for c in (current_user.assigned_clinics or [])]
            if str(clinic_id) not in assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your assigned clinics"
                )
            return clinic

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view clinics"
        )

    @staticmethod
    async def update_clinic(clinic_id: str, clinic_data: ClinicUpdate, current_user: User) -> Clinic:
        """Update clinic with permission checks"""
        if not is_valid_uuid(clinic_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid clinic UUID: '{clinic_id}'"
            )

        clinic = await ClinicModel.get_by_id(clinic_id)
        if not clinic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic not found"
            )

        role_str = get_role_str(current_user.role)

        if role_str not in ["super_admin", "org_admin", "clinic_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update clinics"
            )

        if role_str == "org_admin":
            if str(clinic.organization_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update clinics in your own organization"
                )

        if role_str == "clinic_manager":
            assigned = [str(c) for c in (current_user.assigned_clinics or [])]
            if str(clinic_id) not in assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update your assigned clinics"
                )

        updated_clinic = await ClinicModel.update(clinic_id, clinic_data)

        try:
            await AuditService.log_action(
                action="clinic.update",
                entity_type="clinic",
                entity_id=str(clinic_id),
                user_id=str(current_user.id),
                user_email=current_user.email,
                user_role=role_str,
                description=f"Updated clinic: {clinic.name}",
                organization_id=str(clinic.organization_id),
                clinic_id=str(clinic_id),
                changes=clinic_data.model_dump(exclude_unset=True)
            )
        except Exception:
            pass

        return updated_clinic

    @staticmethod
    async def get_clinics_by_organization(org_id: str, current_user: User) -> List[Clinic]:
        """Get all clinics in an organization with safety validation"""
        # Invalid UUID prevention to stop 22P02 database crashes
        if not is_valid_uuid(org_id):
            return []

        role_str = get_role_str(current_user.role)

        if role_str not in ["super_admin", "org_admin", "clinic_manager", "reception"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view clinics"
            )

        if role_str in ["org_admin", "reception"]:
            if str(org_id) != str(current_user.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view clinics in your own organization"
                )

        return await ClinicModel.get_by_organization(org_id)

    @staticmethod
    async def get_assigned_clinics(current_user: User) -> List[Clinic]:
        """Get clinics assigned to the current user"""
        if not current_user.assigned_clinics:
            return []

        # Filter out invalid UUIDs from assigned array
        valid_assigned_ids = [
            str(cid) for cid in current_user.assigned_clinics if is_valid_uuid(str(cid))
        ]

        if not valid_assigned_ids:
            return []

        return await ClinicModel.get_by_ids(valid_assigned_ids)