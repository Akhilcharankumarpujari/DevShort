import httpx
import json
import logging
from fastapi import FastAPI, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.config import settings
from app.database import get_db, SessionLocal
from app.middleware import setup_logging, LoggingAndMetricsMiddleware
from app.routes import notifications, admin
from app.utils.seed import seed_database

# Initialize logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(LoggingAndMetricsMiddleware, service_name="notification-service")

# Mount routes
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["User Notification APIs"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Notification APIs"])

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logging.error(f"Error seeding database: {str(e)}", exc_info=True)
    finally:
        db.close()

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "database": "connected",
        "dependencies": {
            "booking-service": "connected",
            "payment-service": "connected"
        }
    }
    
    # 1. Check Database
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"disconnected: {str(e)}"
        
    # 2. Check Booking Service Connectivity
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.BOOKING_SERVICE_URL}/health", timeout=2.0)
            if res.status_code != 200:
                health_status["dependencies"]["booking-service"] = f"unhealthy (status {res.status_code})"
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["dependencies"]["booking-service"] = f"disconnected: {str(e)}"
        health_status["status"] = "unhealthy"
        
    # 3. Check Payment Service Connectivity
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.PAYMENT_SERVICE_URL}/health", timeout=2.0)
            if res.status_code != 200:
                health_status["dependencies"]["payment-service"] = f"unhealthy (status {res.status_code})"
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["dependencies"]["payment-service"] = f"disconnected: {str(e)}"
        health_status["status"] = "unhealthy"
        
    status_code = 200 if health_status["status"] == "healthy" else 500
    
    return Response(
        status_code=status_code,
        content=json.dumps(health_status),
        media_type="application/json"
    )

from prometheus_fastapi_instrumentator import Instrumentator

# Initialize Prometheus Instrumentator
Instrumentator().instrument(app).expose(app)
