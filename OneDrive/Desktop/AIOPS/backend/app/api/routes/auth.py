from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from app.services.auth_service import AuthService, user_to_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    return await AuthService(session).register_user(
        email=str(payload.email),
        full_name=payload.full_name,
        password=payload.password,
    )


@router.post("/login", response_model=AuthResponse, summary="Login with email and password")
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    return await AuthService(session).login(email=str(payload.email), password=payload.password)


@router.post("/refresh", response_model=TokenPair, summary="Rotate refresh token")
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenPair:
    return await AuthService(session).refresh(payload.refresh_token)


@router.post("/logout", response_model=LogoutResponse, summary="Logout and revoke refresh token")
async def logout(
    payload: LogoutRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LogoutResponse:
    await AuthService(session).logout(payload.refresh_token)
    return LogoutResponse()


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    return user_to_response(current_user)
