from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    ON_HOLD = "on_hold"


class LeadSource(str, Enum):
    WEBSITE = "website"
    PHONE_CALL = "phone_call"
    WALK_IN = "walk_in"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    INSTAGRAM = "instagram"
    EMAIL_CAMPAIGN = "email_campaign"
    OTHER = "other"


class LeadBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    source: Optional[LeadSource] = LeadSource.OTHER
    status: Optional[LeadStatus] = LeadStatus.NEW
    notes: Optional[str] = None
    treatment_interest: Optional[str] = None
    expected_revenue: Optional[float] = None
    assigned_to: Optional[str] = None  # User ID
    
    # FIX 1: priority ko Optional[str] banaya taake DB ka NULL gracefully handle ho
    priority: Optional[str] = "medium"  # low, medium, high, urgent


class LeadCreate(LeadBase):
    clinic_id: Optional[str] = None
    organization_id: Optional[str] = None


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    source: Optional[LeadSource] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None
    treatment_interest: Optional[str] = None
    expected_revenue: Optional[float] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    clinic_id: Optional[str] = None


class Lead(LeadBase):
    id: str
    # FIX 2: clinic_id aur organization_id ko optional banaya response safety ke liye
    clinic_id: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    converted_at: Optional[datetime] = None
    lost_reason: Optional[str] = None
    last_contacted_at: Optional[datetime] = None
    appointment_count: Optional[int] = 0
    call_count: Optional[int] = 0
    note_count: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)