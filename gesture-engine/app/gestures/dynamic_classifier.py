"""
Dynamic gesture classification.

Operates on a `MotionTracker`'s recent samples (palm-center pixel position
+ hand roll angle over ~1.2s) and detects motion-based gestures. Checks
run in priority order from "most structurally distinctive" to "least",
since a real trajectory can weakly satisfy more than one pattern.

Recognized: Wave, Circle, Orbit, Rotate Left/Right, Swipe Left/Right.
"""

from __future__ import annotations

import math

from app.config import settings
from app.gestures.motion_tracker import MotionSample

# internal id -> (public label, mapped command name)
DYNAMIC_GESTURE_META: dict[str, tuple[str, str]] = {
    "WAVE": ("Wave", "RETURN_HOME"),
    "CIRCLE": ("Circle", "CIRCLE"),
    "ORBIT": ("Orbit", "ORBIT"),
    "ROTATE_LEFT": ("Rotate Left", "YAW_LEFT"),
    "ROTATE_RIGHT": ("Rotate Right", "YAW_RIGHT"),
    "SWIPE_LEFT": ("Swipe Left", "MOVE_LEFT"),
    "SWIPE_RIGHT": ("Swipe Right", "MOVE_RIGHT"),
}


def _unwrap_angles(angles: list[float]) -> list[float]:
    unwrapped = [angles[0]]
    for a in angles[1:]:
        prev = unwrapped[-1]
        d = a - (prev % 360)
        if d > 180:
            d -= 360
        elif d < -180:
            d += 360
        unwrapped.append(prev + d)
    return unwrapped


def _detect_wave(samples: list[MotionSample]) -> tuple[str, float] | None:
    xs = [s.x for s in samples]
    if len(xs) < 6:
        return None
    direction_changes = 0
    last_dir = 0
    for a, b in zip(xs, xs[1:]):
        d = b - a
        if abs(d) < 2:
            continue
        cur_dir = 1 if d > 0 else -1
        if last_dir != 0 and cur_dir != last_dir:
            direction_changes += 1
        last_dir = cur_dir

    amplitude = max(xs) - min(xs)
    if direction_changes >= settings.wave_min_direction_changes and amplitude > 30:
        score = min(1.0, direction_changes / (settings.wave_min_direction_changes + 2))
        return "WAVE", max(0.9, score)
    return None


def _fit_circle_quality(samples: list[MotionSample]) -> tuple[float, float, float]:
    """Returns (avg_radius, radius_consistency 0..1, total_angular_sweep_deg)."""
    cx = sum(s.x for s in samples) / len(samples)
    cy = sum(s.y for s in samples) / len(samples)

    radii = [math.hypot(s.x - cx, s.y - cy) for s in samples]
    avg_radius = sum(radii) / len(radii)
    if avg_radius < 1e-6:
        return 0.0, 0.0, 0.0

    variance = sum((r - avg_radius) ** 2 for r in radii) / len(radii)
    consistency = max(0.0, 1 - (math.sqrt(variance) / avg_radius))

    angles = [math.degrees(math.atan2(s.y - cy, s.x - cx)) for s in samples]
    unwrapped = _unwrap_angles(angles)
    sweep = abs(unwrapped[-1] - unwrapped[0])

    return avg_radius, consistency, sweep


def _detect_circle_or_orbit(samples: list[MotionSample], duration: float) -> tuple[str, float] | None:
    if len(samples) < 8:
        return None

    avg_radius, consistency, sweep = _fit_circle_quality(samples)
    required_sweep = 360 * settings.circle_min_coverage

    if avg_radius < settings.circle_min_radius_px or consistency < 0.55 or sweep < required_sweep:
        return None

    confidence = min(1.0, consistency * min(1.0, sweep / 360))

    # Orbit = larger, slower circular sweep. Circle = tighter, quicker loop.
    is_orbit = avg_radius > settings.circle_min_radius_px * 2.2 and duration > 0.7
    return ("ORBIT", confidence) if is_orbit else ("CIRCLE", confidence)


def _detect_rotate(samples: list[MotionSample]) -> tuple[str, float] | None:
    rolls = [s.roll_deg for s in samples]
    unwrapped = _unwrap_angles(rolls)
    delta = unwrapped[-1] - unwrapped[0]

    if abs(delta) < settings.rotate_min_angle_deg:
        return None

    # Require reasonably monotonic rotation (not jittery back-and-forth).
    diffs = [b - a for a, b in zip(unwrapped, unwrapped[1:])]
    same_sign = sum(1 for d in diffs if d != 0 and (d > 0) == (delta > 0))
    monotonicity = same_sign / max(1, len(diffs))
    if monotonicity < 0.65:
        return None

    confidence = min(1.0, monotonicity * min(1.0, abs(delta) / (settings.rotate_min_angle_deg * 1.5)))
    return ("ROTATE_LEFT" if delta < 0 else "ROTATE_RIGHT", confidence)


def _detect_swipe(samples: list[MotionSample], duration: float) -> tuple[str, float] | None:
    if duration > settings.swipe_max_duration_s or duration <= 0:
        return None

    start, end = samples[0], samples[-1]
    dx = end.x - start.x
    dy = end.y - start.y
    distance = math.hypot(dx, dy)

    if distance < settings.swipe_min_distance_px:
        return None
    # Must be predominantly horizontal to count as a left/right swipe.
    if abs(dy) > abs(dx) * 0.6:
        return None

    confidence = min(1.0, distance / (settings.swipe_min_distance_px * 1.6))
    return ("SWIPE_LEFT" if dx < 0 else "SWIPE_RIGHT", confidence)


def classify_dynamic(samples: list[MotionSample]) -> tuple[str, float] | None:
    """Returns (internal_gesture_id, confidence) for the recent motion
    history, or None if no dynamic gesture is currently in progress."""
    if len(samples) < 5:
        return None

    duration = samples[-1].t - samples[0].t
    if duration <= 0:
        return None

    detectors = (
        _detect_wave,
        lambda s: _detect_circle_or_orbit(s, duration),
        _detect_rotate,
        lambda s: _detect_swipe(s, duration),
    )

    for detector in detectors:
        result = detector(samples)
        if result is not None:
            return result

    return None


def dynamic_gesture_label(gesture_id: str) -> str:
    return DYNAMIC_GESTURE_META.get(gesture_id, (gesture_id, "UNKNOWN"))[0]


def dynamic_gesture_command(gesture_id: str) -> str:
    return DYNAMIC_GESTURE_META.get(gesture_id, ("Unknown", "UNKNOWN"))[1]
