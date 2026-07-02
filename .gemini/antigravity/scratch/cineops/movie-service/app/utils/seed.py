import uuid
from datetime import date, datetime, timedelta, time
from sqlalchemy.orm import Session
from app.models.movie import Movie, Theatre, Screen, Show

def seed_database(db: Session):
    # Check if movies exist already. If so, skip seeding
    if db.query(Movie).first() is not None:
        return
        
    print("Seeding database...")
    
    # 1. Seed 20 Movies
    movies_data = [
        {"title": "Inception", "genre": "Sci-Fi", "language": "English", "duration": 148, "status": "NOW_SHOWING", "rating": 8.8},
        {"title": "Interstellar", "genre": "Sci-Fi", "language": "English", "duration": 169, "status": "NOW_SHOWING", "rating": 8.7},
        {"title": "The Dark Knight", "genre": "Action", "language": "English", "duration": 152, "status": "NOW_SHOWING", "rating": 9.0},
        {"title": "Avatar: The Way of Water", "genre": "Sci-Fi", "language": "English", "duration": 192, "status": "NOW_SHOWING", "rating": 7.6},
        {"title": "Dune: Part Two", "genre": "Sci-Fi", "language": "English", "duration": 166, "status": "NOW_SHOWING", "rating": 8.9},
        {"title": "Oppenheimer", "genre": "Drama", "language": "English", "duration": 180, "status": "NOW_SHOWING", "rating": 8.4},
        {"title": "Spider-Man: Across the Spider-Verse", "genre": "Animation", "language": "English", "duration": 140, "status": "NOW_SHOWING", "rating": 8.6},
        {"title": "RRR", "genre": "Action", "language": "Telugu", "duration": 187, "status": "NOW_SHOWING", "rating": 7.8},
        {"title": "Jawan", "genre": "Action", "language": "Hindi", "duration": 168, "status": "NOW_SHOWING", "rating": 7.0},
        {"title": "Kalki 2898 AD", "genre": "Sci-Fi", "language": "Telugu", "duration": 181, "status": "NOW_SHOWING", "rating": 7.5},
        {"title": "Pathaan", "genre": "Action", "language": "Hindi", "duration": 146, "status": "NOW_SHOWING", "rating": 6.5},
        {"title": "Leo", "genre": "Action", "language": "Tamil", "duration": 164, "status": "NOW_SHOWING", "rating": 7.2},
        {"title": "Drishyam 2", "genre": "Drama", "language": "Hindi", "duration": 140, "status": "NOW_SHOWING", "rating": 8.2},
        {"title": "Salaar: Part 1 - Ceasefire", "genre": "Action", "language": "Telugu", "duration": 175, "status": "NOW_SHOWING", "rating": 6.8},
        {"title": "Gadar 2", "genre": "Action", "language": "Hindi", "duration": 170, "status": "NOW_SHOWING", "rating": 6.2},
        # Coming soon movies
        {"title": "Avengers: Doomsday", "genre": "Action", "language": "English", "duration": 150, "status": "COMING_SOON", "rating": 0.0},
        {"title": "Superman", "genre": "Action", "language": "English", "duration": 140, "status": "COMING_SOON", "rating": 0.0},
        {"title": "Avatar 3", "genre": "Sci-Fi", "language": "English", "duration": 180, "status": "COMING_SOON", "rating": 0.0},
        {"title": "Pushpa 2: The Rule", "genre": "Action", "language": "Telugu", "duration": 180, "status": "COMING_SOON", "rating": 0.0},
        {"title": "War 2", "genre": "Action", "language": "Hindi", "duration": 150, "status": "COMING_SOON", "rating": 0.0},
    ]
    
    movies = []
    for m in movies_data:
        movie = Movie(
            id=str(uuid.uuid4()),
            title=m["title"],
            description=f"An amazing {m['genre']} movie in {m['language']}.",
            genre=m["genre"],
            language=m["language"],
            duration_minutes=m["duration"],
            release_date=date.today() - timedelta(days=30) if m["status"] == "NOW_SHOWING" else date.today() + timedelta(days=90),
            rating=m["rating"],
            status=m["status"]
        )
        db.add(movie)
        movies.append(movie)
    
    db.commit()
    
    # 2. Seed 8 Theatres across 5 Cities (Mumbai, Delhi, Bangalore, Hyderabad, Chennai)
    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"]
    theatre_names = [
        ("PVR ICON", "Mumbai", "Phoenix High Street, Lower Parel"),
        ("Inox Insignia", "Mumbai", "Nariman Point"),
        ("PVR Director's Cut", "Delhi", "Ambience Mall, Vasant Kunj"),
        ("Cinepolis", "Delhi", "Saket"),
        ("PVR Superplex", "Bangalore", "Forum Mall, Koramangala"),
        ("Inox Lido", "Bangalore", "Off MG Road"),
        ("Prasads Multiplex", "Hyderabad", "NTR Marg"),
        ("Sathyam Cinemas", "Chennai", "Royapettah"),
    ]
    
    theatres = []
    for t_name, city, address in theatre_names:
        theatre = Theatre(
            id=str(uuid.uuid4()),
            name=t_name,
            city=city,
            address=address
        )
        db.add(theatre)
        theatres.append(theatre)
        
    db.commit()
    
    # 3. Seed 20 Screens distributed among theatres
    screens = []
    for idx, theatre in enumerate(theatres):
        # Create 2 or 3 screens per theatre
        num_screens = 3 if idx < 4 else 2
        for s_idx in range(1, num_screens + 1):
            screen = Screen(
                id=str(uuid.uuid4()),
                theatre_id=theatre.id,
                screen_name=f"Screen {s_idx}",
                total_seats=100 + (s_idx * 50)  # 150, 200, 250 seats
            )
            db.add(screen)
            screens.append(screen)
            
    db.commit()
    
    # 4. Seed 50 Shows (distributed over the next 3 days to avoid schedule overlaps)
    # Define 4 non-overlapping daily showtime slots:
    # Slot 1: 10:00 - 12:45
    # Slot 2: 13:30 - 16:15
    # Slot 3: 17:00 - 19:45
    # Slot 4: 20:30 - 23:15
    slots = [
        (time(10, 0), time(12, 45)),
        (time(13, 30), time(16, 15)),
        (time(17, 0), time(19, 45)),
        (time(20, 30), time(23, 15))
    ]
    
    showing_movies = [m for m in movies if m.status == "NOW_SHOWING"]
    
    show_count = 0
    today = date.today()
    
    # Generate shows across 3 days, looping through screens and slotting movies
    for day_offset in range(3):
        show_date = today + day_offset
        
        for screen in screens:
            if show_count >= 50:
                break
                
            for slot_idx, (start_t, end_t) in enumerate(slots):
                if show_count >= 50:
                    break
                    
                # Pick a movie rotationally
                movie = showing_movies[show_count % len(showing_movies)]
                
                # Combine date and time
                start_dt = datetime.combine(show_date, start_t)
                end_dt = datetime.combine(show_date, end_t)
                
                show = Show(
                    id=str(uuid.uuid4()),
                    movie_id=movie.id,
                    screen_id=screen.id,
                    show_date=show_date,
                    start_time=start_dt,
                    end_time=end_dt,
                    ticket_price=150.0 + (slot_idx * 50.0), # Prices: 150, 200, 250, 300
                    available_seats=screen.total_seats,
                    status="ACTIVE"
                )
                db.add(show)
                show_count += 1
                
    db.commit()
    print(f"Successfully seeded database with {len(movies)} movies, {len(theatres)} theatres, {len(screens)} screens, and {show_count} shows.")
