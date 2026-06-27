from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "TechHub API Gateway"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    USER_SERVICE_URL: str = Field(default="http://user-service:8000")
    PRODUCT_SERVICE_URL: str = Field(default="http://product-service:8000")
    ORDER_SERVICE_URL: str = Field(default="http://order-service:8000")
    INVENTORY_SERVICE_URL: str = Field(default="http://inventory-service:8000")
    PAYMENT_SERVICE_URL: str = Field(default="http://payment-service:8000")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
