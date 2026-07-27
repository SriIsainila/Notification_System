import pytest

from app.core.security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verification() -> None:
    password_hash = hash_password("strong-password")

    assert password_hash != "strong-password"
    assert verify_password("strong-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_bcrypt_rejects_password_over_72_bytes() -> None:
    with pytest.raises(ValueError, match="72"):
        hash_password("é" * 37)


def test_access_token_round_trip() -> None:
    token = create_access_token(42, {"email": "person@example.com"})
    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["email"] == "person@example.com"
    assert payload["type"] == "access"


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(TokenValidationError):
        decode_access_token("not-a-jwt")
