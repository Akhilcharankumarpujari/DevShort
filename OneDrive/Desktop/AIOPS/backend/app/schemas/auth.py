from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    id: UUID
    key: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    status: str
    is_verified: bool
    roles: list[RoleResponse] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPair


class LogoutResponse(BaseModel):
    status: str = "logged_out"
