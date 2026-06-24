from app.schemas.auth import LoginRequest, RegisterRequest


def test_register_request_normalizes_email() -> None:
    payload = RegisterRequest(
        email="USER@EXAMPLE.COM",
        full_name="Test User",
        password="StrongPassword123!",
    )

    assert str(payload.email) == "user@example.com"


def test_login_request_normalizes_email() -> None:
    payload = LoginRequest(email="USER@EXAMPLE.COM", password="secret")

    assert str(payload.email) == "user@example.com"
