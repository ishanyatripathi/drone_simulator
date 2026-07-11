from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.auth.security import authenticate_user, create_access_token
from app.config import settings
from app.models.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not authenticate_user(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token, expires_in_minutes=settings.jwt_expiry_minutes)
