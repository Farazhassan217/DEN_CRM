from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class NoteType(str, Enum):
    GENERAL = "general"
    CALL_SUMMARY = "call_summary"
    MEETING = "meeting"
    FOLLOW_UP = "follow_up"
    TREATMENT = "treatment"
    INTERNAL = "internal"


class NoteBase(BaseModel):
    lead_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    note_type: NoteType = NoteType.GENERAL
    is_internal: bool = False  # Internal notes not visible to patient
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None


class NoteCreate(NoteBase):
    clinic_id: str
    created_by: str  # User ID


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    note_type: Optional[NoteType] = None
    is_internal: Optional[bool] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None


class Note(NoteBase):
    id: str
    clinic_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
