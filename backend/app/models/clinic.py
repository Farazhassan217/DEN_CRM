from typing import Optional, List
from ..core.supabase_client import get_admin_client
from ..schemas.clinic import Clinic, ClinicCreate, ClinicUpdate


class ClinicModel:
    """Model for clinic operations with Supabase"""
    
    TABLE_NAME = "clinics"
    
    @staticmethod
    async def create(clinic_data: ClinicCreate) -> Clinic:
        """Create a new clinic"""
        supabase = get_admin_client()
        
        data = clinic_data.model_dump(exclude_unset=True)
        
        response = supabase.table(ClinicModel.TABLE_NAME).insert(data).execute()
        return Clinic(**response.data[0])
    
    @staticmethod
    async def get_by_id(clinic_id: str) -> Optional[Clinic]:
        """Get clinic by ID"""
        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .eq("id", clinic_id)\
            .execute()
        
        if response.data:
            return Clinic(**response.data[0])
        return None
    
    @staticmethod
    async def update(clinic_id: str, clinic_data: ClinicUpdate) -> Optional[Clinic]:
        """Update clinic"""
        supabase = get_admin_client()
        
        data = clinic_data.model_dump(exclude_unset=True)
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .update(data)\
            .eq("id", clinic_id)\
            .execute()
        
        if response.data:
            return Clinic(**response.data[0])
        return None
    
    @staticmethod
    async def delete(clinic_id: str) -> bool:
        """Soft delete clinic"""
        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .update({"is_active": False})\
            .eq("id", clinic_id)\
            .execute()
        
        return len(response.data) > 0
    
    @staticmethod
    async def get_by_organization(org_id: str) -> List[Clinic]:
        """Get all clinics in an organization"""
        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .eq("organization_id", org_id)\
            .eq("is_active", True)\
            .execute()
        
        return [Clinic(**clinic) for clinic in response.data]
    
    @staticmethod
    async def get_by_ids(clinic_ids: List[str]) -> List[Clinic]:
        """Get clinics by IDs"""
        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("*")\
            .in_("id", clinic_ids)\
            .execute()
        
        return [Clinic(**clinic) for clinic in response.data]
    
    @staticmethod
    async def count_by_organization(org_id: str) -> int:
        """Count clinics in an organization"""
        supabase = get_admin_client()
        
        response = supabase.table(ClinicModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("organization_id", org_id)\
            .eq("is_active", True)\
            .execute()
        
        return response.count if response.count else 0
