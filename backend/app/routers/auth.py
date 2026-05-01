"""P1-08 + P4-01 (partial): Admin auth — login, logout."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginIn, TokenOut

router = APIRouter()

_COOKIE_NAME = "access_token"


def _password_matches(plain: str, hashed: str) -> bool:
    """Bcrypt verify; treat empty hash as 'no admin configured'."""
    if not hashed:
        return False
    try:
        return verify_password(plain, hashed)
    except Exception:
        # passlib raises on malformed hashes — surface as auth failure, not 500.
        return False


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
async def login(
    request: Request,  # noqa: ARG001 — required by slowapi for IP extraction
    body: LoginIn,
    response: Response,
) -> TokenOut:
    """Validate credentials, return a JWT, and set an HttpOnly cookie."""
    settings = get_settings()
    expected_hash = settings.ADMIN_PASSWORD_HASH.get_secret_value()

    if body.username != settings.ADMIN_USERNAME or not _password_matches(
        body.password, expected_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    ttl = dt.timedelta(minutes=settings.JWT_TTL_MIN)
    expires_at = dt.datetime.now(dt.timezone.utc) + ttl
    token = create_access_token(
        {"sub": body.username, "role": "admin"},
        expires_delta=ttl,
    )
    secure = settings.ENV == "prod"
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=int(ttl.total_seconds()),
        path="/",
    )
    return TokenOut(access_token=token, expires_at=expires_at.isoformat())


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    """Clear the admin cookie."""
    response.delete_cookie(_COOKIE_NAME, path="/")
    return {"ok": True}
