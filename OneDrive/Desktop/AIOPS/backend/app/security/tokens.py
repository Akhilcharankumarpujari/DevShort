from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from jwt import InvalidTokenError

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException

TokenType = Literal["access", "refresh"]


class TokenService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def create_access_token(
        self,
        *,
        subject: str,
        roles: list[str],
        permissions: list[str],
    ) -> tuple[str, int]:
        expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        expires_at = datetime.now(UTC) + expires_delta
        payload = {
            "sub": subject,
            "type": "access",
            "roles": roles,
            "permissions": permissions,
            "jti": str(uuid.uuid4()),
            "iss": self.settings.jwt_issuer,
            "iat": datetime.now(UTC),
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self.settings.secret_key.get_secret_value(),
            algorithm=self.settings.jwt_algorithm,
        )
        return token, int(expires_delta.total_seconds())

    def create_refresh_token(self, *, subject: str) -> tuple[str, str, datetime]:
        expires_at = datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days)
        jti = str(uuid.uuid4())
        payload = {
            "sub": subject,
            "type": "refresh",
            "jti": jti,
            "iss": self.settings.jwt_issuer,
            "iat": datetime.now(UTC),
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self.settings.secret_key.get_secret_value(),
            algorithm=self.settings.jwt_algorithm,
        )
        return token, jti, expires_at

    def decode_token(self, token: str, *, expected_type: TokenType) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key.get_secret_value(),
                algorithms=[self.settings.jwt_algorithm],
                issuer=self.settings.jwt_issuer,
            )
        except InvalidTokenError as exc:
            raise AppException(
                status_code=401,
                code="invalid_token",
                message="Token is invalid or expired.",
            ) from exc

        token_type = payload.get("type")
        if token_type != expected_type:
            raise AppException(
                status_code=401,
                code="invalid_token_type",
                message="Token type is not valid for this operation.",
            )
        if not payload.get("sub"):
            raise AppException(
                status_code=401,
                code="invalid_token_subject",
                message="Token subject is missing.",
            )
        return payload


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
