from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "TechHub User Service"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@db:5432/techhub_users")
    
    # JWT Security Settings
    # In production, this must be a secure random key
    SECRET_KEY: str = Field(default="8810df66a3ea68a8dc4e7a8848f02931a54160de4698de29b222959828d9c6c5")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
