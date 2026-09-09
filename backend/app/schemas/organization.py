from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    branding: Optional[dict] = None  # Logo, colors, etc.


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    branding: Optional[dict] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    clinic_count: int = 0
    user_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)
