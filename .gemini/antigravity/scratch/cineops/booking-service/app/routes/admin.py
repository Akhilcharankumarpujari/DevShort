from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.booking import Booking, BookingHistory, SeatLock
from app.schemas.booking import BookingResponse
from app.utils.auth import get_current_admin_user
from app.utils.movie_client import update_show_seats

router = APIRouter(dependencies=[Depends(get_current_admin_user)])

@router.get("/bookings", response_model=List[BookingResponse])
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).order_by(Booking.booked_at.desc()).all()

@router.put("/bookings/{id}/status", response_model=BookingResponse)
async def update_booking_status(id: str, new_status: str, reason: Optional[str] = None, db: Session = Depends(get_db)):
    # Validate status choice
    valid_statuses = ["PENDING", "CONFIRMED", "CANCELLED", "EXPIRED", "COMPLETED"]
    new_status = new_status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
        
    booking = db.query(Booking).filter(Booking.id == id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.booking_status == new_status:
        return booking

    previous = booking.booking_status
    booking.booking_status = new_status
    
    # If transitioning to CANCELLED or EXPIRED from PENDING/CONFIRMED, release seats in Movie Service
    if new_status in ["CANCELLED", "EXPIRED"] and previous in ["PENDING", "CONFIRMED"]:
        # Release locks
        locks = db.query(SeatLock).filter(
            SeatLock.show_id == booking.show_id,
            SeatLock.user_id == booking.user_id,
            SeatLock.status.in_(["LOCKED", "CONFIRMED"])
        ).all()
        for lock in locks:
            lock.status = "RELEASED"
            
        # Restore seat count in Movie Service
        num_seats = len(booking.seats)
        await update_show_seats(booking.show_id, +num_seats)

    # Write History
    history = BookingHistory(
        booking_id=booking.id,
        previous_status=previous,
        new_status=new_status,
        reason=reason or f"Admin updated status from {previous} to {new_status}"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    return booking

@router.delete("/bookings/{id}", status_code=status.HTTP_200_OK)
def delete_booking(id: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Release locks before deleting
    locks = db.query(SeatLock).filter(
        SeatLock.show_id == booking.show_id,
        SeatLock.user_id == booking.user_id,
        SeatLock.status.in_(["LOCKED", "CONFIRMED"])
    ).all()
    for lock in locks:
        lock.status = "RELEASED"

    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted successfully"}
