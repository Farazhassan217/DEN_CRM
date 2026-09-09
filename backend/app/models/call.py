from typing import Optional, List
from ..core.supabase_client import get_admin_client
from ..schemas.call import Call, CallCreate


class CallModel:
    """Model for call operations with Supabase"""
    
    TABLE_NAME = "calls"
    
    @staticmethod
    async def create(call_data: CallCreate) -> Call:
        """Create a new call log"""
        supabase = get_admin_client()
        
        data = call_data.model_dump(exclude_unset=True)
        
        response = supabase.table(CallModel.TABLE_NAME).insert(data).execute()
        return Call(**response.data[0])
    
    @staticmethod
    async def get_by_id(call_id: str) -> Optional[Call]:
        """Get call by ID"""
        supabase = get_admin_client()
        
        response = supabase.table(CallModel.TABLE_NAME)\
            .select("*")\
            .eq("id", call_id)\
            .execute()
        
        if response.data:
            return Call(**response.data[0])
        return None
    
    @staticmethod
    async def get_by_lead(lead_id: str, limit: int = 100) -> List[Call]:
        """Get all calls for a lead"""
        supabase = get_admin_client()
        
        response = supabase.table(CallModel.TABLE_NAME)\
            .select("*")\
            .eq("lead_id", lead_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [Call(**call) for call in response.data]
    
    @staticmethod
    async def get_by_user(user_id: str, limit: int = 100) -> List[Call]:
        """Get all calls made by a user"""
        supabase = get_admin_client()
        
        response = supabase.table(CallModel.TABLE_NAME)\
            .select("*")\
            .eq("made_by", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [Call(**call) for call in response.data]
    
    @staticmethod
    async def get_by_clinic(clinic_id: str, limit: int = 100) -> List[Call]:
        """Get all calls for a clinic"""
        supabase = get_admin_client()
        
        response = supabase.table(CallModel.TABLE_NAME)\
            .select("*")\
            .eq("clinic_id", clinic_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [Call(**call) for call in response.data]
    
    @staticmethod
    async def count_by_user(user_id: str) -> int:
        """Count calls made by a user"""
        supabase = get_admin_client()
        
        response = supabase.table(CallModel.TABLE_NAME)\
            .select("id", count="exact")\
            .eq("made_by", user_id)\
            .execute()
        
        return response.count if response.count else 0
