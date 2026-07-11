from __future__ import annotations

import time
from enum import Enum

from pydantic import BaseModel, Field


class CommandName(str, Enum):
    """The full command vocabulary this backend understands, matching the
    gesture engine's current mapped commands plus the REST-exposed
    discrete actions. Unrecognized command strings are rejected by the
    validator rather than raising here, so upstream producers (e.g. a
    future gesture) can send new names without crashing this service —
    see `core/command_validator.py`.
    """

    TAKEOFF = "TAKEOFF"
    LAND = "LAND"
    HOVER = "HOVER"
    RESET = "RESET"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    MOVE_FORWARD = "MOVE_FORWARD"
    MOVE_BACKWARD = "MOVE_BACKWARD"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    ASCEND = "ASCEND"
    DESCEND = "DESCEND"
    ROTATE_LEFT = "ROTATE_LEFT"
    ROTATE_RIGHT = "ROTATE_RIGHT"


class CommandRequest(BaseModel):
    """A raw incoming command, from a REST call or the gesture WebSocket
    stream. `gesture` / `confidence` are populated only when the source is
    the gesture engine, and are carried straight through to the flight log.
    """

    command: str
    source: str = "rest"  # "rest" | "gesture_stream"
    gesture: str | None = None
    confidence: float | None = None
    drone_id: str | None = None
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)


class CommandResult(BaseModel):
    """Returned to REST callers and broadcast internally after a command
    has passed through the validator + state machine + command queue.
    """

    accepted: bool
    command: str
    reason: str | None = None
    previous_state: str | None = None
    new_state: str | None = None
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
