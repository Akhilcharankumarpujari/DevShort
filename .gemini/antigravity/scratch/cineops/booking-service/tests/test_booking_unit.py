import pytest
import re
from datetime import datetime, timedelta
from pydantic import ValidationError
from app.routes.bookings import generate_booking_reference
from app.schemas.booking import SeatRequest

def test_booking_reference_format():
    ref = generate_booking_reference()
    # Matches pattern CINE-YYYYMMDD-[A-Z0-9]{6}
    pattern = r"^CINE-\d{8}-[A-Z0-9]{6}$"
    assert re.match(pattern, ref) is not None

def test_seat_price_validation():
    # Valid seat price
    seat = SeatRequest(seat_number="A1", seat_price=200.0)
    assert seat.seat_price == 200.0

    # Negative price should raise ValidationError
    with pytest.raises(ValidationError):
        SeatRequest(seat_number="A1", seat_price=-50.0)

    # Zero price should raise ValidationError
    with pytest.raises(ValidationError):
        SeatRequest(seat_number="A1", seat_price=0.0)
