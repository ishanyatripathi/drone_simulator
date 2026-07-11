"""
Stability filter — the safety-critical gate between "classifier thinks it
saw a gesture this frame" and "a command is actually emitted".

Per spec, a gesture must:
  1. Exceed a >95% confidence threshold.
  2. Remain the SAME gesture continuously for >= 500ms (confirmation).
  3. Respect a >= 300ms cooldown after each emitted command.

A small amount of frame-drop tolerance (`max_dropped_frames`) absorbs
single-frame detection blips (motion blur, brief occlusion) without
resetting an otherwise-stable hold, since real camera input is noisy.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import settings


@dataclass
class StabilityFilter:
    candidate: str | None = None
    candidate_start: float | None = None
    dropped_frames: int = 0
    last_emit_time: float | None = None

    def update(self, gesture_id: str | None, confidence: float, now: float | None = None) -> tuple[str, float] | None:
        """Feed one frame's raw classification result. Returns
        (gesture_id, confidence) exactly once a gesture is confirmed and
        clears cooldown, otherwise None.
        """
        t = now if now is not None else time.monotonic()

        if gesture_id is None or confidence < settings.min_gesture_confidence:
            self.dropped_frames += 1
            if self.dropped_frames > settings.max_dropped_frames:
                self._reset_candidate()
            return None

        self.dropped_frames = 0

        if gesture_id != self.candidate:
            self.candidate = gesture_id
            self.candidate_start = t
            return None

        assert self.candidate_start is not None
        held_ms = (t - self.candidate_start) * 1000
        if held_ms < settings.confirmation_window_ms:
            return None

        if self.last_emit_time is not None:
            since_last_ms = (t - self.last_emit_time) * 1000
            if since_last_ms < settings.cooldown_ms:
                return None

        self.last_emit_time = t
        # Re-arm: the SAME gesture must be freshly re-confirmed after the
        # cooldown before firing again, which naturally throttles a held
        # gesture to one command roughly every (confirmation + cooldown).
        self.candidate_start = t

        return gesture_id, confidence

    def _reset_candidate(self) -> None:
        self.candidate = None
        self.candidate_start = None
        self.dropped_frames = 0

    def reset(self) -> None:
        self._reset_candidate()
        self.last_emit_time = None
