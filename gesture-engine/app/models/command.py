"""
Wire format for commands emitted by the gesture engine.

Per spec, the gesture engine NEVER controls the drone directly — it only
ever produces these abstract command envelopes over the WebSocket. The
frontend's CommandQueue is solely responsible for translating them into
simulator action.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field


class GestureCommand(BaseModel):
    """A single confirmed, debounced gesture -> command event."""

    command: str = Field(..., description="Abstract command name, e.g. 'TAKEOFF'")
    gesture: str = Field(..., description="Human-readable gesture name, e.g. 'Thumbs Up'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
    kind: str = Field(default="static", description="'static' or 'dynamic'")
    hand: str | None = Field(default=None, description="'Left' or 'Right'")
    session_id: str | None = Field(default=None)


class GestureEventMessage(BaseModel):
    """Envelope for any message pushed to the frontend over the socket."""

    type: str  # "frame" | "command" | "status" | "error"
    payload: dict
