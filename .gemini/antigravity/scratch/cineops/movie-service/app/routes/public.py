from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import Date, and_
from datetime import date
from typing import List, Optional

from app.database import get_db
from app.models.movie import Movie, Theatre, Screen, Show
from app.schemas.movie import MovieResponse, TheatreResponse, ShowResponse

router = APIRouter()

@router.get("/movies", response_model=List[MovieResponse])
def get_movies(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    city: Optional[str] = None,
    theatre_id: Optional[str] = None,
    show_date: Optional[date] = None,
    sort_by: Optional[str] = "title",
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Movie)

    # Perform joins if filters require it
    has_show_join = False
    has_screen_join = False
    has_theatre_join = False

    # Apply filters
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))
    if genre:
        query = query.filter(Movie.genre.ilike(f"%{genre}%"))
    if language:
        query = query.filter(Movie.language.ilike(f"%{language}%"))

    if show_date:
        query = query.join(Show)
        has_show_join = True
        query = query.filter(Show.show_date == show_date)

    if theatre_id:
        if not has_show_join:
            query = query.join(Show)
            has_show_join = True
        query = query.join(Screen)
        has_screen_join = True
        query = query.filter(Screen.theatre_id == theatre_id)

    if city:
        if not has_show_join:
            query = query.join(Show)
            has_show_join = True
        if not has_screen_join:
            query = query.join(Screen)
            has_screen_join = True
        query = query.join(Theatre)
        has_theatre_join = True
        query = query.filter(Theatre.city.ilike(city))

    # Apply distinct to prevent duplicate movie objects when joining
    if has_show_join or has_screen_join or has_theatre_join:
        query = query.distinct()

    # Apply sorting
    if sort_by == "rating":
        query = query.order_by(Movie.rating.desc())
    elif sort_by == "release_date":
        query = query.order_by(Movie.release_date.desc())
    else:
        query = query.order_by(Movie.title.asc())

    return query.limit(limit).offset(offset).all()

@router.get("/movies/search", response_model=List[MovieResponse])
def search_movies(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return db.query(Movie).filter(Movie.title.ilike(f"%{q}%")).all()

@router.get("/movies/now-showing", response_model=List[MovieResponse])
def get_now_showing(db: Session = Depends(get_db)):
    return db.query(Movie).filter(Movie.status == "NOW_SHOWING").all()

@router.get("/movies/coming-soon", response_model=List[MovieResponse])
def get_coming_soon(db: Session = Depends(get_db)):
    return db.query(Movie).filter(Movie.status == "COMING_SOON").all()

@router.get("/movies/{id}", response_model=MovieResponse)
def get_movie_by_id(id: str, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@router.get("/theatres", response_model=List[TheatreResponse])
def get_theatres(city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Theatre)
    if city:
        query = query.filter(Theatre.city.ilike(city))
    return query.all()

@router.get("/shows", response_model=List[ShowResponse])
def get_shows(
    movie_id: Optional[str] = None,
    screen_id: Optional[str] = None,
    show_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Show)
    if movie_id:
        query = query.filter(Show.movie_id == movie_id)
    if screen_id:
        query = query.filter(Show.screen_id == screen_id)
    if show_date:
        query = query.filter(Show.show_date == show_date)
    return query.all()

@router.get("/shows/{id}", response_model=ShowResponse)
def get_show_by_id(id: str, db: Session = Depends(get_db)):
    show = db.query(Show).filter(Show.id == id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show

@router.get("/cities", response_model=List[str])
def get_cities(db: Session = Depends(get_db)):
    cities = db.query(Theatre.city).distinct().all()
    return [c[0] for c in cities if c[0]]
