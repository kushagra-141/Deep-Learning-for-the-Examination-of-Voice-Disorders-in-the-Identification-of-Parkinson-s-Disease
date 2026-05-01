"""P1-08: Security helpers for auth and hashing."""
from __future__ import annotations

import datetime as dt
from datetime import timezone

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: dt.timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = dt.datetime.now(timezone.utc) + expires_delta
    else:
        expire = dt.datetime.now(timezone.utc) + dt.timedelta(minutes=settings.JWT_TTL_MIN)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGO,
    )
    return encoded_jwt
