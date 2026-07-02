import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_reference = Column(String(100), unique=True, index=True, nullable=False)
    booking_reference = Column(String(100), index=True, nullable=False)
    booking_id = Column(String(36), index=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    payment_method = Column(String(50), nullable=False, default="CARD")  # CARD, UPI, NETBANKING
    payment_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, SUCCESS, FAILED, REFUNDED
    transaction_id = Column(String(100), unique=True, index=True, nullable=True)
    gateway_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")
    histories = relationship("PaymentHistory", back_populates="payment", cascade="all, delete-orphan")

class Refund(Base):
    __tablename__ = "refunds"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    refund_reference = Column(String(100), unique=True, index=True, nullable=False)
    refund_amount = Column(Float, nullable=False)
    refund_reason = Column(String(255), nullable=True)
    refund_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, SUCCESS, FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    payment = relationship("Payment", back_populates="refunds")

class PaymentHistory(Base):
    __tablename__ = "payment_histories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remarks = Column(String(255), nullable=True)
    
    payment = relationship("Payment", back_populates="histories")
