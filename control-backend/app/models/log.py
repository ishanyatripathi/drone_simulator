from __future__ import annotations

import time

from pydantic import BaseModel, Field


class FlightLogEntry(BaseModel):
    """One row per command attempt (accepted or rejected), per spec:
    timestamp, gesture, confidence, executed command, and resulting drone
    state. Persisted as JSON Lines (`app/config.py: flight_log_path`) so
    logs survive a process restart and remain trivially greppable.
    """

    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
    drone_id: str
    gesture: str | None = None
    confidence: float | None = None
    command: str
    accepted: bool
    reason: str | None = None
    drone_state: str
    source: str
