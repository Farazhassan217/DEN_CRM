import uuid
from typing import Optional, List
from ..core.supabase_client import get_admin_client
from ..schemas.clinic import Clinic, ClinicCreate, ClinicUpdate


def is_valid_uuid(val: Optional[str]) -> bool:
    """Validate whether input is a non-empty valid UUID string."""
    if not val or str(val).strip().lower() in ["none", "null", ""]:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


class ClinicModel:
    """Model for clinic operations with Supabase"""
    
    TABLE_NAME = "clinics"
    
    @staticmethod
    async def get_all() -> List[Clinic]:
        """Get all active clinics in the system (for Super Admin)"""
        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .eq("is_active", True)\
            .execute()
        
        return [Clinic(**clinic) for clinic in response.data] if response.data else []

    # Alias for flexibility
    get_all_clinics = get_all

    @staticmethod
    async def create(clinic_data: ClinicCreate) -> Clinic:
        """Create a new clinic"""
        supabase = get_admin_client()
        
        data = clinic_data.model_dump(exclude_unset=True)
        
        response = supabase.table(ClinicModel.TABLE_NAME).insert(data).execute()
        return Clinic(**response.data[0])
    
    @staticmethod
    async def get_by_id(clinic_id: str) -> Optional[Clinic]:
        """Get clinic by ID with UUID validation guard"""
        if not is_valid_uuid(clinic_id):
            return None

        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .eq("id", str(clinic_id))\
            .execute()
        
        if response.data:
            return Clinic(**response.data[0])
        return None
    
    @staticmethod
    async def update(clinic_id: str, clinic_data: ClinicUpdate) -> Optional[Clinic]:
        """Update clinic"""
        if not is_valid_uuid(clinic_id):
            return None

        supabase = get_admin_client()
        
        data = clinic_data.model_dump(exclude_unset=True)
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .update(data)\
            .eq("id", str(clinic_id))\
            .execute()
        
        if response.data:
            return Clinic(**response.data[0])
        return None
    
    @staticmethod
    async def delete(clinic_id: str) -> bool:
        """Soft delete clinic"""
        if not is_valid_uuid(clinic_id):
            return False

        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .update({"is_active": False})\
            .eq("id", str(clinic_id))\
            .execute()
        
        return len(response.data) > 0 if response.data else False
    
    @staticmethod
    async def get_by_organization(org_id: str) -> List[Clinic]:
        """Get all active clinics in an organization safely"""
        if not is_valid_uuid(org_id):
            return []

        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .eq("organization_id", str(org_id))\
            .eq("is_active", True)\
            .execute()
        
        return [Clinic(**clinic) for clinic in response.data] if response.data else []
    
    @staticmethod
    async def get_by_ids(clinic_ids: List[str]) -> List[Clinic]:
        """Get clinics by IDs safely"""
        valid_ids = [str(cid) for cid in clinic_ids if is_valid_uuid(str(cid))]
        if not valid_ids:
            return []

        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .in_("id", valid_ids)\
            .execute()
        
        return [Clinic(**clinic) for clinic in response.data] if response.data else []
    
    @staticmethod
    async def count_by_organization(org_id: str) -> int:
        """Count clinics in an organization"""
        if not is_valid_uuid(org_id):
            return 0

        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("organization_id", str(org_id))\
            .eq("is_active", True)\
            .execute()
        
        return response.count if response.count else 0