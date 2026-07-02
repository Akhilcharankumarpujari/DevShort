from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationHistory
from datetime import datetime, timedelta

def seed_database(db: Session):
    if db.query(Notification).first() is not None:
        return
        
    print("Seeding notifications...")
    # 1. Seed successful notification
    notif1 = Notification(
        id="mock-notif-id-1",
        notification_reference="NOTIF-20260630-00001",
        user_id="mock-user-id-1",
        booking_reference="CINE-20260630-00001",
        notification_type="Booking Confirmation",
        channel="EMAIL",
        subject="Your CineOps Ticket Booking is Confirmed!",
        message="Hi User, your tickets for Interstellar have been confirmed successfully. Booking reference: CINE-20260630-00001",
        status="SENT",
        retry_count=0,
        delivered_at=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(notif1)
    
    # 2. Seed failed notification
    notif2 = Notification(
        id="mock-notif-id-2",
        notification_reference="NOTIF-20260630-00002",
        user_id="mock-user-id-1",
        booking_reference="CINE-20260630-00002",
        notification_type="Payment Failure",
        channel="SMS",
        subject="Payment Failed for Booking CINE-20260630-00002",
        message="Payment for your show was declined. Your seats have been released.",
        status="FAILED",
        retry_count=3
    )
    db.add(notif2)
    db.commit()
    
    # Histories
    hist1 = NotificationHistory(notification_id=notif1.id, previous_status=None, new_status="PENDING", remarks="Notification request initialized")
    hist2 = NotificationHistory(notification_id=notif1.id, previous_status="PENDING", new_status="SENT", remarks="Notification delivered successfully via mock EMAIL channel")
    
    hist3 = NotificationHistory(notification_id=notif2.id, previous_status=None, new_status="PENDING", remarks="Notification request initialized")
    hist4 = NotificationHistory(notification_id=notif2.id, previous_status="PENDING", new_status="RETRYING", remarks="Simulated channel error. Auto-retry attempt 1/3")
    hist5 = NotificationHistory(notification_id=notif2.id, previous_status="RETRYING", new_status="RETRYING", remarks="Simulated channel error. Auto-retry attempt 2/3")
    hist6 = NotificationHistory(notification_id=notif2.id, previous_status="RETRYING", new_status="RETRYING", remarks="Simulated channel error. Auto-retry attempt 3/3")
    hist7 = NotificationHistory(notification_id=notif2.id, previous_status="RETRYING", new_status="FAILED", remarks="Notification failed after maximum 3 auto-retry attempts")
    
    db.add_all([hist1, hist2, hist3, hist4, hist5, hist6, hist7])
    db.commit()
    print("Notifications seeded successfully.")
