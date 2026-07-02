import os
import jwt
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.config import settings

SECRET_KEY = os.getenv("JWT_SECRET", "cineops-super-secure-jwt-secret-key-change-in-prod")
ALGORITHM = "HS256"

def generate_service_token() -> str:
    payload = {
        "sub": "booking-service",
        "email": "booking-service@cineops.internal",
        "role": "ADMIN",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_show_details(show_id: str) -> Optional[dict]:
    # Public route, doesn't require admin token
    url = f"{settings.MOVIE_SERVICE_URL}/api/v1/shows/{show_id}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=5.0)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            logging.error(f"Error fetching show {show_id}: {str(e)}")
            return None

async def get_movie_details(movie_id: str) -> Optional[dict]:
    url = f"{settings.MOVIE_SERVICE_URL}/api/v1/movies/{movie_id}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=5.0)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            logging.error(f"Error fetching movie {movie_id}: {str(e)}")
            return None

async def update_show_seats(show_id: str, change: int) -> bool:
    # Requires service-to-service admin authorization to hit admin route
    show = await get_show_details(show_id)
    if not show:
        return False
        
    current_seats = show.get("available_seats", 0)
    new_seats = current_seats + change
    
    url = f"{settings.MOVIE_SERVICE_URL}/api/v1/admin/shows/{show_id}"
    token = generate_service_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.put(url, json={"available_seats": new_seats}, headers=headers, timeout=5.0)
            return res.status_code == 200
        except Exception as e:
            logging.error(f"Error updating show {show_id} seats: {str(e)}")
            return False
