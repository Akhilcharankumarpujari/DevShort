from fastapi import FastAPI, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.config import settings
from app.database import get_db
from app.middleware import setup_logging, LoggingAndMetricsMiddleware
from app.routes import auth, users

# Initialize logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(LoggingAndMetricsMiddleware, service_name="user-service")

# Register routers under prefix /api/v1/users
app.include_router(auth.router, prefix="/api/v1/users", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["User Profile"])

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "user-service",
            "version": "1.0.0",
            "database": "connected",
            "dependencies": {}
        }
    except Exception as e:
        return Response(
            status_code=500,
            content=f'{{"status": "unhealthy", "service": "user-service", "version": "1.0.0", "database": "disconnected: {str(e)}", "dependencies": {{}}}}',
            media_type="application/json"
        )

from prometheus_fastapi_instrumentator import Instrumentator

# Initialize Prometheus Instrumentator
Instrumentator().instrument(app).expose(app)
