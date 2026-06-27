import uuid
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import require_auth, RoleChecker, UserContext
from app.models.payment import Payment
from app.models.history import PaymentHistory
from app.schemas.payment import PaymentCreate, PaymentResponse, ConfirmPayment
from app.schemas.history import PaymentHistoryResponse
from app.services import order_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Role checkers
admin_required = RoleChecker(allowed_roles=["admin"])

def log_payment_history(db: Session, payment_id: int, status: str, notes: Optional[str] = None):
    history = PaymentHistory(
        payment_id=payment_id,
        status=status,
        notes=notes
    )
    db.add(history)

@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    List payments.
    - Admin lists all transactions.
    - Customer lists their own transactions.
    """
    if current_user.role == "admin":
        return db.query(Payment).order_by(Payment.created_at.desc()).all()
    else:
        return db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc()).all()

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_by_id(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Get details of a specific payment.
    - Admin can view any transaction.
    - Customer can only view their own transaction.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
        
    if current_user.role != "admin" and payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this payment")
        
    return payment

@router.get("/{payment_id}/history", response_model=List[PaymentHistoryResponse])
def get_payment_history(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Get event history of a specific payment.
    - Admin can view any payment's history.
    - Customer can only view their own payment's history.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
        
    if current_user.role != "admin" and payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this history")
        
    return db.query(PaymentHistory).filter(PaymentHistory.payment_id == payment_id).order_by(PaymentHistory.id.desc()).all()

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    pay_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Create a new payment intent. Enforces idempotency via 'idempotency_key'.
    """
    # 1. Enforce idempotency
    existing_pay = db.query(Payment).filter(Payment.idempotency_key == pay_in.idempotency_key).first()
    if existing_pay:
        logger.info(f"Duplicate payment request detected for key '{pay_in.idempotency_key}'. Returning existing intent.")
        return existing_pay
        
    payment = Payment(
        order_id=pay_in.order_id,
        user_id=current_user.id,
        payment_method=pay_in.payment_method,
        amount=pay_in.amount,
        currency=pay_in.currency,
        idempotency_key=pay_in.idempotency_key,
        status="PENDING"
    )
    db.add(payment)
    db.flush() # gets payment.id
    
    log_payment_history(db, payment.id, "PENDING", "Payment intent created")
    db.commit()
    db.refresh(payment)
    return payment

@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    confirm_in: ConfirmPayment,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_auth)
):
    """
    Confirm payment. Simulates success/failure gateways.
    If success, calls Order Service status callback.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
        
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to confirm this payment")
        
    if payment.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot confirm payment in status '{payment.status}'. Only PENDING can be confirmed.")
        
    if confirm_in.simulate_success:
        payment.status = "SUCCESS"
        payment.transaction_id = f"tx_{uuid.uuid4().hex[:12]}"
        log_payment_history(db, payment.id, "SUCCESS", f"Transaction capture success. TxId: {payment.transaction_id}")
        
        # Callback to Order Service
        success = order_service.confirm_order(payment.order_id)
        if not success:
            logger.error(f"Failed to callback Order Service to confirm order {payment.order_id}")
            # In microservices, we still capture the payment success but log/alert the synchronization failure.
    else:
        payment.status = "FAILED"
        log_payment_history(db, payment.id, "FAILED", "Transaction capture failed by gateway simulator")
        
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(admin_required)
):
    """
    Refund a successful payment.
    [Requires Admin Privileges]
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
        
    if payment.status != "SUCCESS":
        raise HTTPException(status_code=400, detail=f"Cannot refund unpaid or failed order. Status: {payment.status}")
        
    payment.status = "REFUNDED"
    log_payment_history(db, payment.id, "REFUNDED", "Payment refunded by administrator")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
