"""
Static gesture classification — current vocabulary (Phase 2.1 remap).

Every gesture below is a single-frame hand pose, evaluated per hand and
keyed by MediaPipe handedness ("Left" / "Right" from the user's own
perspective — the camera feed is pre-mirrored in `camera_manager.py`,
which is exactly what MediaPipe's handedness model assumes). Two-hand
combined gestures (HOVER, EMERGENCY_STOP) are NOT decided here — they are
resolved in `gesture_engine.py`, which has visibility into both hands at
once; this module only ever looks at one hand's landmarks at a time.

Gesture vocabulary:
  TAKEOFF        Right hand, thumb-only extended, pointing up
  LAND           Right hand, thumb-only extended, pointing down
  ROTATE_RIGHT   Right hand, thumb-only extended, pointing right
  ROTATE_LEFT    Left hand,  thumb-only extended, pointing left
  MOVE_FORWARD   Right hand, index + pinky extended (others curled)
  MOVE_BACKWARD  Left hand,  index + pinky extended (others curled)
  ASCEND         Right hand, pinky-only extended
  DESCEND        Left hand,  pinky-only extended
  MOVE_RIGHT     Right hand, all 5 fingers extended (open palm)
  MOVE_LEFT      Left hand,  all 5 fingers extended (open palm)
"""

from __future__ import annotations

from app.config import settings
from app.gestures.landmark_utils import Point, fingers_extended, thumb_direction_deg

# internal pose id -> (public gesture label, mapped command name)
STATIC_GESTURE_META: dict[str, tuple[str, str]] = {
    "TAKEOFF_POSE": ("Right Thumbs Up", "TAKEOFF"),
    "LAND_POSE": ("Right Thumbs Down", "LAND"),
    "ROTATE_RIGHT_POSE": ("Right Thumb Pointing Right", "ROTATE_RIGHT"),
    "ROTATE_LEFT_POSE": ("Left Thumb Pointing Left", "ROTATE_LEFT"),
    "MOVE_FORWARD_POSE": ("Right Hand Index+Pinky", "MOVE_FORWARD"),
    "MOVE_BACKWARD_POSE": ("Left Hand Index+Pinky", "MOVE_BACKWARD"),
    "ASCEND_POSE": ("Right Hand Pinky Extended", "ASCEND"),
    "DESCEND_POSE": ("Left Hand Pinky Extended", "DESCEND"),
    "MOVE_RIGHT_POSE": ("Right Open Palm", "MOVE_RIGHT"),
    "MOVE_LEFT_POSE": ("Left Open Palm", "MOVE_LEFT"),
}


def _angle_diff(a: float, b: float) -> float:
    return ((a - b + 180) % 360) - 180


def _thumb_axis_score(lm: list[Point], target_deg: float) -> float:
    """1.0 when the thumb points exactly at `target_deg`, decaying linearly
    to 0 at `settings.thumb_axis_tolerance_deg` away."""
    angle = thumb_direction_deg(lm)
    diff = abs(_angle_diff(angle, target_deg))
    tol = settings.thumb_axis_tolerance_deg
    return max(0.0, 1 - diff / tol)


def classify_static(lm: list[Point], handedness: str) -> tuple[str, float] | None:
    """Returns (internal_pose_id, confidence 0..1) for a SINGLE hand, or
    None if no pose in the current vocabulary matches. `handedness` is
    "Left" or "Right", exactly as reported by MediaPipe.
    """
    fingers = fingers_extended(lm, handedness)
    is_right = handedness == "Right"
    is_left = handedness == "Left"

    candidates: list[tuple[str, float]] = []

    # --- Thumb-only poses: orientation determines the gesture ---
    thumb_only = fingers.thumb and not any([fingers.index, fingers.middle, fingers.ring, fingers.pinky])
    if thumb_only:
        if is_right:
            up_score = _thumb_axis_score(lm, -90)
            if up_score > 0:
                candidates.append(("TAKEOFF_POSE", up_score))
            down_score = _thumb_axis_score(lm, 90)
            if down_score > 0:
                candidates.append(("LAND_POSE", down_score))
            right_score = _thumb_axis_score(lm, 0)
            if right_score > 0:
                candidates.append(("ROTATE_RIGHT_POSE", right_score))
        if is_left:
            left_score = _thumb_axis_score(lm, 180)
            if left_score > 0:
                candidates.append(("ROTATE_LEFT_POSE", left_score))

    # --- Index + pinky extended only ("rock on") ---
    if fingers.index and fingers.pinky and not fingers.thumb and not fingers.middle and not fingers.ring:
        if is_right:
            candidates.append(("MOVE_FORWARD_POSE", 1.0))
        elif is_left:
            candidates.append(("MOVE_BACKWARD_POSE", 1.0))

    # --- Pinky-only extended ---
    if fingers.pinky and not any([fingers.thumb, fingers.index, fingers.middle, fingers.ring]):
        if is_right:
            candidates.append(("ASCEND_POSE", 1.0))
        elif is_left:
            candidates.append(("DESCEND_POSE", 1.0))

    # --- Open palm: all 5 fingers extended ---
    # NOTE: when BOTH hands are simultaneously open, `gesture_engine.py`
    # overrides this per-hand reading with the two-hand HOVER (or, if the
    # hands are also overlapping, EMERGENCY_STOP) gesture — see there.
    if fingers.count() == 5:
        if is_right:
            candidates.append(("MOVE_RIGHT_POSE", 1.0))
        elif is_left:
            candidates.append(("MOVE_LEFT_POSE", 1.0))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[1], reverse=True)
    return candidates[0]


def static_gesture_label(pose_id: str) -> str:
    return STATIC_GESTURE_META.get(pose_id, (pose_id, "UNKNOWN"))[0]


def static_gesture_command(pose_id: str) -> str:
    return STATIC_GESTURE_META.get(pose_id, ("Unknown", "UNKNOWN"))[1]
