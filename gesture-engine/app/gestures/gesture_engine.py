"""
GestureEngine ties together, per session:
  1. Per-hand static pose classification (single frame)
  2. Two-hand combined gesture detection (HOVER, EMERGENCY_STOP), which
     takes priority over single-hand readings when both hands are visible
  3. Independent stability filters (confidence + 500ms hold + 300ms
     cooldown) for the two-hand channel and for each hand's single-hand
     channel

...and returns the list of gestures CONFIRMED this frame. Everything
upstream of this file is CV; everything downstream only ever sees clean,
debounced gesture events.

NOTE (Phase 2.1 remap): the current gesture vocabulary is entirely
static/pose-based — there are no motion-based gestures anymore, so the
`motion_tracker` / `dynamic_classifier` modules are no longer wired in
here. They're left in place (unused) rather than deleted, in case a
future phase reintroduces motion gestures.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.config import settings
from app.gestures.landmark_utils import dist, hand_scale, palm_center
from app.gestures.stability_filter import StabilityFilter
from app.gestures.static_classifier import classify_static, static_gesture_command, static_gesture_label
from app.vision.hand_tracker import HandResult

# Two-hand combined gestures are resolved here (not in static_classifier.py)
# since they require seeing both hands at once.
TWO_HAND_GESTURE_META: dict[str, tuple[str, str]] = {
    "HOVER_POSE": ("Both Open Palms", "HOVER"),
    "EMERGENCY_CROSS_POSE": ("Crossed Hands", "EMERGENCY_STOP"),
}

# Per-hand poses that are superseded by a two-hand reading when both hands
# are simultaneously open (either side-by-side -> HOVER, or overlapping ->
# EMERGENCY_STOP), so they never fire alongside the two-hand gesture.
_SUPPRESSED_WHEN_TWO_HANDED = {"MOVE_LEFT_POSE", "MOVE_RIGHT_POSE"}


@dataclass
class ConfirmedGesture:
    kind: str  # "static" | "dual"
    gesture_id: str
    label: str
    command: str
    confidence: float
    hand: str  # "Left" | "Right" | "Both"


@dataclass
class HandChannel:
    static_filter: StabilityFilter = field(default_factory=StabilityFilter)


class GestureEngine:
    """One instance per active session (see `session/session_manager.py`),
    so concurrent users/cameras never share debounce state.
    """

    def __init__(self) -> None:
        self._channels: dict[str, HandChannel] = {}
        # Dedicated stability filter for the two-hand channel, entirely
        # separate from each hand's own filter, so a held single-hand pose
        # never blocks (or is blocked by) the two-hand gesture's debounce.
        self._two_hand_filter = StabilityFilter()

    def process(self, hand_results: list[HandResult], frame_w: int, frame_h: int) -> list[ConfirmedGesture]:
        now = time.monotonic()
        confirmed: list[ConfirmedGesture] = []
        seen_labels: set[str] = {h.hand_label for h in hand_results}

        right_hand = next((h for h in hand_results if h.hand_label == "Right"), None)
        left_hand = next((h for h in hand_results if h.hand_label == "Left"), None)

        both_open, crossed, two_hand_confidence = self._evaluate_two_hand_state(right_hand, left_hand)

        # --- Two-hand channel (highest priority: checked and confirmed
        # independently of, and before, any single-hand gesture) ---
        two_hand_pose_id: str | None = None
        if crossed:
            two_hand_pose_id = "EMERGENCY_CROSS_POSE"
        elif both_open:
            two_hand_pose_id = "HOVER_POSE"

        two_hand_out = self._two_hand_filter.update(two_hand_pose_id, two_hand_confidence, now)
        if two_hand_out is not None:
            gid, conf = two_hand_out
            label, command = TWO_HAND_GESTURE_META[gid]
            confirmed.append(
                ConfirmedGesture(kind="dual", gesture_id=gid, label=label, command=command, confidence=conf, hand="Both")
            )

        # --- Per-hand single-hand channel ---
        for hand in hand_results:
            channel = self._channels.setdefault(hand.hand_label, HandChannel())

            static_result = classify_static(hand.landmarks, hand.hand_label)
            if static_result is not None and static_result[0] in _SUPPRESSED_WHEN_TWO_HANDED and (both_open or crossed):
                static_result = None  # superseded by the two-hand reading above

            if static_result is not None:
                pose_id, pose_conf = static_result
                combined = pose_conf * hand.handedness_confidence
                out = channel.static_filter.update(pose_id, combined, now)
                if out is not None:
                    gid, conf = out
                    confirmed.append(
                        ConfirmedGesture(
                            kind="static",
                            gesture_id=gid,
                            label=static_gesture_label(gid),
                            command=static_gesture_command(gid),
                            confidence=conf,
                            hand=hand.hand_label,
                        )
                    )
            else:
                channel.static_filter.update(None, 0.0, now)

        # Hands that dropped out of frame this tick: decay their filters so
        # stale confirmations can't linger indefinitely.
        for label, channel in self._channels.items():
            if label not in seen_labels:
                channel.static_filter.update(None, 0.0, now)

        return confirmed

    @staticmethod
    def _evaluate_two_hand_state(right_hand: HandResult | None, left_hand: HandResult | None) -> tuple[bool, bool, float]:
        """Returns (both_open, crossed, confidence). Both are False (and
        confidence 0) unless both hands are visible and both individually
        read as an open palm. `crossed` additionally requires the two
        palms to be close together / overlapping in frame — a pragmatic
        proxy for "hands crossed in front of the camera", since MediaPipe
        Hands tracks hands only, not forearms.
        """
        if right_hand is None or left_hand is None:
            return False, False, 0.0

        right_pose = classify_static(right_hand.landmarks, "Right")
        left_pose = classify_static(left_hand.landmarks, "Left")
        right_is_open = right_pose is not None and right_pose[0] == "MOVE_RIGHT_POSE"
        left_is_open = left_pose is not None and left_pose[0] == "MOVE_LEFT_POSE"

        if not (right_is_open and left_is_open):
            return False, False, 0.0

        rx, ry, _ = palm_center(right_hand.landmarks)
        lx, ly, _ = palm_center(left_hand.landmarks)
        avg_scale = (hand_scale(right_hand.landmarks) + hand_scale(left_hand.landmarks)) / 2
        normalized_distance = dist((rx, ry, 0.0), (lx, ly, 0.0)) / avg_scale

        confidence = min(right_hand.handedness_confidence, left_hand.handedness_confidence)
        is_crossed = normalized_distance < settings.crossed_hands_max_distance
        return True, is_crossed, confidence

    def reset(self) -> None:
        self._channels.clear()
        self._two_hand_filter.reset()
