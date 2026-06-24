from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.models.user import User
from app.security.tokens import TokenService
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    payload = getattr(request.state, "token_payload", None)
    if payload is None:
        if credentials is None:
            raise AppException(
                status_code=401,
                code="not_authenticated",
                message="Authentication credentials were not provided.",
            )
        payload = TokenService().decode_token(credentials.credentials, expected_type="access")

    user = await AuthService(session).get_user_by_id(UUID(str(payload["sub"])))
    if user is None:
        raise AppException(status_code=401, code="user_not_found", message="User no longer exists.")
    if not user.is_active:
        raise AppException(status_code=403, code="user_disabled", message="User account is disabled.")
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_permissions(*required_permissions: str) -> Callable[..., Awaitable[User]]:
    async def dependency(user: User = Depends(get_current_active_user)) -> User:
        user_permissions = {
            permission.key
            for role in user.roles
            for permission in role.permissions
        }
        missing_permissions = set(required_permissions) - user_permissions
        if missing_permissions:
            raise AppException(
                status_code=403,
                code="insufficient_permissions",
                message="User does not have permission to perform this action.",
                details={"missing_permissions": sorted(missing_permissions)},
            )
        return user

    return dependency
