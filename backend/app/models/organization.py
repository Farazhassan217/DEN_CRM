from typing import Optional, List
from ..core.supabase_client import get_admin_client
from ..schemas.organization import Organization, OrganizationCreate, OrganizationUpdate


class OrganizationModel:
    """Model for organization operations with Supabase"""
    
    TABLE_NAME = "organizations"
    
    @staticmethod
    async def create(org_data: OrganizationCreate) -> Organization:
        """Create a new organization"""
        supabase = get_admin_client()
        
        data = org_data.model_dump(exclude_unset=True)
        
        response = supabase.table(OrganizationModel.TABLE_NAME).insert(data).execute()
        return Organization(**response.data[0])
    
    @staticmethod
    async def get_by_id(org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        supabase = get_admin_client()
        
        response = supabase.table(OrganizationModel.TABLE_NAME)\
            .select("*")\
            .eq("id", org_id)\
            .execute()
        
        if response.data:
            return Organization(**response.data[0])
        return None
    
    @staticmethod
    async def update(org_id: str, org_data: OrganizationUpdate) -> Optional[Organization]:
        """Update organization"""
        supabase = get_admin_client()
        
        data = org_data.model_dump(exclude_unset=True)
        
        response = supabase.table(OrganizationModel.TABLE_NAME)\
            .update(data)\
            .eq("id", org_id)\
            .execute()
        
        if response.data:
            return Organization(**response.data[0])
        return None
    
    @staticmethod
    async def delete(org_id: str) -> bool:
        """Soft delete organization"""
        supabase = get_admin_client()
        
        response = supabase.table(OrganizationModel.TABLE_NAME)\
            .update({"is_active": False})\
            .eq("id", org_id)\
            .execute()
        
        return len(response.data) > 0
    
    @staticmethod
    async def get_all(limit: int = 100, offset: int = 0) -> List[Organization]:
        """Get all organizations"""
        supabase = get_admin_client()
        
        response = supabase.table(OrganizationModel.TABLE_NAME)\
            .select("*")\
            .eq("is_active", True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return [Organization(**org) for org in response.data]
    
    @staticmethod
    async def count() -> int:
        """Count all active organizations"""
        supabase = get_admin_client()
        
        response = supabase.table(OrganizationModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("is_active", True)\
            .execute()
        
        return response.count if response.count else 0
