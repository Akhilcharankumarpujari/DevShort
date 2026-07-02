from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.utils.auth import get_current_admin_user

router = APIRouter(dependencies=[Depends(get_current_admin_user)])

@router.get("/notifications", response_model=List[NotificationResponse])
def get_all_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.created_at.desc()).all()

@router.get("/failed-notifications", response_model=List[NotificationResponse])
def get_failed_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.status == "FAILED").order_by(Notification.created_at.desc()).all()
