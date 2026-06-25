from __future__ import annotations

import json
from enum import StrEnum
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AIOps Platform API"
    app_version: str = "0.1.0"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    log_level: str = "INFO"
    log_json: bool = True
    request_id_header: str = "X-Request-ID"

    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "aiops-platform"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_min_length: int = 8

    cors_origins: list[str] = Field(default_factory=list)

    prometheus_url: str = "http://localhost:9090"
    loki_url: str = "http://localhost:3100"

    # Jenkins settings
    jenkins_url: str = "http://localhost:8080"
    jenkins_username: str = ""
    jenkins_api_token: SecretStr | None = None
    jenkins_request_timeout: int = 30

    # AI Provider settings
    ai_provider: str = "ollama"  # "openai" or "ollama"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o"
    openai_api_url: str = "https://api.openai.com/v1"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ai_request_timeout: int = 120
    ai_max_retries: int = 2

    database_url: str = "postgresql+asyncpg://aiops:aiops@localhost:5432/aiops"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 30
    sql_echo: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON value must be a list")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        raise ValueError("CORS_ORIGINS must be a comma-separated string or list")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return normalized

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if self.secret_key.get_secret_value() == "change-me-in-production":
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.cors_origins:
                raise ValueError("CORS_ORIGINS must be explicitly configured in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
