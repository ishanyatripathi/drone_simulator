"""Models describing per-frame hand tracking state sent to the frontend."""

from __future__ import annotations

from pydantic import BaseModel


class Landmark(BaseModel):
    x: float
    y: float
    z: float


class HandDetection(BaseModel):
    hand: str  # "Left" | "Right"
    handedness_confidence: float
    landmarks: list[Landmark]  # always 21 points, MediaPipe order
    bounding_box: tuple[float, float, float, float]  # x, y, w, h (normalized 0-1)


class FrameMessage(BaseModel):
    """Broadcast once per processed frame."""

    frame_jpeg_b64: str
    hands: list[HandDetection]
    fps: float
    frame_index: int
