from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from app.database import get_db
from app.models.movie import Movie, Theatre, Screen, Show
from app.schemas.movie import (
    MovieCreate, MovieUpdate, MovieResponse,
    TheatreCreate, TheatreUpdate, TheatreResponse,
    ScreenCreate, ScreenUpdate, ScreenResponse,
    ShowCreate, ShowUpdate, ShowResponse
)
from app.utils.auth import get_current_admin_user

router = APIRouter(dependencies=[Depends(get_current_admin_user)])

# --- Admin Movie APIs ---
@router.post("/movies", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
def create_movie(movie_in: MovieCreate, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.title == movie_in.title).first()
    if db_movie:
        raise HTTPException(status_code=400, detail="Movie title already exists")
    
    new_movie = Movie(**movie_in.model_dump())
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie

@router.put("/movies/{id}", response_model=MovieResponse)
def update_movie(id: str, movie_in: MovieUpdate, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    update_data = movie_in.model_dump(exclude_unset=True)
    
    # Check duplicate title if updating title
    if "title" in update_data and update_data["title"] != db_movie.title:
        title_exists = db.query(Movie).filter(Movie.title == update_data["title"]).first()
        if title_exists:
            raise HTTPException(status_code=400, detail="Movie title already exists")
            
    for key, value in update_data.items():
        setattr(db_movie, key, value)
        
    db.commit()
    db.refresh(db_movie)
    return db_movie

@router.delete("/movies/{id}", status_code=status.HTTP_200_OK)
def delete_movie(id: str, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(db_movie)
    db.commit()
    return {"message": "Movie deleted successfully"}


# --- Admin Theatre APIs ---
@router.post("/theatres", response_model=TheatreResponse, status_code=status.HTTP_201_CREATED)
def create_theatre(theatre_in: TheatreCreate, db: Session = Depends(get_db)):
    new_theatre = Theatre(**theatre_in.model_dump())
    db.add(new_theatre)
    db.commit()
    db.refresh(new_theatre)
    return new_theatre

@router.put("/theatres/{id}", response_model=TheatreResponse)
def update_theatre(id: str, theatre_in: TheatreUpdate, db: Session = Depends(get_db)):
    db_theatre = db.query(Theatre).filter(Theatre.id == id).first()
    if not db_theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")
        
    update_data = theatre_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_theatre, key, value)
        
    db.commit()
    db.refresh(db_theatre)
    return db_theatre

@router.delete("/theatres/{id}", status_code=status.HTTP_200_OK)
def delete_theatre(id: str, db: Session = Depends(get_db)):
    db_theatre = db.query(Theatre).filter(Theatre.id == id).first()
    if not db_theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")
    db.delete(db_theatre)
    db.commit()
    return {"message": "Theatre deleted successfully"}


# --- Admin Screen APIs ---
@router.post("/screens", response_model=ScreenResponse, status_code=status.HTTP_201_CREATED)
def create_screen(screen_in: ScreenCreate, db: Session = Depends(get_db)):
    # Verify theatre exists
    db_theatre = db.query(Theatre).filter(Theatre.id == screen_in.theatre_id).first()
    if not db_theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")
        
    new_screen = Screen(**screen_in.model_dump())
    db.add(new_screen)
    db.commit()
    db.refresh(new_screen)
    return new_screen

@router.put("/screens/{id}", response_model=ScreenResponse)
def update_screen(id: str, screen_in: ScreenUpdate, db: Session = Depends(get_db)):
    db_screen = db.query(Screen).filter(Screen.id == id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    update_data = screen_in.model_dump(exclude_unset=True)
    if "theatre_id" in update_data:
        theatre_exists = db.query(Theatre).filter(Theatre.id == update_data["theatre_id"]).first()
        if not theatre_exists:
            raise HTTPException(status_code=404, detail="Theatre not found")
            
    for key, value in update_data.items():
        setattr(db_screen, key, value)
        
    db.commit()
    db.refresh(db_screen)
    return db_screen

@router.delete("/screens/{id}", status_code=status.HTTP_200_OK)
def delete_screen(id: str, db: Session = Depends(get_db)):
    db_screen = db.query(Screen).filter(Screen.id == id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    db.delete(db_screen)
    db.commit()
    return {"message": "Screen deleted successfully"}


# --- Admin Show APIs ---
@router.post("/shows", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
def create_show(show_in: ShowCreate, db: Session = Depends(get_db)):
    # 1. Verify Movie & Screen exist
    db_movie = db.query(Movie).filter(Movie.id == show_in.movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    db_screen = db.query(Screen).filter(Screen.id == show_in.screen_id).first()
    if not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    # 2. Validate available seats limit
    if show_in.available_seats is not None:
        if show_in.available_seats > db_screen.total_seats:
            raise HTTPException(
                status_code=400,
                detail="Available seats cannot exceed screen capacity"
            )
    else:
        # Default to full screen capacity
        show_in.available_seats = db_screen.total_seats

    # 3. Check screen schedule conflict
    overlapping = db.query(Show).filter(
        Show.screen_id == show_in.screen_id,
        Show.status == "ACTIVE",
        Show.start_time < show_in.end_time,
        Show.end_time > show_in.start_time
    ).first()
    if overlapping:
        raise HTTPException(
            status_code=400,
            detail="Schedule conflict: another show is active on this screen during these timings"
        )
        
    new_show = Show(**show_in.model_dump())
    db.add(new_show)
    db.commit()
    db.refresh(new_show)
    return new_show

@router.put("/shows/{id}", response_model=ShowResponse)
def update_show(id: str, show_in: ShowUpdate, db: Session = Depends(get_db)):
    db_show = db.query(Show).filter(Show.id == id).first()
    if not db_show:
        raise HTTPException(status_code=404, detail="Show not found")
        
    update_data = show_in.model_dump(exclude_unset=True)
    
    # Pre-checks for updates
    movie_id = update_data.get("movie_id", db_show.movie_id)
    screen_id = update_data.get("screen_id", db_show.screen_id)
    start_time = update_data.get("start_time", db_show.start_time)
    end_time = update_data.get("end_time", db_show.end_time)
    available_seats = update_data.get("available_seats", db_show.available_seats)

    # Validate Movie/Screen references if updated
    if "movie_id" in update_data:
        m_exists = db.query(Movie).filter(Movie.id == movie_id).first()
        if not m_exists:
            raise HTTPException(status_code=404, detail="Movie not found")
            
    db_screen = db.query(Screen).filter(Screen.id == screen_id).first()
    if "screen_id" in update_data and not db_screen:
        raise HTTPException(status_code=404, detail="Screen not found")

    # Validate seats against screen total
    if db_screen and available_seats > db_screen.total_seats:
        raise HTTPException(
            status_code=400,
            detail="Available seats cannot exceed screen capacity"
        )

    # Check for schedule conflicts
    overlapping = db.query(Show).filter(
        Show.id != id,
        Show.screen_id == screen_id,
        Show.status == "ACTIVE",
        Show.start_time < end_time,
        Show.end_time > start_time
    ).first()
    if overlapping:
        raise HTTPException(
            status_code=400,
            detail="Schedule conflict: another show is active on this screen during these timings"
        )

    for key, value in update_data.items():
        setattr(db_show, key, value)
        
    db.commit()
    db.refresh(db_show)
    return db_show

@router.delete("/shows/{id}", status_code=status.HTTP_200_OK)
def delete_show(id: str, db: Session = Depends(get_db)):
    db_show = db.query(Show).filter(Show.id == id).first()
    if not db_show:
        raise HTTPException(status_code=404, detail="Show not found")
    db.delete(db_show)
    db.commit()
    return {"message": "Show deleted successfully"}
