from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class NotificationSendRequest(BaseModel):
    booking_reference: str
    user_id: str
    notification_type: str  # Booking Confirmation, Booking Cancellation, Payment Success, Payment Failure, Refund Confirmation, Booking Reminder, Show Reminder
    channel: str = "EMAIL"  # EMAIL, SMS, PUSH
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

class NotificationRetryRequest(BaseModel):
    notification_id: str

class NotificationResponse(BaseModel):
    id: str
    notification_reference: str
    user_id: str
    booking_reference: str
    notification_type: str
    channel: str
    subject: str
    message: str
    status: str
    retry_count: int
    created_at: datetime
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationHistoryResponse(BaseModel):
    id: int
    notification_id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_at: datetime
    remarks: Optional[str] = None

    class Config:
        from_attributes = True
