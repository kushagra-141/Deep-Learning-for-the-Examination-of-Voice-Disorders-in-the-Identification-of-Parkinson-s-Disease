"""P1-08: FastAPI dependencies."""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.ml.manager import ModelManager
from app.schemas.auth import AdminUser

# Dependency types
SessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_model_manager(request: Request) -> ModelManager:
    """Get the ModelManager singleton from app state."""
    return request.app.state.model_manager


ModelManagerDep = Annotated[ModelManager, Depends(get_model_manager)]


def get_current_admin(
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> AdminUser:
    """Validate the admin JWT cookie and return the user, or 401."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGO],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from None
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token")
    return AdminUser(username=sub, role="admin")


AdminDep = Annotated[AdminUser, Depends(get_current_admin)]
