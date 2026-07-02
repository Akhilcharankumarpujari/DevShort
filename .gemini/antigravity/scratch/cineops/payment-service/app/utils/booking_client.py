import os
import jwt
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config import settings

SECRET_KEY = os.getenv("JWT_SECRET", "cineops-super-secure-jwt-secret-key-change-in-prod")
ALGORITHM = "HS256"

def generate_user_jwt(user_id: str, role: str = "USER") -> str:
    payload = {
        "sub": user_id,
        "email": f"{user_id}@cineops.internal",
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=5)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_booking_details(booking_id: str, user_id: str) -> Optional[dict]:
    token = generate_user_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{settings.BOOKING_SERVICE_URL}/api/v1/bookings/{booking_id}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, headers=headers, timeout=5.0)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            logging.error(f"Error fetching booking {booking_id}: {str(e)}")
            return None

async def confirm_booking(booking_id: str, user_id: str) -> bool:
    token = generate_user_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{settings.BOOKING_SERVICE_URL}/api/v1/bookings/confirm"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json={"booking_id": booking_id}, headers=headers, timeout=5.0)
            return res.status_code == 200
        except Exception as e:
            logging.error(f"Error confirming booking {booking_id}: {str(e)}")
            return False

async def cancel_booking(booking_id: str, user_id: str) -> bool:
    token = generate_user_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{settings.BOOKING_SERVICE_URL}/api/v1/bookings/cancel"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json={"booking_id": booking_id}, headers=headers, timeout=5.0)
            return res.status_code == 200
        except Exception as e:
            logging.error(f"Error cancelling booking {booking_id}: {str(e)}")
            return False
