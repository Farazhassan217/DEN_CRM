from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class ReportFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    clinic_ids: Optional[List[str]] = None
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    lead_status: Optional[List[str]] = None
    appointment_status: Optional[List[str]] = None
    payment_status: Optional[List[str]] = None
    group_by: Optional[str] = None  # date, clinic, user, status


class DashboardData(BaseModel):
    # Lead Metrics
    total_leads: int = 0
    new_leads: int = 0
    converted_leads: int = 0
    conversion_rate: float = 0.0
    
    # Appointment Metrics
    total_appointments: int = 0
    upcoming_appointments: int = 0
    completed_appointments: int = 0
    no_show_count: int = 0
    no_show_rate: float = 0.0
    
    # Revenue Metrics
    total_revenue: float = 0.0
    pending_revenue: float = 0.0
    collected_revenue: float = 0.0
    outstanding_revenue: float = 0.0
    
    # Call Metrics
    total_calls: int = 0
    answered_calls: int = 0
    call_answer_rate: float = 0.0
    
    # Task Metrics
    pending_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    
    # Time-based data for charts
    leads_over_time: List[Dict[str, Any]] = []
    revenue_over_time: List[Dict[str, Any]] = []
    appointments_over_time: List[Dict[str, Any]] = []


class LeadReport(BaseModel):
    total_leads: int
    by_status: Dict[str, int]
    by_source: Dict[str, int]
    by_clinic: Dict[str, int]
    by_agent: Dict[str, int]
    conversion_rate: float
    avg_conversion_days: float


class RevenueReport(BaseModel):
    total_revenue: float
    collected: float
    pending: float
    outstanding: float
    by_clinic: Dict[str, float]
    by_treatment: Dict[str, float]
    by_payment_type: Dict[str, float]
    refunds: float


class AppointmentReport(BaseModel):
    total_appointments: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_clinic: Dict[str, int]
    no_shows: int
    no_show_rate: float
    avg_duration: float


class UserPerformanceReport(BaseModel):
    user_id: str
    user_name: str
    role: str
    leads_handled: int
    leads_converted: int
    conversion_rate: float
    calls_made: int
    appointments_booked: int
    revenue_generated: float
    tasks_completed: int
