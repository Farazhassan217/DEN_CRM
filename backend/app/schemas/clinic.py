from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ClinicBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    timezone: str = "UTC"
    working_hours: Optional[dict] = None  # {monday: {open: "09:00", close: "17:00"}, ...}


class ClinicCreate(ClinicBase):
    organization_id: str


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    working_hours: Optional[dict] = None
    is_active: Optional[bool] = None


class ClinicAssignment(BaseModel):
    clinic_id: str
    user_id: str
    assigned_at: datetime


class Clinic(ClinicBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    lead_count: int = 0
    appointment_count: int = 0
    revenue_total: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)
