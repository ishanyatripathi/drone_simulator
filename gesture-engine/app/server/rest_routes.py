from __future__ import annotations

from fastapi import APIRouter

from app.commands.command_mapper import list_supported_gestures
from app.session.session_manager import session_manager
from app.vision.camera_manager import CameraManager

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "active_sessions": session_manager.active_count}


@router.get("/cameras")
def list_cameras() -> dict:
    cameras = CameraManager.list_available()
    return {"cameras": [c.__dict__ for c in cameras]}


@router.get("/gestures")
def list_gestures() -> dict:
    return {"gestures": list_supported_gestures()}
