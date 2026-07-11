"""Maintains a short rolling history of hand position/orientation samples
used to detect dynamic (motion-based) gestures such as swipes, rotations,
circles, and waves.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class MotionSample:
    t: float  # seconds
    x: float  # pixel-space palm center x
    y: float  # pixel-space palm center y
    roll_deg: float


@dataclass
class MotionTracker:
    """One instance per tracked hand within a session."""

    history: deque[MotionSample] = field(default_factory=deque)

    def add(self, x: float, y: float, roll_deg: float, t: float | None = None) -> None:
        now = t if t is not None else time.monotonic()
        self.history.append(MotionSample(now, x, y, roll_deg))
        self._trim(now)

    def _trim(self, now: float) -> None:
        window = settings.motion_history_seconds
        while self.history and (now - self.history[0].t) > window:
            self.history.popleft()

    def clear(self) -> None:
        self.history.clear()

    def samples(self) -> list[MotionSample]:
        return list(self.history)

    def duration(self) -> float:
        if len(self.history) < 2:
            return 0.0
        return self.history[-1].t - self.history[0].t
