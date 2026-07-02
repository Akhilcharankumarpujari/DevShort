from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.payment import Payment, Refund
from app.schemas.payment import PaymentResponse, RefundResponse
from app.utils.auth import get_current_admin_user

router = APIRouter(dependencies=[Depends(get_current_admin_user)])

@router.get("/payments", response_model=List[PaymentResponse])
def get_all_payments(db: Session = Depends(get_db)):
    return db.query(Payment).order_by(Payment.created_at.desc()).all()

@router.get("/payments/{id}", response_model=PaymentResponse)
def get_payment_details_by_id(id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment

@router.get("/refunds", response_model=List[RefundResponse])
def get_all_refunds(db: Session = Depends(get_db)):
    return db.query(Refund).order_by(Refund.created_at.desc()).all()
