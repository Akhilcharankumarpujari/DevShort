from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CineOps Notification Service"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cineops_notifications"
    BOOKING_SERVICE_URL: str = "http://localhost:8003"
    PAYMENT_SERVICE_URL: str = "http://localhost:8004"
    
    class Config:
        env_file = ".env"

settings = Settings()
