import pytest
from datetime import date, datetime, timedelta
from pydantic import ValidationError
from app.schemas.movie import MovieCreate, ShowCreate

def test_movie_duration_validation():
    # Valid movie
    movie = MovieCreate(
        title="Valid Movie",
        duration_minutes=120,
        genre="Action",
        language="English"
    )
    assert movie.duration_minutes == 120

    # Negative duration should fail
    with pytest.raises(ValidationError):
        MovieCreate(
            title="Invalid Movie",
            duration_minutes=-10,
            genre="Action",
            language="English"
        )

def test_show_price_validation():
    start = datetime.now()
    end = start + timedelta(hours=2)
    
    # Negative ticket price should fail
    with pytest.raises(ValidationError):
        ShowCreate(
            movie_id="movie_id",
            screen_id="screen_id",
            show_date=date.today(),
            start_time=start,
            end_time=end,
            ticket_price=-5.0
        )

def test_show_time_validation():
    start = datetime.now()
    # End time is equal to start time -> invalid
    with pytest.raises(ValidationError):
        ShowCreate(
            movie_id="movie_id",
            screen_id="screen_id",
            show_date=date.today(),
            start_time=start,
            end_time=start,
            ticket_price=150.0
        )

    # End time is before start time -> invalid
    with pytest.raises(ValidationError):
        ShowCreate(
            movie_id="movie_id",
            screen_id="screen_id",
            show_date=date.today(),
            start_time=start,
            end_time=start - timedelta(hours=1),
            ticket_price=150.0
        )
