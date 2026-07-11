"""
Minimal JWT authentication for Phase 3.

A single demo operator account (see `app/config.py`) is used as a
stand-in for a real user/identity store — swapping in one later only
touches `authenticate_user` below; every REST/WebSocket consumer just
calls `decode_token` / the FastAPI dependencies in `dependencies.py`.

The demo password is hashed with `bcrypt` at import time and verified
via bcrypt's constant-time comparison, rather than compared as plaintext
— the same pattern a real user store would use, just backed by one
hardcoded account instead of a database. (Using `bcrypt` directly rather
than `passlib`: passlib's bcrypt backend is unmaintained and incompatible
with modern bcrypt releases — it crashes at import time — so this calls
the actively-maintained `bcrypt` package directly.)
"""

from __future__ import annotations

import time

import bcrypt
from jose import JWTError, jwt

from app.config import settings

_demo_password_hash = bcrypt.hashpw(settings.demo_password.encode("utf-8"), bcrypt.gensalt())


def authenticate_user(username: str, password: str) -> bool:
    if username != settings.demo_username:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), _demo_password_hash)


def create_access_token(subject: str) -> str:
    expire = time.time() + settings.jwt_expiry_minutes * 60
    payload = {"sub": subject, "exp": int(expire)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    """Returns the subject (username) if the token is valid, else None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    return payload.get("sub")


