import uuid
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(String(1000), nullable=True)
    genre = Column(String(100), nullable=True)
    language = Column(String(100), nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    release_date = Column(Date, nullable=True)
    rating = Column(Float, nullable=True, default=0.0)
    poster_url = Column(String(512), nullable=True)
    trailer_url = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False, default="NOW_SHOWING")  # NOW_SHOWING / COMING_SOON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    shows = relationship("Show", back_populates="movie", cascade="all, delete-orphan")

class Theatre(Base):
    __tablename__ = "theatres"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    screens = relationship("Screen", back_populates="theatre", cascade="all, delete-orphan")

class Screen(Base):
    __tablename__ = "screens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    theatre_id = Column(String(36), ForeignKey("theatres.id", ondelete="CASCADE"), nullable=False)
    screen_name = Column(String(100), nullable=False)
    total_seats = Column(Integer, nullable=False)
    
    theatre = relationship("Theatre", back_populates="screens")
    shows = relationship("Show", back_populates="screen", cascade="all, delete-orphan")

class Show(Base):
    __tablename__ = "shows"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    movie_id = Column(String(36), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    screen_id = Column(String(36), ForeignKey("screens.id", ondelete="CASCADE"), nullable=False)
    show_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    ticket_price = Column(Float, nullable=False)
    available_seats = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, CANCELLED
    
    movie = relationship("Movie", back_populates="shows")
    screen = relationship("Screen", back_populates="shows")
