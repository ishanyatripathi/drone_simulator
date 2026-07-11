"""
Camera acquisition layer.

Designed for future multi-camera support: each camera is opened and read
on its own background thread so multiple `CameraStream` instances can run
concurrently without blocking each other or the asyncio event loop. Each
websocket session (see `session/session_manager.py`) is handed a
`CameraStream` by index, defaulting to camera 0.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np

from app.config import settings


@dataclass
class CameraInfo:
    index: int
    is_open: bool
    width: int
    height: int


class CameraStream:
    """Continuously reads frames from a single camera device on a
    dedicated thread, always exposing only the most recent frame. This
    avoids buffered/stale frames piling up under CPU load, which matters
    for gesture timing accuracy.
    """

    def __init__(self, camera_index: int = settings.default_camera_index):
        self.camera_index = camera_index
        self._cap: cv2.VideoCapture | None = None
        self._lock = threading.Lock()
        self._latest_frame: np.ndarray | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._subscribers = 0

    def open(self) -> None:
        with self._lock:
            if self._cap is not None:
                return
            cap = cv2.VideoCapture(self.camera_index)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.frame_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.frame_height)
            cap.set(cv2.CAP_PROP_FPS, settings.target_fps)
            if not cap.isOpened():
                raise RuntimeError(f"Unable to open camera index {self.camera_index}")
            self._cap = cap
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()

    def _read_loop(self) -> None:
        assert self._cap is not None
        while self._running:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            frame = cv2.flip(frame, 1)  # mirror for intuitive left/right gestures
            with self._lock:
                self._latest_frame = frame
            time.sleep(1 / max(settings.target_fps, 1))

    def read(self) -> np.ndarray | None:
        with self._lock:
            return None if self._latest_frame is None else self._latest_frame.copy()

    def acquire(self) -> None:
        self._subscribers += 1
        self.open()

    def release(self) -> None:
        self._subscribers = max(0, self._subscribers - 1)
        if self._subscribers == 0:
            self.close()

    def close(self) -> None:
        with self._lock:
            self._running = False
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._latest_frame = None

    @property
    def is_open(self) -> bool:
        return self._cap is not None


class CameraManager:
    """Registry of `CameraStream`s keyed by camera index, shared across
    sessions so two users/sessions can watch the same physical camera
    without opening it twice.
    """

    def __init__(self) -> None:
        self._streams: dict[int, CameraStream] = {}
        self._lock = threading.Lock()

    def get_stream(self, camera_index: int) -> CameraStream:
        with self._lock:
            if camera_index not in self._streams:
                self._streams[camera_index] = CameraStream(camera_index)
            return self._streams[camera_index]

    @staticmethod
    def list_available(max_probe: int = 4) -> list[CameraInfo]:
        """Best-effort enumeration of camera devices for a UI picker."""
        found: list[CameraInfo] = []
        for idx in range(max_probe):
            cap = cv2.VideoCapture(idx)
            is_open = cap.isOpened()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if is_open else 0
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if is_open else 0
            if is_open:
                found.append(CameraInfo(index=idx, is_open=True, width=width, height=height))
            cap.release()
        return found


camera_manager = CameraManager()
