from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class SeatRequest(BaseModel):
    seat_number: str = Field(..., min_length=1)
    seat_type: str = "REGULAR"  # REGULAR, PREMIUM, VIP
    seat_price: float = Field(..., gt=0)

class SeatReservationRequest(BaseModel):
    show_id: str
    movie_id: str
    theatre_id: str
    screen_id: str
    seats: List[SeatRequest] = Field(..., min_length=1)

class SeatLockResponse(BaseModel):
    booking_id: str
    booking_reference: str
    expires_at: datetime
    total_amount: float
    status: str

class BookingConfirmRequest(BaseModel):
    booking_id: str

class BookingCancelRequest(BaseModel):
    booking_id: str

class BookedSeatResponse(BaseModel):
    seat_number: str
    seat_type: str
    seat_price: float

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    id: str
    booking_reference: str
    user_id: str
    movie_id: str
    theatre_id: str
    screen_id: str
    show_id: str
    booking_status: str
    total_amount: float
    payment_status: str
    booked_at: datetime
    updated_at: datetime
    seats: List[BookedSeatResponse]

    class Config:
        from_attributes = True

class BookingHistoryResponse(BaseModel):
    id: int
    booking_id: str
    previous_status: Optional[str]
    new_status: str
    changed_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True
