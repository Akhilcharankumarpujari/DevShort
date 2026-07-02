import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_reference = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    booking_reference = Column(String(100), index=True, nullable=False)
    notification_type = Column(String(50), nullable=False)  # Booking Confirmation, Booking Cancellation, Payment Success, Payment Failure, Refund Confirmation, Booking Reminder, Show Reminder
    channel = Column(String(20), nullable=False)  # EMAIL, SMS, PUSH
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, SENT, FAILED, RETRYING
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    
    histories = relationship("NotificationHistory", back_populates="notification", cascade="all, delete-orphan")

class NotificationHistory(Base):
    __tablename__ = "notification_histories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    notification_id = Column(String(36), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remarks = Column(String(255), nullable=True)
    
    notification = relationship("Notification", back_populates="histories")
