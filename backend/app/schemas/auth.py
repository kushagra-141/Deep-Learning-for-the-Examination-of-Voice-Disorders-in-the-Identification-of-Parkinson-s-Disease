"""Auth schemas (LLD §2.4.3, §2.7.8)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str  # ISO8601 UTC


class AdminUser(BaseModel):
    username: str
    role: str = "admin"
