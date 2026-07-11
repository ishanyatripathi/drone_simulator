from __future__ import annotations

import time

from pydantic import BaseModel, Field

from app.models.state import DroneState


class GPSCoordinate(BaseModel):
    lat: float
    lon: float
    satellites: int


class Telemetry(BaseModel):
    """Canonical telemetry snapshot. Whether this data originates from the
    in-process `SimulatedDrone` or, later, a MAVLink telemetry stream, the
    shape returned to REST/WebSocket clients never changes.
    """

    drone_id: str
    battery_percent: float = Field(ge=0, le=100)
    altitude_m: float
    gps: GPSCoordinate
    velocity_mps: float
    yaw_deg: float
    pitch_deg: float
    roll_deg: float
    motor_rpm: list[float] = Field(min_length=4, max_length=4)
    connection: str  # "connected" | "disconnected"
    mode: DroneState
    current_command: str
    armed: bool
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
