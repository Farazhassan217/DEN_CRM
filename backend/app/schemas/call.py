from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class CallType(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class CallOutcome(str, Enum):
    ANSWERED = "answered"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    WRONG_NUMBER = "wrong_number"
    CALLBACK_REQUESTED = "callback_requested"
    APPOINTMENT_BOOKED = "appointment_booked"
    NOT_INTERESTED = "not_interested"


class CallBase(BaseModel):
    lead_id: str
    call_type: CallType
    outcome: CallOutcome
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None


class CallCreate(CallBase):
    clinic_id: str
    made_by: str  # User ID


class CallLog(BaseModel):
    phone_number: str = Field(..., min_length=7, max_length=20, pattern=r'^\+?[0-9\-\(\)\s]{7,20}$')
    call_type: CallType
    timestamp: datetime
    duration_seconds: Optional[int] = None


class Call(CallBase):
    id: str
    clinic_id: str
    made_by: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
