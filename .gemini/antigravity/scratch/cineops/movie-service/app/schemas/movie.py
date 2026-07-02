from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import Optional, List

# Movie Schemas
class MovieBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    duration_minutes: int = Field(..., gt=0)
    release_date: Optional[date] = None
    rating: Optional[float] = Field(0.0, ge=0.0, le=10.0)
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    status: Optional[str] = "NOW_SHOWING"  # NOW_SHOWING or COMING_SOON

class MovieCreate(MovieBase):
    pass

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    release_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    status: Optional[str] = None

class MovieResponse(MovieBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Theatre Schemas
class TheatreBase(BaseModel):
    name: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    address: Optional[str] = None

class TheatreCreate(TheatreBase):
    pass

class TheatreUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None

class TheatreResponse(TheatreBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Screen Schemas
class ScreenBase(BaseModel):
    theatre_id: str
    screen_name: str = Field(..., min_length=1)
    total_seats: int = Field(..., gt=0)

class ScreenCreate(ScreenBase):
    pass

class ScreenUpdate(BaseModel):
    theatre_id: Optional[str] = None
    screen_name: Optional[str] = None
    total_seats: Optional[int] = Field(None, gt=0)

class ScreenResponse(ScreenBase):
    id: str

    class Config:
        from_attributes = True

# Show Schemas
class ShowBase(BaseModel):
    movie_id: str
    screen_id: str
    show_date: date
    start_time: datetime
    end_time: datetime
    ticket_price: float = Field(..., gt=0)
    available_seats: Optional[int] = None
    status: Optional[str] = "ACTIVE"  # ACTIVE or CANCELLED

class ShowCreate(ShowBase):
    @model_validator(mode="after")
    def validate_times(self) -> 'ShowCreate':
        if self.end_time <= self.start_time:
            raise ValueError("Show end_time must be strictly after start_time")
        return self

class ShowUpdate(BaseModel):
    movie_id: Optional[str] = None
    screen_id: Optional[str] = None
    show_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    ticket_price: Optional[float] = Field(None, gt=0)
    available_seats: Optional[int] = None
    status: Optional[str] = None

    @model_validator(mode="after")
    def validate_times(self) -> 'ShowUpdate':
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("Show end_time must be strictly after start_time")
        return self

class ShowResponse(ShowBase):
    id: str

    class Config:
        from_attributes = True
