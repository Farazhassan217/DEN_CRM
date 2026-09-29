from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime, date, time
from enum import Enum


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    REMINDED = "reminded"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    TREATMENT = "treatment"
    FOLLOW_UP = "follow_up"
    CLEANING = "cleaning"
    EMERGENCY = "emergency"
    OTHER = "other"


class AppointmentBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 30
    notes: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    patient_name: str
    patient_email: Optional[EmailStr] = None
    patient_phone: str = Field(..., min_length=7, max_length=20, pattern=r'^\+?[0-9\-\(\)\s]{7,20}$')
    reminder_sent: bool = False


class AppointmentCreate(AppointmentBase):
    clinic_id: str
    lead_id: Optional[str] = None
    assigned_to: Optional[str] = None  # User ID (reception/doctor)


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    appointment_type: Optional[AppointmentType] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    patient_name: Optional[str] = None
    patient_email: Optional[EmailStr] = None
    patient_phone: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r'^\+?[0-9\-\(\)\s]{7,20}$')
    reminder_sent: Optional[bool] = None
    assigned_to: Optional[str] = None


class Appointment(AppointmentBase):
    id: str
    clinic_id: str
    lead_id: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    checked_in_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    revenue_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
