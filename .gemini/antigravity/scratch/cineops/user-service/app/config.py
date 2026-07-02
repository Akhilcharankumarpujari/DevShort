from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CineOps User Service"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cineops_users"
    
    class Config:
        env_file = ".env"

settings = Settings()
