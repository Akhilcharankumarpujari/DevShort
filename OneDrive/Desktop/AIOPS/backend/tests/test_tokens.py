import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import AppException
from app.security.tokens import TokenService, hash_refresh_token


def test_access_token_round_trip() -> None:
    service = TokenService(Settings(secret_key=SecretStr("test-secret"), jwt_issuer="test-suite"))

    token, expires_in = service.create_access_token(
        subject="user-1",
        roles=["Admin"],
        permissions=["users:read"],
    )
    payload = service.decode_token(token, expected_type="access")

    assert expires_in == 900
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"
    assert payload["roles"] == ["Admin"]
    assert payload["permissions"] == ["users:read"]


def test_refresh_token_round_trip() -> None:
    service = TokenService(Settings(secret_key=SecretStr("test-secret"), jwt_issuer="test-suite"))

    token, jti, expires_at = service.create_refresh_token(subject="user-1")
    payload = service.decode_token(token, expected_type="refresh")

    assert payload["sub"] == "user-1"
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti
    assert expires_at is not None


def test_token_type_mismatch_is_rejected() -> None:
    service = TokenService(Settings(secret_key=SecretStr("test-secret"), jwt_issuer="test-suite"))
    token, _ = service.create_access_token(subject="user-1", roles=[], permissions=[])

    with pytest.raises(AppException) as exc_info:
        service.decode_token(token, expected_type="refresh")

    assert exc_info.value.code == "invalid_token_type"


def test_refresh_token_hash_is_stable_and_non_plaintext() -> None:
    token = "refresh-token-value"

    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != token
