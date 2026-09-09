from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    DEPOSIT_RECEIVED = "deposit_received"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentType(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    INSURANCE = "insurance"
    FINANCING = "financing"
    OTHER = "other"


class RevenueBase(BaseModel):
    lead_id: str
    clinic_id: str
    treatment_name: str = Field(..., min_length=2, max_length=200)
    treatment_type: Optional[str] = None
    total_amount: float = Field(..., gt=0)
    currency: str = "USD"
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_type: Optional[PaymentType] = None
    deposit_amount: Optional[float] = None
    notes: Optional[str] = None
    invoice_number: Optional[str] = None


class RevenueCreate(RevenueBase):
    appointment_id: Optional[str] = None


class RevenueUpdate(BaseModel):
    treatment_name: Optional[str] = None
    treatment_type: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payment_status: Optional[PaymentStatus] = None
    payment_type: Optional[PaymentType] = None
    deposit_amount: Optional[float] = None
    notes: Optional[str] = None
    invoice_number: Optional[str] = None
    appointment_id: Optional[str] = None


class Payment(BaseModel):
    id: str
    revenue_id: str
    amount: float
    payment_type: PaymentType
    payment_date: datetime
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime


class Revenue(RevenueBase):
    id: str
    appointment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_amount: float = 0.0
    outstanding_amount: float = 0.0
    payments: List[Payment] = []
    created_by: str
    converted_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)