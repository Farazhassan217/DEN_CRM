from typing import Optional, List
from datetime import date
from ..core.supabase_client import get_admin_client
from ..core.async_runner import execute_query
from ..schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentStatus


class AppointmentModel:
    """Model for appointment operations with Supabase (Non-blocking async execution)"""
    
    TABLE_NAME = "appointments"
    
    @staticmethod
    async def create(appointment_data: AppointmentCreate) -> Appointment:
        """Create a new appointment"""
        supabase = get_admin_client()
        data = appointment_data.model_dump(exclude_unset=True, mode="json")
        query = supabase.table(AppointmentModel.TABLE_NAME).insert(data)
        response = await execute_query(query)
        return Appointment(**response.data[0])
    
    @staticmethod
    async def get_by_id(appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("*")
            .eq("id", appointment_id)
        )
        response = await execute_query(query)
        if response.data:
            return Appointment(**response.data[0])
        return None
    
    @staticmethod
    async def update(appointment_id: str, appointment_data: AppointmentUpdate) -> Optional[Appointment]:
        """Update appointment"""
        supabase = get_admin_client()
        data = appointment_data.model_dump(exclude_unset=True, mode="json")
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .update(data)
            .eq("id", appointment_id)
        )
        response = await execute_query(query)
        if response.data:
            return Appointment(**response.data[0])
        return None
    
    @staticmethod
    async def delete(appointment_id: str) -> bool:
        """Cancel appointment (soft delete)"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .update({"status": AppointmentStatus.CANCELLED.value})
            .eq("id", appointment_id)
        )
        response = await execute_query(query)
        return len(response.data) > 0
    
    @staticmethod
    async def get_by_clinic(
        clinic_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Appointment]:
        """Get appointments for a clinic within date range"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("*")
            .eq("clinic_id", clinic_id)
            .neq("status", AppointmentStatus.CANCELLED.value)
            .order("scheduled_date")
            .order("scheduled_time")
        )
        if start_date:
            query = query.gte("scheduled_date", start_date.isoformat())
        if end_date:
            query = query.lte("scheduled_date", end_date.isoformat())
        
        response = await execute_query(query)
        return [Appointment(**apt) for apt in response.data]
    
    @staticmethod
    async def get_by_lead(lead_id: str) -> List[Appointment]:
        """Get all appointments for a lead"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("*")
            .eq("lead_id", lead_id)
            .order("scheduled_date", desc=True)
        )
        response = await execute_query(query)
        return [Appointment(**apt) for apt in response.data]
    
    @staticmethod
    async def get_by_user(user_id: str, start_date: Optional[date] = None) -> List[Appointment]:
        """Get appointments assigned to a user"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("*")
            .eq("assigned_to", user_id)
            .neq("status", AppointmentStatus.CANCELLED.value)
            .order("scheduled_date", asc=True)
            .order("scheduled_time", asc=True)
        )
        if start_date:
            query = query.gte("scheduled_date", start_date.isoformat())
        
        response = await execute_query(query)
        return [Appointment(**apt) for apt in response.data]
    
    @staticmethod
    async def get_by_status(status: AppointmentStatus, clinic_id: Optional[str] = None) -> List[Appointment]:
        """Get appointments by status"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("*")
            .eq("status", status.value)
            .order("scheduled_date", asc=True)
        )
        if clinic_id:
            query = query.eq("clinic_id", clinic_id)
        
        response = await execute_query(query)
        return [Appointment(**apt) for apt in response.data]
    
    @staticmethod
    async def get_upcoming(clinic_id: str, limit: int = 50) -> List[Appointment]:
        """Get upcoming appointments for a clinic"""
        supabase = get_admin_client()
        from datetime import datetime
        today = datetime.now().date().isoformat()
        
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("*")
            .eq("clinic_id", clinic_id)
            .gte("scheduled_date", today)
            .neq("status", AppointmentStatus.CANCELLED.value)
            .order("scheduled_date", asc=True)
            .order("scheduled_time", asc=True)
            .limit(limit)
        )
        response = await execute_query(query)
        return [Appointment(**apt) for apt in response.data]
    
    @staticmethod
    async def count_by_clinic(clinic_id: str, status: Optional[AppointmentStatus] = None) -> int:
        """Count appointments in a clinic"""
        supabase = get_admin_client()
        query = (
            supabase.table(AppointmentModel.TABLE_NAME)
            .select("id", count="exact")
            .eq("clinic_id", clinic_id)
        )
        if status:
            query = query.eq("status", status.value)
        
        response = await execute_query(query)
        return response.count if response.count else 0