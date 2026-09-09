from typing import Optional, List
from ..core.supabase_client import get_admin_client
from ..schemas.note import Note, NoteCreate, NoteUpdate


class NoteModel:
    """Model for note operations with Supabase"""
    
    TABLE_NAME = "notes"
    
    @staticmethod
    async def create(note_data: NoteCreate) -> Note:
        """Create a new note"""
        supabase = get_admin_client()
        
        data = note_data.model_dump(exclude_unset=True)
        
        response = supabase.table(NoteModel.TABLE_NAME).insert(data).execute()
        return Note(**response.data[0])
    
    @staticmethod
    async def get_by_id(note_id: str) -> Optional[Note]:
        """Get note by ID"""
        supabase = get_admin_client()
        
        response = supabase.table(NoteModel.TABLE_NAME)\
            .select("*")\
            .eq("id", note_id)\
            .execute()
        
        if response.data:
            return Note(**response.data[0])
        return None
    
    @staticmethod
    async def update(note_id: str, note_data: NoteUpdate) -> Optional[Note]:
        """Update note"""
        supabase = get_admin_client()
        
        data = note_data.model_dump(exclude_unset=True)
        
        response = supabase.table(NoteModel.TABLE_NAME)\
            .update(data)\
            .eq("id", note_id)\
            .execute()
        
        if response.data:
            return Note(**response.data[0])
        return None
    
    @staticmethod
    async def delete(note_id: str) -> bool:
        """Delete note"""
        supabase = get_admin_client()
        
        response = supabase.table(NoteModel.TABLE_NAME)\
            .delete()\
            .eq("id", note_id)\
            .execute()
        
        return len(response.data) > 0
    
    @staticmethod
    async def get_by_lead(lead_id: str, limit: int = 100) -> List[Note]:
        """Get all notes for a lead"""
        supabase = get_admin_client()
        
        response = supabase.table(NoteModel.TABLE_NAME)\
            .select("*")\
            .eq("lead_id", lead_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [Note(**note) for note in response.data]
    
    @staticmethod
    async def get_by_clinic(clinic_id: str, limit: int = 100) -> List[Note]:
        """Get all notes for a clinic"""
        supabase = get_admin_client()
        
        response = supabase.table(NoteModel.TABLE_NAME)\
            .select("*")\
            .eq("clinic_id", clinic_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return [Note(**note) for note in response.data]
    
    @staticmethod
    async def get_internal_notes(lead_id: str) -> List[Note]:
        """Get only internal notes for a lead"""
        supabase = get_admin_client()
        
        response = supabase.table(NoteModel.TABLE_NAME)\
            .select("*")\
            .eq("lead_id", lead_id)\
            .eq("is_internal", True)\
            .order("created_at", desc=True)\
            .execute()
        
        return [Note(**note) for note in response.data]
