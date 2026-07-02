from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CineOps API Gateway"
    USER_SERVICE_URL: str = "http://user-service:8001"
    MOVIE_SERVICE_URL: str = "http://movie-service:8002"
    BOOKING_SERVICE_URL: str = "http://booking-service:8003"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8004"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"
    
    class Config:
        env_file = ".env"

settings = Settings()
