from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class PaymentCreateRequest(BaseModel):
    booking_id: str
    booking_reference: str
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    payment_method: str = "CARD"  # CARD, UPI, NETBANKING

class PaymentConfirmRequest(BaseModel):
    payment_id: str

class PaymentFailRequest(BaseModel):
    payment_id: str

class RefundCreateRequest(BaseModel):
    payment_id: str
    refund_amount: float = Field(..., gt=0)
    refund_reason: str = "User requested refund"

class PaymentResponse(BaseModel):
    id: str
    payment_reference: str
    booking_reference: str
    booking_id: str
    user_id: str
    amount: float
    currency: str
    payment_method: str
    payment_status: str
    transaction_id: Optional[str] = None
    gateway_response: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RefundResponse(BaseModel):
    id: str
    payment_id: str
    refund_reference: str
    refund_amount: float
    refund_reason: Optional[str] = None
    refund_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentHistoryResponse(BaseModel):
    id: int
    payment_id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_at: datetime
    remarks: Optional[str] = None

    class Config:
        from_attributes = True
