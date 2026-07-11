"""
Canonical registry of every gesture this engine can recognize and the
abstract command name it produces. Kept in one place so the frontend
mapping table (src/core/gestureCommandMap.ts) can be kept in sync by
inspection.

NOTE: command names here are the gesture engine's own vocabulary. The
frontend decides how (or whether) to translate each one into an existing
`CommandType` for the flight simulator — this backend never assumes the
consumer is any particular frontend.
"""

from __future__ import annotations

from app.gestures.gesture_engine import TWO_HAND_GESTURE_META, ConfirmedGesture
from app.gestures.static_classifier import STATIC_GESTURE_META
from app.models.command import GestureCommand

FULL_GESTURE_VOCABULARY: dict[str, tuple[str, str, str]] = {
    **{k: ("static", *v) for k, v in STATIC_GESTURE_META.items()},
    **{k: ("dual", *v) for k, v in TWO_HAND_GESTURE_META.items()},
}


def build_gesture_command(confirmed: ConfirmedGesture, session_id: str | None) -> GestureCommand:
    return GestureCommand(
        command=confirmed.command,
        gesture=confirmed.label,
        confidence=round(confirmed.confidence, 4),
        kind=confirmed.kind,
        hand=confirmed.hand,
        session_id=session_id,
    )


def list_supported_gestures() -> list[dict]:
    return [
        {"id": gid, "kind": kind, "label": label, "command": command}
        for gid, (kind, label, command) in FULL_GESTURE_VOCABULARY.items()
    ]
