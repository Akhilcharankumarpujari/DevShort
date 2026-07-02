from sqlalchemy.orm import Session
from app.models.payment import Payment, Refund, PaymentHistory
from datetime import datetime, timedelta

def seed_database(db: Session):
    if db.query(Payment).first() is not None:
        return
        
    print("Seeding payments...")
    # 1. Seed successful payment
    payment1 = Payment(
        id="mock-payment-id-1",
        payment_reference="PAY-20260630-00001",
        booking_reference="CINE-20260630-00001",
        booking_id="mock-booking-id-1",
        user_id="mock-user-id-1",
        amount=500.0,
        currency="INR",
        payment_method="CARD",
        payment_status="SUCCESS",
        transaction_id="TXN-20260630-00001",
        gateway_response='{"status": "captured", "gateway": "MockGateway"}'
    )
    db.add(payment1)
    
    # 2. Seed refunded payment
    payment2 = Payment(
        id="mock-payment-id-2",
        payment_reference="PAY-20260630-00002",
        booking_reference="CINE-20260630-00002",
        booking_id="mock-booking-id-2",
        user_id="mock-user-id-1",
        amount=300.0,
        currency="INR",
        payment_method="UPI",
        payment_status="REFUNDED",
        transaction_id="TXN-20260630-00002",
        gateway_response='{"status": "captured", "gateway": "MockGateway"}'
    )
    db.add(payment2)
    db.commit()
    
    # Refund record
    refund = Refund(
        id="mock-refund-id-1",
        payment_id=payment2.id,
        refund_reference="REF-20260630-00001",
        refund_amount=300.0,
        refund_reason="User cancelled booking",
        refund_status="SUCCESS"
    )
    db.add(refund)
    
    # History logs
    hist1 = PaymentHistory(payment_id=payment1.id, previous_status=None, new_status="PENDING", remarks="Payment initialized")
    hist2 = PaymentHistory(payment_id=payment1.id, previous_status="PENDING", new_status="SUCCESS", remarks="Payment authorized")
    
    hist3 = PaymentHistory(payment_id=payment2.id, previous_status=None, new_status="PENDING", remarks="Payment initialized")
    hist4 = PaymentHistory(payment_id=payment2.id, previous_status="PENDING", new_status="SUCCESS", remarks="Payment authorized")
    hist5 = PaymentHistory(payment_id=payment2.id, previous_status="SUCCESS", new_status="REFUNDED", remarks="Payment refunded")
    
    db.add_all([hist1, hist2, hist3, hist4, hist5])
    db.commit()
    print("Payments seeded successfully.")
