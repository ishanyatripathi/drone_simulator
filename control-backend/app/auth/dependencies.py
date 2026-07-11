from __future__ import annotations

from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_token

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


async def get_current_user(token: str | None = Depends(_oauth2_scheme)) -> str:
    """REST dependency: validates the Bearer token and returns the username."""
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    username = decode_token(token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return username


async def authenticate_websocket(websocket: WebSocket) -> str | None:
    """WebSocket connections can't set Authorization headers from a plain
    browser WebSocket client, so the token is passed as a query parameter
    (`?token=...`), a standard pragmatic pattern for WS auth. Returns the
    username, or None if the token is missing/invalid (caller should close
    the connection with code 4401 in that case).
    """
    token = websocket.query_params.get("token")
    if not token:
        return None
    return decode_token(token)
