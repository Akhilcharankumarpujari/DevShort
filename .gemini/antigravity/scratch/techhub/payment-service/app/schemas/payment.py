from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    payment_method: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0.0)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    idempotency_key: str = Field(..., min_length=10, max_length=100)

class ConfirmPayment(BaseModel):
    simulate_success: bool = Field(default=True)

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    transaction_id: Optional[str]
    payment_method: str
    amount: float
    currency: str
    status: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
