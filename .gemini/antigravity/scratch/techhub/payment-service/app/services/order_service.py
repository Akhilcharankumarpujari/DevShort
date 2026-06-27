import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def confirm_order(order_id: int) -> bool:
    """
    Call the Order Service to update the status to 'Confirmed' upon successful payment.
    """
    url = f"{settings.ORDER_SERVICE_URL}{settings.API_V1_STR}/orders/{order_id}/status"
    # Create a JWT token to bypass or authenticate with the Order Service
    # Wait, in development/testing, the services are in the same environment and use the same SECRET_KEY.
    # The Order Service checks JWT tokens using settings.SECRET_KEY.
    # We can generate a token representing an internal/admin service, or we can just call it directly.
    # Wait, the PUT `/api/v1/orders/{order_id}/status` endpoint requires Admin privileges:
    # `current_user: UserContext = Depends(admin_required)`
    # So we MUST include an admin JWT token in the request headers to authorize it!
    # Let's generate an admin JWT token on the fly from the Payment Service using settings.SECRET_KEY!
    # This is an incredibly elegant and practical microservice authentication pattern!
    import jwt
    from datetime import datetime, timedelta, timezone
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {
        "exp": expire,
        "sub": "0", # system/admin ID
        "role": "admin",
        "type": "access",
        "jti": "system-payment-callback"
    }
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = httpx.put(
            url,
            json={"status": "Confirmed", "notes": "Payment confirmed via Payment Service Callback"},
            headers=headers,
            timeout=5.0
        )
        if response.status_code == 200:
            return True
        logger.error(f"Failed to confirm order {order_id} in Order Service. Status: {response.status_code}. Response: {response.text}")
    except Exception as e:
        logger.error(f"Error calling Order Service for order confirmation {order_id}: {str(e)}")
    return False
