from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "TechHub Product Service"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@db:5432/techhub_products")
    
    # JWT Security Settings
    SECRET_KEY: str = Field(default="8810df66a3ea68a8dc4e7a8848f02931a54160de4698de29b222959828d9c6c5")
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
