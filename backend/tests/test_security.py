import pytest
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token

def test_password_hashing():
    raw_pwd = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation():
    subject = "user-12345"
    token = create_access_token(subject=subject, role="USER")
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == subject
    assert payload["role"] == "USER"

def test_jwt_token_invalid():
    invalid_token = "invalid.token.str"
    payload = decode_access_token(invalid_token)
    assert payload is None
