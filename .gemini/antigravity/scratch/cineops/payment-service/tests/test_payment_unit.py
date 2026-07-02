import pytest
from pydantic import ValidationError
from app.schemas.payment import PaymentCreateRequest, RefundCreateRequest

def test_payment_amount_validation():
    # Valid amount
    req = PaymentCreateRequest(
        booking_id="mock-booking-id",
        booking_reference="CINE-001",
        amount=100.0
    )
    assert req.amount == 100.0

    # Negative amount should raise ValidationError
    with pytest.raises(ValidationError):
        PaymentCreateRequest(
            booking_id="mock-booking-id",
            booking_reference="CINE-001",
            amount=-5.0
        )

    # Zero amount should raise ValidationError
    with pytest.raises(ValidationError):
        PaymentCreateRequest(
            booking_id="mock-booking-id",
            booking_reference="CINE-001",
            amount=0.0
        )

def test_refund_amount_validation():
    # Negative refund amount should raise ValidationError
    with pytest.raises(ValidationError):
        RefundCreateRequest(
            payment_id="mock-payment-id",
            refund_amount=-20.0
        )
