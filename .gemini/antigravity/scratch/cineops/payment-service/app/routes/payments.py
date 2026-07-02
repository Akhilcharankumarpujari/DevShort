from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import json
import logging
from typing import List

from app.database import get_db
from app.models.payment import Payment, Refund, PaymentHistory
from app.schemas.payment import (
    PaymentCreateRequest, PaymentConfirmRequest, PaymentFailRequest,
    RefundCreateRequest, PaymentResponse, RefundResponse, PaymentHistoryResponse
)
from app.utils.auth import get_current_user
from app.utils.booking_client import get_booking_details, confirm_booking, cancel_booking
from app.utils.metrics import (
    payments_total, payment_success_total, payment_failure_total,
    refunds_total, payment_duration_seconds
)

router = APIRouter()

def generate_reference(prefix: str) -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = str(uuid.uuid4().hex[:6]).upper()
    return f"{prefix}-{date_str}-{unique_suffix}"

@router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(req: PaymentCreateRequest, response: Response, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    payments_total.inc()

    # 1. Idempotency Check
    existing = db.query(Payment).filter(
        Payment.booking_id == req.booking_id,
        Payment.payment_status.in_(["PENDING", "PROCESSING", "SUCCESS"])
    ).first()
    if existing:
        response.status_code = status.HTTP_200_OK
        return existing

    # 2. REST check with Booking Service
    booking = await get_booking_details(req.booking_id, user_id)
    if not booking:
        payment_failure_total.inc()
        raise HTTPException(status_code=404, detail="Booking not found in Booking Service")

    if booking["booking_status"] not in ["PENDING"]:
        payment_failure_total.inc()
        raise HTTPException(
            status_code=400,
            detail=f"Booking is in {booking['booking_status']} status, payments only allowed for PENDING bookings"
        )

    # Validate price matches booking amount
    if abs(booking["total_amount"] - req.amount) > 0.01:
        payment_failure_total.inc()
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount {req.amount} does not match booking total {booking['total_amount']}"
        )

    # 3. Create Payment record
    ref = generate_reference("PAY")
    new_payment = Payment(
        id=str(uuid.uuid4()),
        payment_reference=ref,
        booking_reference=req.booking_reference,
        booking_id=req.booking_id,
        user_id=user_id,
        amount=req.amount,
        currency=req.currency,
        payment_method=req.payment_method,
        payment_status="PENDING"
    )
    db.add(new_payment)
    db.commit()

    # History
    history = PaymentHistory(
        payment_id=new_payment.id,
        previous_status=None,
        new_status="PENDING",
        remarks="Payment intent initialized"
    )
    db.add(history)
    db.commit()
    db.refresh(new_payment)

    return new_payment

@router.post("/confirm", response_model=PaymentResponse)
async def confirm_payment(req: PaymentConfirmRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    payment = db.query(Payment).filter(Payment.id == req.payment_id, Payment.user_id == user_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    if payment.payment_status == "SUCCESS":
        return payment
        
    if payment.payment_status not in ["PENDING", "PROCESSING"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm payment in {payment.payment_status} status"
        )

    # Simulating successful gateway confirmation
    previous = payment.payment_status
    payment.payment_status = "SUCCESS"
    payment.transaction_id = generate_reference("TXN")
    payment.gateway_response = json.dumps({
        "status": "captured",
        "gateway": "MockGateway",
        "card_brand": "Visa",
        "card_last4": "1111",
        "captured_at": datetime.utcnow().isoformat()
    })

    # Call Booking Service to confirm booking
    confirmed = await confirm_booking(payment.booking_id, user_id)
    if not confirmed:
        logging.error(f"Failed to update booking status in booking-service for booking {payment.booking_id}")

    # History
    history = PaymentHistory(
        payment_id=payment.id,
        previous_status=previous,
        new_status="SUCCESS",
        remarks="Payment successfully authorized and captured"
    )
    db.add(history)
    db.commit()
    db.refresh(payment)

    # Metrics
    payment_success_total.inc()
    duration = (datetime.utcnow() - payment.created_at).total_seconds()
    payment_duration_seconds.observe(duration)

    return payment

@router.post("/fail", response_model=PaymentResponse)
async def fail_payment(req: PaymentFailRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    payment = db.query(Payment).filter(Payment.id == req.payment_id, Payment.user_id == user_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    if payment.payment_status == "FAILED":
        return payment

    if payment.payment_status not in ["PENDING", "PROCESSING"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot fail payment in {payment.payment_status} status"
        )

    previous = payment.payment_status
    payment.payment_status = "FAILED"
    payment.gateway_response = json.dumps({
        "status": "failed",
        "gateway": "MockGateway",
        "error_code": "INSUFFICIENT_FUNDS",
        "error_message": "Transaction declined by issuing bank",
        "failed_at": datetime.utcnow().isoformat()
    })

    # Call Booking Service to cancel booking
    cancelled = await cancel_booking(payment.booking_id, user_id)
    if not cancelled:
        logging.error(f"Failed to cancel booking status in booking-service for booking {payment.booking_id}")

    # History
    history = PaymentHistory(
        payment_id=payment.id,
        previous_status=previous,
        new_status="FAILED",
        remarks="Payment failed: INSUFFICIENT_FUNDS"
    )
    db.add(history)
    db.commit()
    db.refresh(payment)

    # Metrics
    payment_failure_total.inc()

    return payment

@router.post("/refund", response_model=RefundResponse)
async def refund_payment(req: RefundCreateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    payment = db.query(Payment).filter(Payment.id == req.payment_id, Payment.user_id == user_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    if payment.payment_status != "SUCCESS":
        raise HTTPException(status_code=400, detail="Only successful payments can be refunded")

    # Idempotent check: check if already refunded
    existing_refund = db.query(Refund).filter(Refund.payment_id == req.payment_id).first()
    if existing_refund:
        return existing_refund

    # 1. Update Payment Status
    previous = payment.payment_status
    payment.payment_status = "REFUNDED"

    # 2. Create Refund record
    ref = generate_reference("REF")
    refund = Refund(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        refund_reference=ref,
        refund_amount=req.refund_amount,
        refund_reason=req.refund_reason,
        refund_status="SUCCESS"
    )
    db.add(refund)

    # 3. Call Booking Service to refund/cancel booking
    cancelled = await cancel_booking(payment.booking_id, user_id)
    if not cancelled:
        logging.error(f"Failed to cancel/refund booking in booking-service for booking {payment.booking_id}")

    # History
    history = PaymentHistory(
        payment_id=payment.id,
        previous_status=previous,
        new_status="REFUNDED",
        remarks=f"Payment refunded. Reason: {req.refund_reason}"
    )
    db.add(history)
    db.commit()
    db.refresh(refund)

    # Metrics
    refunds_total.inc()

    return refund

@router.get("/history", response_model=List[PaymentHistoryResponse])
def get_user_payment_history(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    return db.query(PaymentHistory).join(Payment).filter(Payment.user_id == user_id).order_by(PaymentHistory.changed_at.desc()).all()

@router.get("/{id}", response_model=PaymentResponse)
def get_payment_by_id(id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    payment = db.query(Payment).filter(Payment.id == id, Payment.user_id == user_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment
