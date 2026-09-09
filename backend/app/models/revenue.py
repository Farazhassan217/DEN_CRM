from typing import Optional, List, Tuple, Union
from uuid import UUID
from enum import Enum
from decimal import Decimal
from ..core.supabase_client import get_admin_client
from ..core.async_runner import execute_query
from ..schemas.revenue import Revenue, RevenueCreate, RevenueUpdate, PaymentStatus


def sanitize_value(v):
    """Convert non-JSON serializable types into primitive values."""
    if isinstance(v, UUID):
        return str(v)
    elif isinstance(v, Enum):
        return v.value
    elif isinstance(v, Decimal):
        return float(v)
    elif hasattr(v, "isoformat"):
        return v.isoformat()
    elif isinstance(v, dict):
        return {k: sanitize_value(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [sanitize_value(val) for val in v]
    return v


class RevenueModel:
    """Model for revenue operations with Supabase (Non-blocking async execution)"""
    
    TABLE_NAME = "revenue"
    PAYMENTS_TABLE = "payments"
    
    @staticmethod
    async def create(data: dict) -> Revenue:
        """Create a new revenue record"""
        supabase = get_admin_client()
        data.pop("installments", None)
        cleaned_data = {k: sanitize_value(v) for k, v in data.items()}
        
        query = supabase.table(RevenueModel.TABLE_NAME).insert(cleaned_data)
        response = await execute_query(query)
        
        if not response.data:
            raise Exception("Failed to create revenue record")
            
        return Revenue(**response.data[0])
    
    @staticmethod
    async def get_by_id(revenue_id: str) -> Optional[Revenue]:
        """Get revenue record by ID"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*, payments(*)")
            .eq("id", str(revenue_id))
        )
        response = await execute_query(query)
        if response.data:
            return Revenue(**response.data[0])
        return None
    
    @staticmethod
    async def update(revenue_id: str, revenue_data: RevenueUpdate) -> Optional[Revenue]:
        """Update revenue record"""
        supabase = get_admin_client()
        data = revenue_data.model_dump(exclude_unset=True, mode="json")
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .update(data)
            .eq("id", str(revenue_id))
        )
        response = await execute_query(query)
        if response.data:
            return Revenue(**response.data[0])
        return None

    @staticmethod
    async def get_all(
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ) -> Union[List[Revenue], Tuple[List[Revenue], int]]:
        """Get all revenue records with pagination"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*, payments(*)", count="exact")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        response = await execute_query(query)
        records = [Revenue(**rev) for rev in response.data]
        if return_count:
            total = response.count if response.count is not None else len(records)
            return records, total
        return records
    
    @staticmethod
    async def get_by_clinic(
        clinic_id: str,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ) -> Union[List[Revenue], Tuple[List[Revenue], int]]:
        """Get revenue records for a clinic"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*, payments(*)", count="exact")
            .eq("clinic_id", str(clinic_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        response = await execute_query(query)
        records = [Revenue(**rev) for rev in response.data]
        if return_count:
            total = response.count if response.count is not None else len(records)
            return records, total
        return records
    
    @staticmethod
    async def get_by_lead(lead_id: str) -> List[Revenue]:
        """Get revenue records for a lead"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*, payments(*)")
            .eq("lead_id", str(lead_id))
            .order("created_at", desc=True)
        )
        response = await execute_query(query)
        return [Revenue(**rev) for rev in response.data]
    
    @staticmethod
    async def get_by_organization(
        org_id: str,
        limit: int = 100,
        offset: int = 0,
        return_count: bool = False
    ) -> Union[List[Revenue], Tuple[List[Revenue], int]]:
        """Get revenue records for an organization"""
        supabase = get_admin_client()
        from .clinic import ClinicModel
        clinics = await ClinicModel.get_by_organization(str(org_id))
        clinic_ids = [str(c.id) for c in clinics if hasattr(c, "id")]
        
        if not clinic_ids:
            return ([], 0) if return_count else []
        
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*", count="exact")
            .in_("clinic_id", clinic_ids)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )
        response = await execute_query(query)
        records = [Revenue(**rev) for rev in response.data] if response.data else []
        if return_count:
            total = response.count if response.count is not None else len(records)
            return records, total
        return records
    
    @staticmethod
    async def get_by_payment_status(status: PaymentStatus, clinic_id: Optional[str] = None) -> List[Revenue]:
        """Get revenue by payment status"""
        supabase = get_admin_client()
        status_val = status.value if hasattr(status, "value") else str(status)
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*, payments(*)")
            .eq("payment_status", status_val)
        )
        if clinic_id:
            query = query.eq("clinic_id", str(clinic_id))
        
        response = await execute_query(query)
        return [Revenue(**rev) for rev in response.data]
    
    @staticmethod
    async def get_outstanding_payments(clinic_id: Optional[str] = None) -> List[Revenue]:
        """Get revenue with outstanding payments"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("*, payments(*)")
            .gt("outstanding_amount", 0)
            .neq("payment_status", PaymentStatus.CANCELLED.value)
        )
        if clinic_id:
            query = query.eq("clinic_id", str(clinic_id))
        
        response = await execute_query(query)
        return [Revenue(**rev) for rev in response.data]
    
    @staticmethod
    async def total_by_clinic(clinic_id: str) -> dict:
        """Get revenue totals for a clinic"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.TABLE_NAME)
            .select("total_amount, paid_amount, outstanding_amount")
            .eq("clinic_id", str(clinic_id))
        )
        response = await execute_query(query)
        total = sum(r.get('total_amount', 0) for r in response.data) if response.data else 0
        paid = sum(r.get('paid_amount', 0) for r in response.data) if response.data else 0
        outstanding = sum(r.get('outstanding_amount', 0) for r in response.data) if response.data else 0
        
        return {
            "total_revenue": total,
            "collected": paid,
            "outstanding": outstanding
        }
    
    @staticmethod
    async def create_payment(payment_data: dict) -> dict:
        """Create a payment record"""
        supabase = get_admin_client()
        cleaned_payment = {k: sanitize_value(v) for k, v in payment_data.items()}
        query = supabase.table(RevenueModel.PAYMENTS_TABLE).insert(cleaned_payment)
        response = await execute_query(query)
        return response.data[0] if response.data else None
    
    @staticmethod
    async def get_payments_by_revenue(revenue_id: str) -> List[dict]:
        """Get all payments for a revenue record"""
        supabase = get_admin_client()
        query = (
            supabase.table(RevenueModel.PAYMENTS_TABLE)
            .select("*")
            .eq("revenue_id", str(revenue_id))
            .order("payment_date", desc=True)
        )
        response = await execute_query(query)
        return response.data if response.data else []