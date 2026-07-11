from __future__ import annotations

import time
from enum import Enum

from pydantic import BaseModel, Field


class DroneState(str, Enum):
    """The 8-state flight lifecycle, per spec. Ordering below is the
    typical happy-path progression, though RESET and EMERGENCY_STOP can
    jump from almost any state — see `core/state_machine.py`.
    """

    DISCONNECTED = "DISCONNECTED"
    CONNECTED = "CONNECTED"
    ARMED = "ARMED"
    TAKEOFF = "TAKEOFF"
    HOVER = "HOVER"
    MISSION = "MISSION"
    LANDING = "LANDING"
    DISARMED = "DISARMED"


class StateTransitionEvent(BaseModel):
    """Broadcast on `/ws/state_stream` whenever the state machine transitions."""

    drone_id: str
    previous_state: DroneState
    new_state: DroneState
    trigger_command: str | None = None
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
