from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CineOps Payment Service"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cineops_payments"
    BOOKING_SERVICE_URL: str = "http://localhost:8003"
    
    class Config:
        env_file = ".env"

settings = Settings()
