from typing import Optional, List, Tuple, Union
from ..core.supabase_client import get_admin_client
from ..core.async_runner import execute_query
from ..schemas.lead import Lead, LeadCreate, LeadUpdate, LeadStatus


class LeadModel:
    """Model for lead operations with Supabase (Non-blocking async execution)"""
    
    TABLE_NAME = "leads"
    
    @staticmethod
    async def create(lead_data: LeadCreate) -> Lead:
        """Create a new lead"""
        supabase = get_admin_client()
        data = lead_data.model_dump(exclude_unset=True)
        query = supabase.table(LeadModel.TABLE_NAME).insert(data)
        response = await execute_query(query)
        return Lead(**response.data[0])
    
    @staticmethod
    async def get_by_id(lead_id: str, include_deleted: bool = False) -> Optional[Lead]:
        """Get lead by ID (excluding soft-deleted leads by default)"""
        supabase = get_admin_client()
        query = supabase.table(LeadModel.TABLE_NAME).select("*").eq("id", lead_id)
        if not include_deleted:
            query = query.eq("is_deleted", False)
        
        response = await execute_query(query)
        if response.data:
            return Lead(**response.data[0])
        return None
    
    @staticmethod
    async def update(lead_id: str, lead_data: LeadUpdate) -> Optional[Lead]:
        """Update lead"""
        supabase = get_admin_client()
        data = lead_data.model_dump(exclude_unset=True)
        query = supabase.table(LeadModel.TABLE_NAME).update(data).eq("id", lead_id)
        response = await execute_query(query)
        if response.data:
            return Lead(**response.data[0])
        return None
    
    @staticmethod
    async def delete(lead_id: str) -> bool:
        """Soft delete lead"""
        supabase = get_admin_client()
        query = supabase.table(LeadModel.TABLE_NAME).update({"is_deleted": True}).eq("id", lead_id)
        response = await execute_query(query)
        return len(response.data) > 0
    
    @staticmethod
    async def get_by_clinic(
        clinic_id: str,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ) -> Union[List[Lead], Tuple[List[Lead], int]]:
        """Get all leads for a clinic with count support"""
        supabase = get_admin_client()
        query = (
            supabase.table(LeadModel.TABLE_NAME)
            .select("*", count="exact")
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        response = await execute_query(query)
        leads = [Lead(**lead) for lead in response.data]
        if return_count:
            total = response.count if response.count is not None else len(leads)
            return leads, total
        return leads
    
    @staticmethod
    async def get_by_assigned_user(
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ) -> Union[List[Lead], Tuple[List[Lead], int]]:
        """Get leads assigned to a specific user with count support"""
        supabase = get_admin_client()
        query = (
            supabase.table(LeadModel.TABLE_NAME)
            .select("*", count="exact")
            .eq("assigned_to", user_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        response = await execute_query(query)
        leads = [Lead(**lead) for lead in response.data]
        if return_count:
            total = response.count if response.count is not None else len(leads)
            return leads, total
        return leads
    
    @staticmethod
    async def get_by_organization(
        org_id: str,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ) -> Union[List[Lead], Tuple[List[Lead], int]]:
        """Get all leads in an organization with count support"""
        supabase = get_admin_client()
        query = (
            supabase.table(LeadModel.TABLE_NAME)
            .select("*", count="exact")
            .eq("organization_id", org_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        response = await execute_query(query)
        leads = [Lead(**lead) for lead in response.data]
        if return_count:
            total = response.count if response.count is not None else len(leads)
            return leads, total
        return leads
    
    @staticmethod
    async def get_by_status(status: LeadStatus, clinic_id: Optional[str] = None) -> List[Lead]:
        """Get leads by status"""
        supabase = get_admin_client()
        query = (
            supabase.table(LeadModel.TABLE_NAME)
            .select("*")
            .eq("status", status.value)
            .eq("is_deleted", False)
        )
        if clinic_id:
            query = query.eq("clinic_id", clinic_id)
        
        response = await execute_query(query)
        return [Lead(**lead) for lead in response.data]
    
    @staticmethod
    async def count_by_clinic(clinic_id: str) -> int:
        """Count leads in a clinic"""
        supabase = get_admin_client()
        query = (
            supabase.table(LeadModel.TABLE_NAME)
            .select("id", count="exact")
            .eq("clinic_id", clinic_id)
            .eq("is_deleted", False)
        )
        response = await execute_query(query)
        return response.count if response.count else 0
    
    @staticmethod
    async def search(query_text: str, clinic_id: Optional[str] = None) -> List[Lead]:
        """Search leads by name, email, or phone"""
        supabase = get_admin_client()
        search_query = (
            supabase.table(LeadModel.TABLE_NAME)
            .select("*")
            .or_(f"first_name.ilike.%{query_text}%,last_name.ilike.%{query_text}%,email.ilike.%{query_text}%,phone.ilike.%{query_text}%")
            .eq("is_deleted", False)
        )
        if clinic_id:
            search_query = search_query.eq("clinic_id", clinic_id)
        
        response = await execute_query(search_query)
        return [Lead(**lead) for lead in response.data]
