from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging
from typing import List

from app.database import get_db
from app.models.notification import Notification, NotificationHistory
from app.schemas.notification import (
    NotificationSendRequest, NotificationRetryRequest,
    NotificationResponse, NotificationHistoryResponse
)
from app.utils.auth import get_current_user
from app.utils.metrics import (
    notifications_total, notification_success_total, notification_failure_total,
    notification_retries_total, notification_latency_seconds
)

router = APIRouter()

def generate_reference() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = str(uuid.uuid4().hex[:6]).upper()
    return f"NOTIF-{date_str}-{unique_suffix}"

async def execute_delivery(notif: Notification, db: Session):
    start_time = datetime.utcnow()
    # Check if we should simulate failure
    should_fail = "fail" in notif.subject.lower() or "fail" in notif.message.lower()

    if should_fail:
        # Auto-retry loop (up to 3 times)
        while notif.retry_count < 3:
            prev_status = notif.status
            notif.retry_count += 1
            notif.status = "RETRYING"
            
            history = NotificationHistory(
                notification_id=notif.id,
                previous_status=prev_status,
                new_status="RETRYING",
                remarks=f"Simulated channel error. Auto-retry attempt {notif.retry_count}/3"
            )
            db.add(history)
            db.commit()
            notification_retries_total.inc()
            logging.info(f"Simulated failure: Retry attempt {notif.retry_count} for notification {notif.id}")
            
        # Final permanent failure
        prev_status = notif.status
        notif.status = "FAILED"
        history = NotificationHistory(
            notification_id=notif.id,
            previous_status=prev_status,
            new_status="FAILED",
            remarks="Notification failed after maximum 3 auto-retry attempts"
        )
        db.add(history)
        db.commit()
        notification_failure_total.inc()
        logging.error(f"Notification {notif.id} permanently failed after retries")
    else:
        # Success pathway
        prev_status = notif.status
        notif.status = "SENT"
        notif.delivered_at = datetime.utcnow()
        
        history = NotificationHistory(
            notification_id=notif.id,
            previous_status=prev_status,
            new_status="SENT",
            remarks=f"Notification delivered successfully via mock {notif.channel} channel"
        )
        db.add(history)
        db.commit()
        notification_success_total.inc()
        
        latency = (datetime.utcnow() - start_time).total_seconds()
        notification_latency_seconds.observe(latency)
        logging.info(f"Notification {notif.id} successfully sent")

@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(req: NotificationSendRequest, response: Response, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    notifications_total.inc()

    # 1. Duplicate Prevention
    existing = db.query(Notification).filter(
        Notification.booking_reference == req.booking_reference,
        Notification.user_id == req.user_id,
        Notification.notification_type == req.notification_type
    ).first()
    if existing:
        response.status_code = status.HTTP_200_OK
        return existing

    # 2. Create PENDING notification record
    ref = generate_reference()
    new_notif = Notification(
        id=str(uuid.uuid4()),
        notification_reference=ref,
        user_id=req.user_id,
        booking_reference=req.booking_reference,
        notification_type=req.notification_type,
        channel=req.channel.upper(),
        subject=req.subject,
        message=req.message,
        status="PENDING",
        retry_count=0
    )
    db.add(new_notif)
    db.commit()

    # History
    history = NotificationHistory(
        notification_id=new_notif.id,
        previous_status=None,
        new_status="PENDING",
        remarks="Notification request initialized"
    )
    db.add(history)
    db.commit()

    # 3. Trigger delivery
    await execute_delivery(new_notif, db)
    db.refresh(new_notif)

    return new_notif

@router.post("/retry", response_model=NotificationResponse)
async def retry_notification(req: NotificationRetryRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    notif = db.query(Notification).filter(Notification.id == req.notification_id, Notification.user_id == user_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notif.status != "FAILED":
        raise HTTPException(status_code=400, detail="Only failed notifications can be retried")

    # Reset retry count and mark PENDING
    notif.retry_count = 0
    prev_status = notif.status
    notif.status = "PENDING"
    
    history = NotificationHistory(
        notification_id=notif.id,
        previous_status=prev_status,
        new_status="PENDING",
        remarks="Manual retry initialized by user"
    )
    db.add(history)
    db.commit()

    # Re-trigger delivery
    await execute_delivery(notif, db)
    db.refresh(notif)

    return notif

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

@router.get("/history", response_model=List[NotificationHistoryResponse])
def get_user_notification_history(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    return db.query(NotificationHistory).join(Notification).filter(Notification.user_id == user_id).order_by(NotificationHistory.changed_at.desc()).all()

@router.get("/{id}", response_model=NotificationResponse)
def get_notification_by_id(id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    notif = db.query(Notification).filter(Notification.id == id, Notification.user_id == user_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif
