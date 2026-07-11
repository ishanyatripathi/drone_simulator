"""
SimulatedDrone — the default `DroneInterface` implementation.

A deliberately lightweight, headless physics approximation (exponential
velocity damping, a simple climb/descend ramp, derived GPS) — enough to
drive believable telemetry and exercise the full validator/state-machine/
command-queue pipeline without depending on the frontend's Three.js
simulator at all. This is what gets swapped out for a real vehicle later
(see `drone_interface.py` for the contract and `real_drone_stub.py` for
where that integration goes).
"""

from __future__ import annotations

import math
import time

from app.config import settings
from app.drone.drone_interface import DroneInterface
from app.models.command import CommandName
from app.models.state import DroneState
from app.models.telemetry import GPSCoordinate, Telemetry

_HOME_LAT = 19.0760
_HOME_LON = 72.8777
_METERS_PER_DEG_LAT = 111_320.0

# Movement intents auto-decay to hover if no fresh movement command
# arrives within this window — a safety net so the sim doesn't fly off
# forever from one stale gesture.
_INTENT_TIMEOUT_S = 1.5


def _damp(current: float, target: float, smoothing: float, dt: float) -> float:
    t = 1 - math.exp(-smoothing * dt)
    return current + (target - current) * t


class SimulatedDrone(DroneInterface):
    def __init__(self, drone_id: str) -> None:
        self.drone_id = drone_id
        self._state = DroneState.DISCONNECTED
        self._battery = 100.0
        self._altitude = 0.0
        self._x = 0.0
        self._z = 0.0
        self._vx = 0.0
        self._vz = 0.0
        self._vy = 0.0
        self._yaw_deg = 0.0
        self._pitch_deg = 0.0
        self._roll_deg = 0.0
        self._motor_rpm = [0.0, 0.0, 0.0, 0.0]
        self._current_command = "NONE"
        self._armed = False

        self._intent_pitch = 0.0
        self._intent_roll = 0.0
        self._intent_yaw = 0.0
        self._intent_throttle = 0.0
        self._last_movement_ts = time.monotonic()
        self._emergency = False

    # --- DroneInterface contract -------------------------------------------------

    async def connect(self) -> None:
        self._state = DroneState.CONNECTED
        self._current_command = "CONNECT"

    async def apply_command(self, command: CommandName, target_state: DroneState) -> None:
        self._current_command = command.value
        now = time.monotonic()

        if command == CommandName.RESET:
            self._reset_internal()
            self._state = target_state
            return

        if command == CommandName.EMERGENCY_STOP:
            self._emergency = True
            self._intent_pitch = self._intent_roll = self._intent_yaw = 0.0
            self._state = target_state
            return

        if command == CommandName.TAKEOFF:
            self._armed = True
            self._emergency = False
            self._state = target_state
            return

        if command == CommandName.LAND:
            self._state = target_state
            return

        if command == CommandName.HOVER:
            self._intent_pitch = self._intent_roll = self._intent_yaw = self._intent_throttle = 0.0
            self._state = target_state
            return

        # Continuous/movement commands.
        self._state = target_state
        self._last_movement_ts = now
        if command == CommandName.MOVE_FORWARD:
            self._intent_pitch = 1.0
        elif command == CommandName.MOVE_BACKWARD:
            self._intent_pitch = -1.0
        elif command == CommandName.MOVE_LEFT:
            self._intent_roll = -1.0
        elif command == CommandName.MOVE_RIGHT:
            self._intent_roll = 1.0
        elif command == CommandName.ASCEND:
            self._intent_throttle = 1.0
        elif command == CommandName.DESCEND:
            self._intent_throttle = -1.0
        elif command == CommandName.ROTATE_LEFT:
            self._intent_yaw = -1.0
        elif command == CommandName.ROTATE_RIGHT:
            self._intent_yaw = 1.0

    async def tick(self, dt: float) -> None:
        self._auto_advance_state(dt)
        self._integrate_attitude_and_motion(dt)
        self._integrate_battery(dt)
        self._integrate_motor_rpm(dt)
        self._auto_decay_intents()

    def get_telemetry(self) -> Telemetry:
        lat = _HOME_LAT + self._z / _METERS_PER_DEG_LAT
        lon_scale = _METERS_PER_DEG_LAT * math.cos(math.radians(_HOME_LAT))
        lon = _HOME_LON + self._x / max(lon_scale, 1e-6)

        return Telemetry(
            drone_id=self.drone_id,
            battery_percent=round(self._battery, 2),
            altitude_m=round(self._altitude, 2),
            gps=GPSCoordinate(lat=round(lat, 6), lon=round(lon, 6), satellites=14),
            velocity_mps=round(math.hypot(self._vx, self._vz), 2),
            yaw_deg=round(self._yaw_deg % 360, 1),
            pitch_deg=round(self._pitch_deg, 1),
            roll_deg=round(self._roll_deg, 1),
            motor_rpm=[round(r, 0) for r in self._motor_rpm],
            connection="connected" if self._state != DroneState.DISCONNECTED else "disconnected",
            mode=self._state,
            current_command=self._current_command,
            armed=self._armed,
        )

    def get_state(self) -> DroneState:
        return self._state

    async def disconnect(self) -> None:
        self._state = DroneState.DISCONNECTED
        self._armed = False

    # --- Internal physics ---------------------------------------------------

    def _reset_internal(self) -> None:
        self._battery = 100.0
        self._altitude = 0.0
        self._x = self._z = 0.0
        self._vx = self._vz = self._vy = 0.0
        self._yaw_deg = self._pitch_deg = self._roll_deg = 0.0
        self._motor_rpm = [0.0, 0.0, 0.0, 0.0]
        self._armed = False
        self._emergency = False
        self._intent_pitch = self._intent_roll = self._intent_yaw = self._intent_throttle = 0.0
        self._current_command = "RESET"

    def _auto_advance_state(self, dt: float) -> None:
        if self._state == DroneState.ARMED:
            self._state = DroneState.TAKEOFF
        elif self._state == DroneState.TAKEOFF:
            self._altitude = min(settings.hover_altitude_m, self._altitude + settings.climb_rate_mps * dt)
            if self._altitude >= settings.hover_altitude_m - 0.1:
                self._state = DroneState.HOVER
        elif self._state == DroneState.LANDING:
            rate = settings.descend_rate_mps * (2.5 if self._emergency else 1.0)
            self._altitude = max(0.0, self._altitude - rate * dt)
            if self._altitude <= 0.02:
                self._state = DroneState.DISARMED
                self._armed = False
                self._emergency = False

    def _integrate_attitude_and_motion(self, dt: float) -> None:
        flyable = self._state in (DroneState.HOVER, DroneState.MISSION)

        target_vx = target_vz = target_vy = 0.0
        if flyable:
            yaw_rad = math.radians(self._yaw_deg)
            forward_x, forward_z = math.sin(yaw_rad), -math.cos(yaw_rad)
            right_x, right_z = math.cos(yaw_rad), math.sin(yaw_rad)
            target_vx = (self._intent_pitch * forward_x + self._intent_roll * right_x) * settings.max_horizontal_speed_mps
            target_vz = (self._intent_pitch * forward_z + self._intent_roll * right_z) * settings.max_horizontal_speed_mps
            target_vy = self._intent_throttle * settings.climb_rate_mps
            self._yaw_deg += settings.max_yaw_rate_deg_s * self._intent_yaw * dt

        self._vx = _damp(self._vx, target_vx, 3.0, dt)
        self._vz = _damp(self._vz, target_vz, 3.0, dt)
        self._vy = _damp(self._vy, target_vy, 3.0, dt)

        if flyable:
            self._x += self._vx * dt
            self._z += self._vz * dt
            self._altitude = max(0.0, self._altitude + self._vy * dt)

        target_pitch = -self._intent_pitch * 22 if flyable else 0.0
        target_roll = self._intent_roll * 22 if flyable else 0.0
        self._pitch_deg = _damp(self._pitch_deg, target_pitch, 4.0, dt)
        self._roll_deg = _damp(self._roll_deg, target_roll, 4.0, dt)

    def _integrate_battery(self, dt: float) -> None:
        airborne = self._state not in (DroneState.DISCONNECTED, DroneState.CONNECTED, DroneState.DISARMED)
        drain = settings.battery_drain_airborne_pct_s if airborne else settings.battery_drain_idle_pct_s
        self._battery = max(0.0, self._battery - drain * dt)

    def _integrate_motor_rpm(self, dt: float) -> None:
        target = 0.0
        if self._state in (DroneState.TAKEOFF, DroneState.LANDING):
            target = 3450.0
        elif self._state == DroneState.HOVER:
            target = 3200.0
        elif self._state == DroneState.MISSION:
            activity = min(1.0, math.hypot(self._vx, self._vz) / settings.max_horizontal_speed_mps)
            target = 3200.0 + activity * 3200.0

        base = _damp(self._motor_rpm[0], target, 6.0, dt)
        variance = min(1.0, abs(math.radians(self._roll_deg)) + abs(math.radians(self._pitch_deg))) * 200
        self._motor_rpm = [base + variance, base - variance, base - variance, base + variance]

    def _auto_decay_intents(self) -> None:
        if self._state != DroneState.MISSION:
            return
        if time.monotonic() - self._last_movement_ts > _INTENT_TIMEOUT_S:
            self._intent_pitch = self._intent_roll = self._intent_yaw = self._intent_throttle = 0.0
            self._state = DroneState.HOVER
            self._current_command = "AUTO_HOVER"
