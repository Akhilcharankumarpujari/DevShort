from fastapi import FastAPI, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.config import settings
from app.database import get_db, SessionLocal
from app.middleware import setup_logging, LoggingAndMetricsMiddleware
from app.routes import public, admin
from app.utils.seed import seed_database

# Initialize logging
setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(LoggingAndMetricsMiddleware, service_name="movie-service")

# Mount public endpoints under /api/v1 and admin endpoints under /api/v1/admin
app.include_router(public.router, prefix="/api/v1", tags=["Public Movie APIs"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Movie APIs"])

@app.on_event("startup")
def startup_event():
    # Trigger database seeding if tables are empty
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        import logging
        logging.error(f"Error seeding database: {str(e)}", exc_info=True)
    finally:
        db.close()

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "movie-service",
            "version": "1.0.0",
            "database": "connected",
            "dependencies": {}
        }
    except Exception as e:
        return Response(
            status_code=500,
            content=f'{{"status": "unhealthy", "service": "movie-service", "version": "1.0.0", "database": "disconnected: {str(e)}", "dependencies": {{}}}}',
            media_type="application/json"
        )

from prometheus_fastapi_instrumentator import Instrumentator

# Initialize Prometheus Instrumentator
Instrumentator().instrument(app).expose(app)
