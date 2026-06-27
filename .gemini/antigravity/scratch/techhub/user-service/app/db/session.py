from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        # Lazy initialization so import works even if DB driver (psycopg2) is missing
        # (e.g. during local tests using SQLite overrides)
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600
        )
    return _engine

def get_db():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
