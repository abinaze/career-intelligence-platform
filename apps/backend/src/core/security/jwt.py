"""
JWT token operations.

Uses HS256 with easy upgrade path to RS256.
Tokens carry minimal claims; user data is always fetched fresh from DB.

Uses PyJWT rather than python-jose, since python-jose transitively
depends on the vulnerable ecdsa library (Minerva timing attack,
GHSA-wgq4-4cfg-c4x3).
"""

from __future__ import annotations

import datetime
import hashlib
from typing import Any
from uuid import UUID

import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from src.core.config.settings import get_settings
from src.core.logging.setup import get_logger

logger = get_logger(__name__)
_settings = get_settings()

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=65536,
    argon2__parallelism=1,
)


class TokenError(Exception):
    """Raised when a JWT cannot be decoded or validated."""


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2id hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: UUID | str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.datetime.now(tz=datetime.UTC)
    expire = now + datetime.timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": TokenType.ACCESS,
        "iat": now,
        "exp": expire,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        _settings.SECRET_KEY,
        algorithm=_settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: UUID | str) -> str:
    """Create a long-lived refresh token."""
    now = datetime.datetime.now(tz=datetime.UTC)
    expire = now + datetime.timedelta(days=_settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "type": TokenType.REFRESH,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        _settings.SECRET_KEY,
        algorithm=_settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token. Raises TokenError if invalid."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            _settings.SECRET_KEY,
            algorithms=[_settings.JWT_ALGORITHM],
        )

        if payload.get("type") != TokenType.ACCESS:
            raise TokenError("Invalid token type")

        return payload

    except ExpiredSignatureError as e:
        logger.warning("JWT expired", error=str(e))
        raise TokenError("Token has expired") from e
    except (DecodeError, InvalidTokenError) as e:
        logger.warning("JWT decode failed", error=str(e))
        raise TokenError("Token is invalid") from e


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token. Raises TokenError if invalid."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            _settings.SECRET_KEY,
            algorithms=[_settings.JWT_ALGORITHM],
        )

        if payload.get("type") != TokenType.REFRESH:
            raise TokenError("Invalid token type")

        return payload

    except ExpiredSignatureError as e:
        logger.warning("Refresh token expired", error=str(e))
        raise TokenError("Token has expired") from e
    except (DecodeError, InvalidTokenError) as e:
        logger.warning("Refresh token decode failed", error=str(e))
        raise TokenError("Token is invalid") from e


def hash_token(token: str) -> str:
    """Hash a token string for secure database storage."""
    return hashlib.sha256(token.encode()).hexdigest()
