from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    FOLLOW_UP = "follow_up"
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    APPOINTMENT_REMINDER = "appointment_reminder"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    task_type: TaskType = TaskType.OTHER
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: date
    lead_id: Optional[str] = None
    appointment_id: Optional[str] = None


class TaskCreate(TaskBase):
    clinic_id: str
    assigned_to: str  # User ID
    created_by: str  # User ID


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None
    lead_id: Optional[str] = None
    appointment_id: Optional[str] = None
    assigned_to: Optional[str] = None


class Task(TaskBase):
    id: str
    clinic_id: str
    assigned_to: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
