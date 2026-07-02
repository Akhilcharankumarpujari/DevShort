import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_reference = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    movie_id = Column(String(36), nullable=False)
    theatre_id = Column(String(36), nullable=False)
    screen_id = Column(String(36), nullable=False)
    show_id = Column(String(36), nullable=False)
    booking_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, CONFIRMED, CANCELLED, EXPIRED, COMPLETED
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, SUCCESS, FAILED, REFUNDED
    booked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    seats = relationship("BookedSeat", back_populates="booking", cascade="all, delete-orphan")
    histories = relationship("BookingHistory", back_populates="booking", cascade="all, delete-orphan")

class BookedSeat(Base):
    __tablename__ = "booked_seats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    seat_number = Column(String(50), nullable=False)
    seat_type = Column(String(50), nullable=False)  # REGULAR, PREMIUM, VIP
    seat_price = Column(Float, nullable=False)
    
    booking = relationship("Booking", back_populates="seats")

class SeatLock(Base):
    __tablename__ = "seat_locks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    show_id = Column(String(36), nullable=False, index=True)
    seat_number = Column(String(50), nullable=False)
    user_id = Column(String(36), nullable=False)
    locked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="LOCKED")  # LOCKED, RELEASED, CONFIRMED
    
class BookingHistory(Base):
    __tablename__ = "booking_histories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String(255), nullable=True)
    
    booking = relationship("Booking", back_populates="histories")
