import pytest
from pydantic import ValidationError
from app.schemas.notification import NotificationSendRequest

def test_notification_schema_validation():
    # Valid send request
    req = NotificationSendRequest(
        booking_reference="CINE-001",
        user_id="user-123",
        notification_type="Booking Confirmation",
        channel="EMAIL",
        subject="Your booking",
        message="Your tickets are confirmed"
    )
    assert req.channel == "EMAIL"

    # Empty subject should fail
    with pytest.raises(ValidationError):
        NotificationSendRequest(
            booking_reference="CINE-001",
            user_id="user-123",
            notification_type="Booking Confirmation",
            channel="EMAIL",
            subject="",
            message="Your tickets are confirmed"
        )

    # Empty message should fail
    with pytest.raises(ValidationError):
        NotificationSendRequest(
            booking_reference="CINE-001",
            user_id="user-123",
            notification_type="Booking Confirmation",
            channel="EMAIL",
            subject="Your booking",
            message=""
        )
