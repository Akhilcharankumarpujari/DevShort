from app.security.password import hash_password, verify_password


def test_hash_password_does_not_store_plaintext() -> None:
    hashed = hash_password("StrongPassword123!")

    assert hashed != "StrongPassword123!"
    assert verify_password("StrongPassword123!", hashed)


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("StrongPassword123!")

    assert not verify_password("wrong-password", hashed)
