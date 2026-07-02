import pytest
from datetime import timedelta
import jwt
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

def test_password_hashing():
    password = "supersecretpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_tokens():
    payload = {"sub": "user_123", "role": "USER"}
    
    # Access Token
    access_token = create_access_token(data=payload, expires_delta=timedelta(minutes=5))
    decoded = decode_token(access_token)
    
    assert decoded["sub"] == "user_123"
    assert decoded["role"] == "USER"
    assert decoded["type"] == "access"
    assert "exp" in decoded

    # Refresh Token
    refresh_token = create_refresh_token(data={"sub": "user_123"}, expires_delta=timedelta(days=1))
    decoded_refresh = decode_token(refresh_token)
    
    assert decoded_refresh["sub"] == "user_123"
    assert decoded_refresh["type"] == "refresh"
    assert "role" not in decoded_refresh
