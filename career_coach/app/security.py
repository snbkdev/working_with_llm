"""Password hashing (bcrypt) and JWT helpers."""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    RESET_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
)

# bcrypt hashes at most 72 bytes of the password.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, token_type: str, expire_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": subject, "typ": token_type, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_token(token: str, expected_type: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("typ") != expected_type:
        return None
    return payload.get("sub")


def create_access_token(subject: str) -> str:
    return _create_token(subject, "access", ACCESS_TOKEN_EXPIRE_MINUTES)


def decode_access_token(token: str) -> str | None:
    """Return the subject (user id) if the access token is valid, else None."""
    return _decode_token(token, "access")


def create_reset_token(subject: str) -> str:
    return _create_token(subject, "reset", RESET_TOKEN_EXPIRE_MINUTES)


def decode_reset_token(token: str) -> str | None:
    """Return the subject (user id) if the reset token is valid, else None."""
    return _decode_token(token, "reset")
