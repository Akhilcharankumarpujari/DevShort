from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import logging
from typing import List

from app.database import get_db
from app.models.booking import Booking, BookedSeat, SeatLock, BookingHistory
from app.schemas.booking import (
    SeatReservationRequest, SeatLockResponse,
    BookingConfirmRequest, BookingCancelRequest,
    BookingResponse, BookingHistoryResponse
)
from app.utils.auth import get_current_user
from app.utils.movie_client import get_show_details, update_show_seats
from app.utils.metrics import (
    bookings_total, booking_success_total, booking_failure_total,
    booking_cancellation_total, seat_locks_total, booking_time_seconds
)

router = APIRouter()

def generate_booking_reference() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = str(uuid.uuid4().hex[:6]).upper()
    return f"CINE-{date_str}-{unique_suffix}"

def cleanup_expired_locks(db: Session):
    now = datetime.utcnow()
    expired_locks = db.query(SeatLock).filter(
        SeatLock.status == "LOCKED",
        SeatLock.expires_at < now
    ).all()
    for lock in expired_locks:
        lock.status = "RELEASED"
    db.commit()

    limit_time = now - timedelta(minutes=5)
    pending_bookings = db.query(Booking).filter(
        Booking.booking_status == "PENDING",
        Booking.booked_at < limit_time
    ).all()
    
    for b in pending_bookings:
        b.booking_status = "EXPIRED"
        
        history = BookingHistory(
            booking_id=b.id,
            previous_status="PENDING",
            new_status="EXPIRED",
            reason="Lock expired after 5 minutes timeout"
        )
        db.add(history)
        
        locks = db.query(SeatLock).filter(
            SeatLock.show_id == b.show_id,
            SeatLock.user_id == b.user_id,
            SeatLock.status == "LOCKED"
        ).all()
        for l in locks:
            l.status = "RELEASED"
            
    db.commit()

@router.post("/lock-seats", response_model=SeatLockResponse, status_code=status.HTTP_201_CREATED)
async def lock_seats(req: SeatReservationRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    cleanup_expired_locks(db)
    
    bookings_total.inc()  # Increment booking attempts

    # 1. Verify show exists in Movie Service
    try:
        show = await get_show_details(req.show_id)
        if not show:
            booking_failure_total.inc()
            raise HTTPException(status_code=404, detail="Show not found in Movie Service")
        
        show_time = datetime.fromisoformat(show["start_time"])
        if show_time < datetime.now():
            booking_failure_total.inc()
            raise HTTPException(status_code=400, detail="Cannot book tickets for a show in the past")
    except HTTPException as he:
        raise he
    except Exception as e:
        booking_failure_total.inc()
        raise HTTPException(status_code=500, detail=f"Error contacting Movie Service: {str(e)}")

    # 2. Check each seat for existing bookings or locks
    requested_seat_numbers = [s.seat_number for s in req.seats]
    
    booked = db.query(BookedSeat.seat_number).join(Booking).filter(
        Booking.show_id == req.show_id,
        Booking.booking_status.in_(["CONFIRMED", "COMPLETED"]),
        BookedSeat.seat_number.in_(requested_seat_numbers)
    ).all()
    if booked:
        booking_failure_total.inc()
        booked_list = [b[0] for b in booked]
        raise HTTPException(
            status_code=400,
            detail=f"Some seats are already booked: {', '.join(booked_list)}"
        )

    locked = db.query(SeatLock.seat_number).filter(
        SeatLock.show_id == req.show_id,
        SeatLock.status == "LOCKED",
        SeatLock.expires_at > datetime.utcnow(),
        SeatLock.seat_number.in_(requested_seat_numbers)
    ).all()
    if locked:
        booking_failure_total.inc()
        locked_list = [l[0] for l in locked]
        raise HTTPException(
            status_code=400,
            detail=f"Some seats are temporarily locked by another user: {', '.join(locked_list)}"
        )

    # 3. Create Seat Locks and Booking entries
    seat_locks_total.inc(len(req.seats))  # Increment seat locks count
    
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    for seat in req.seats:
        lock = SeatLock(
            show_id=req.show_id,
            seat_number=seat.seat_number,
            user_id=user_id,
            expires_at=expires_at,
            status="LOCKED"
        )
        db.add(lock)

    total_amount = sum(s.seat_price for s in req.seats)
    ref = generate_booking_reference()
    
    new_booking = Booking(
        id=str(uuid.uuid4()),
        booking_reference=ref,
        user_id=user_id,
        movie_id=req.movie_id,
        theatre_id=req.theatre_id,
        screen_id=req.screen_id,
        show_id=req.show_id,
        booking_status="PENDING",
        total_amount=total_amount,
        payment_status="PENDING"
    )
    db.add(new_booking)
    db.commit()

    for seat in req.seats:
        booked_seat = BookedSeat(
            booking_id=new_booking.id,
            seat_number=seat.seat_number,
            seat_type=seat.seat_type,
            seat_price=seat.seat_price
        )
        db.add(booked_seat)

    history = BookingHistory(
        booking_id=new_booking.id,
        previous_status=None,
        new_status="PENDING",
        reason="Seat lock initialized, booking pending"
    )
    db.add(history)
    db.commit()

    return {
        "booking_id": new_booking.id,
        "booking_reference": ref,
        "expires_at": expires_at,
        "total_amount": total_amount,
        "status": "PENDING"
    }

@router.post("/confirm", response_model=BookingResponse)
async def confirm_booking(req: BookingConfirmRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    cleanup_expired_locks(db)

    booking = db.query(Booking).filter(Booking.id == req.booking_id, Booking.user_id == user_id).first()
    if not booking:
        booking_failure_total.inc()
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.booking_status == "EXPIRED":
        booking_failure_total.inc()
        raise HTTPException(status_code=400, detail="Lock expired. Please reserve seats again")
    if booking.booking_status != "PENDING":
        booking_failure_total.inc()
        raise HTTPException(status_code=400, detail=f"Booking is already in {booking.booking_status} status")

    previous = booking.booking_status
    booking.booking_status = "CONFIRMED"
    booking.payment_status = "SUCCESS"
    
    locks = db.query(SeatLock).filter(
        SeatLock.show_id == booking.show_id,
        SeatLock.user_id == user_id,
        SeatLock.status == "LOCKED"
    ).all()
    for lock in locks:
        lock.status = "CONFIRMED"

    num_seats = len(booking.seats)
    updated = await update_show_seats(booking.show_id, -num_seats)
    if not updated:
        logging.error(f"Failed to update movie service seat capacity for show {booking.show_id}")

    history = BookingHistory(
        booking_id=booking.id,
        previous_status=previous,
        new_status="CONFIRMED",
        reason="Payment successful, booking confirmed"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    # Track metrics
    booking_success_total.inc()
    duration = (datetime.utcnow() - booking.booked_at).total_seconds()
    booking_time_seconds.observe(duration)

    return booking

@router.post("/cancel", response_model=BookingResponse)
async def cancel_booking(req: BookingCancelRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    booking = db.query(Booking).filter(Booking.id == req.booking_id, Booking.user_id == user_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.booking_status != "CONFIRMED":
        raise HTTPException(status_code=400, detail="Only confirmed bookings can be cancelled")

    previous = booking.booking_status
    booking.booking_status = "CANCELLED"
    booking.payment_status = "REFUNDED"
    
    locks = db.query(SeatLock).filter(
        SeatLock.show_id == booking.show_id,
        SeatLock.user_id == user_id,
        SeatLock.status == "CONFIRMED"
    ).all()
    for lock in locks:
        lock.status = "RELEASED"

    num_seats = len(booking.seats)
    updated = await update_show_seats(booking.show_id, +num_seats)
    if not updated:
        logging.error(f"Failed to restore movie service seat capacity for show {booking.show_id}")

    history = BookingHistory(
        booking_id=booking.id,
        previous_status=previous,
        new_status="CANCELLED",
        reason="User requested cancellation"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    # Track cancellation metrics
    booking_cancellation_total.inc()

    return booking

@router.get("", response_model=List[BookingResponse])
def get_user_bookings(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    cleanup_expired_locks(db)
    return db.query(Booking).filter(Booking.user_id == user_id).order_by(Booking.booked_at.desc()).all()

@router.get("/history", response_model=List[BookingHistoryResponse])
def get_user_booking_history(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    return db.query(BookingHistory).join(Booking).filter(Booking.user_id == user_id).order_by(BookingHistory.changed_at.desc()).all()

@router.get("/{id}", response_model=BookingResponse)
def get_booking_by_id(id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    cleanup_expired_locks(db)
    booking = db.query(Booking).filter(Booking.id == id, Booking.user_id == user_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
