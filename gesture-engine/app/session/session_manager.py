"""
Session management.

Each WebSocket connection gets its own `GestureSession`: its own
`HandTracker`, its own `GestureEngine` (and therefore its own debounce
state), and a reference to a `CameraStream` (shared by camera index, so
two sessions can watch the same physical camera without opening it
twice). This is what makes multi-user support a matter of "accept another
connection" rather than a rewrite — each session is fully isolated.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.config import settings
from app.gestures.gesture_engine import GestureEngine
from app.vision.camera_manager import CameraStream, camera_manager
from app.vision.hand_tracker import HandTracker


@dataclass
class GestureSession:
    session_id: str
    camera_index: int
    camera: CameraStream
    hand_tracker: HandTracker = field(default_factory=HandTracker)
    gesture_engine: GestureEngine = field(default_factory=GestureEngine)
    frame_index: int = 0

    def close(self) -> None:
        self.camera.release()
        self.hand_tracker.close()
        self.gesture_engine.reset()


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, GestureSession] = {}

    def create(self, camera_index: int | None = None) -> GestureSession:
        session_id = str(uuid.uuid4())
        idx = camera_index if camera_index is not None else settings.default_camera_index
        stream = camera_manager.get_stream(idx)
        stream.acquire()
        session = GestureSession(session_id=session_id, camera_index=idx, camera=stream)
        self._sessions[session_id] = session
        return session

    def destroy(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            session.close()

    def get(self, session_id: str) -> GestureSession | None:
        return self._sessions.get(session_id)

    @property
    def active_count(self) -> int:
        return len(self._sessions)


session_manager = SessionManager()
