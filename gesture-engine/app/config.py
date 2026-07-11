"""
Central configuration for the AERIS Gesture Engine.

Keeping every tunable safety/timing constant here makes it easy to
re-balance recognition behavior without touching classifier logic.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]  # tighten in production deployments

    # --- Camera ---
    default_camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 30
    jpeg_quality: int = 70  # streamed preview quality (0-100)

    # --- MediaPipe Hands ---
    # 2 hands required: several gestures in the current vocabulary are
    # two-handed (HOVER = both open palms, EMERGENCY_STOP = crossed hands).
    max_num_hands: int = 2
    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.6
    model_complexity: int = 1

    # --- Safety / stability (per spec) ---
    # A gesture's classifier confidence must exceed this to even be considered.
    min_gesture_confidence: float = 0.95
    # The SAME gesture must be observed continuously for this long before
    # it is confirmed and emitted as a command.
    confirmation_window_ms: int = 500
    # After a command is emitted, no new command will be emitted for this
    # long, to prevent rapid-fire accidental re-triggers.
    cooldown_ms: int = 300
    # If tracking is lost or the gesture changes, how much jitter (in
    # frames) we tolerate before resetting the confirmation timer.
    max_dropped_frames: int = 3

    # --- Static pose geometry (current gesture vocabulary) ---
    # How close a thumb's pointing angle must be to vertical (±90°) to count
    # as a thumbs-up/down pose, vs. horizontal (0°/180°) for a rotate pose.
    thumb_axis_tolerance_deg: float = 30
    # Two-hand gestures: palm-center distance (normalized by average hand
    # scale) below this counts as "hands overlapping/crossed" for
    # EMERGENCY_STOP; at or above it, two simultaneously open palms are
    # read as the (side-by-side) HOVER pose instead.
    crossed_hands_max_distance: float = 1.4

    # --- Legacy dynamic-gesture config (currently unused) ---
    # No gesture in the active vocabulary (see static_classifier.py /
    # gesture_engine.py) is motion-based anymore as of the Phase 2.1
    # remap. These settings are kept only so `motion_tracker.py` and
    # `dynamic_classifier.py` — retained but unwired, in case a future
    # phase reintroduces motion gestures — remain internally consistent
    # and importable/runnable rather than referencing removed config.
    motion_history_seconds: float = 1.2
    swipe_min_distance_px: float = 110
    swipe_max_duration_s: float = 0.6
    rotate_min_angle_deg: float = 65
    circle_min_radius_px: float = 40
    circle_min_coverage: float = 0.75
    wave_min_direction_changes: int = 3

    class Config:
        env_prefix = "AERIS_GESTURE_"
        protected_namespaces = ()


settings = Settings()
