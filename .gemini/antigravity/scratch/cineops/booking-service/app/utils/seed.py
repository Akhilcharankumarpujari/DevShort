from sqlalchemy.orm import Session
from app.models.booking import Booking, BookedSeat, BookingHistory
from datetime import datetime, timedelta

def seed_database(db: Session):
    if db.query(Booking).first() is not None:
        return
        
    print("Seeding bookings...")
    # Seed a couple of mock bookings
    booking1 = Booking(
        id="mock-booking-id-1",
        booking_reference="CINE-20260630-00001",
        user_id="mock-user-id-1",
        movie_id="mock-movie-id-1",
        theatre_id="mock-theatre-id-1",
        screen_id="mock-screen-id-1",
        show_id="mock-show-id-1",
        booking_status="CONFIRMED",
        total_amount=500.0,
        payment_status="SUCCESS",
        booked_at=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(booking1)
    
    booking2 = Booking(
        id="mock-booking-id-2",
        booking_reference="CINE-20260630-00002",
        user_id="mock-user-id-1",
        movie_id="mock-movie-id-2",
        theatre_id="mock-theatre-id-1",
        screen_id="mock-screen-id-2",
        show_id="mock-show-id-2",
        booking_status="CANCELLED",
        total_amount=300.0,
        payment_status="REFUNDED",
        booked_at=datetime.utcnow() - timedelta(days=1)
    )
    db.add(booking2)
    db.commit()
    
    # Booked Seats
    seat1 = BookedSeat(booking_id=booking1.id, seat_number="A1", seat_type="PREMIUM", seat_price=250.0)
    seat2 = BookedSeat(booking_id=booking1.id, seat_number="A2", seat_type="PREMIUM", seat_price=250.0)
    seat3 = BookedSeat(booking_id=booking2.id, seat_number="B5", seat_type="REGULAR", seat_price=300.0)
    db.add_all([seat1, seat2, seat3])
    
    # Histories
    hist1 = BookingHistory(booking_id=booking1.id, previous_status=None, new_status="PENDING", reason="Initial lock")
    hist2 = BookingHistory(booking_id=booking1.id, previous_status="PENDING", new_status="CONFIRMED", reason="Confirmed by user payment")
    hist3 = BookingHistory(booking_id=booking2.id, previous_status=None, new_status="PENDING", reason="Initial lock")
    hist4 = BookingHistory(booking_id=booking2.id, previous_status="PENDING", new_status="CONFIRMED", reason="Confirmed by user payment")
    hist5 = BookingHistory(booking_id=booking2.id, previous_status="CONFIRMED", new_status="CANCELLED", reason="User cancelled booking")
    db.add_all([hist1, hist2, hist3, hist4, hist5])
    db.commit()
    print("Bookings seeded successfully.")
