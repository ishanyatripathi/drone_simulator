"""
>>> REAL DRONE INTEGRATION GOES HERE. <<<

These classes are the intended landing spot for real-vehicle support.
Each implements the exact same `DroneInterface` contract as
`SimulatedDrone`, so once one of them is finished, switching
`AERIS_BACKEND_DRONE_BACKEND=mavsdk` (or `px4`) in configuration is the
ONLY change required — `core/`, `services/`, and `api/` are untouched,
and the frontend's REST/WebSocket contract does not change at all.

Neither class is wired up or imported by `drone_factory.py` yet; they
raise `NotImplementedError` so nobody accidentally ships a half-built
vehicle connection. Fill in the method bodies using the MAVSDK Python
library (https://mavsdk.mavlink.io/main/en/python/) or pymavlink,
whichever the deployment target prefers.
"""

from __future__ import annotations

from app.drone.drone_interface import DroneInterface
from app.models.command import CommandName
from app.models.state import DroneState
from app.models.telemetry import Telemetry


class MAVSDKDrone(DroneInterface):
    """Real-vehicle integration via MAVSDK (`pip install mavsdk`).

    Sketch of what each method should do once implemented:

      connect()
        `self._system = mavsdk.System()`
        `await self._system.connect(system_address="udp://:14540")`
        await the first `self._system.core.connection_state()` that
        reports `is_connected`, then set state -> CONNECTED.

      apply_command(command, target_state)
        TAKEOFF        -> `await self._system.action.arm()` then
                          `await self._system.action.takeoff()`
        LAND           -> `await self._system.action.land()`
        HOVER          -> hold current `offboard` setpoint at zero velocity
        MOVE_*/ASCEND/DESCEND/ROTATE_*
                       -> translate the intent into a
                          `mavsdk.offboard.VelocityBodyYawspeed` and call
                          `await self._system.offboard.set_velocity_body(...)`
                          (requires `offboard.start()` once, on entering MISSION)
        RESET          -> `await self._system.action.return_to_launch()`
        EMERGENCY_STOP -> `await self._system.action.kill()` (or a fast
                          controlled descent, depending on vehicle policy)

      tick(dt)
        Nothing to integrate — MAVSDK pushes telemetry async. Instead,
        this is where you'd assert the offboard connection is still
        healthy / reconnect if it dropped.

      get_telemetry()
        Return the last cached `Telemetry`, built from subscribing to
        `self._system.telemetry.battery()`, `.position()`,
        `.attitude_euler()`, `.velocity_ned()`, etc. in a background task
        started from `connect()`, each updating a cached snapshot.

      get_state()
        Derive a `DroneState` from `self._system.telemetry.flight_mode()`
        and `.armed()`.

    None of this is implemented yet — every method below intentionally
    raises `NotImplementedError`.
    """

    def __init__(self, drone_id: str) -> None:
        self.drone_id = drone_id

    async def connect(self) -> None:
        raise NotImplementedError("MAVSDK integration not yet implemented — see class docstring.")

    async def apply_command(self, command: CommandName, target_state: DroneState) -> None:
        raise NotImplementedError("MAVSDK integration not yet implemented — see class docstring.")

    async def tick(self, dt: float) -> None:
        raise NotImplementedError("MAVSDK integration not yet implemented — see class docstring.")

    def get_telemetry(self) -> Telemetry:
        raise NotImplementedError("MAVSDK integration not yet implemented — see class docstring.")

    def get_state(self) -> DroneState:
        raise NotImplementedError("MAVSDK integration not yet implemented — see class docstring.")

    async def disconnect(self) -> None:
        raise NotImplementedError("MAVSDK integration not yet implemented — see class docstring.")


class PX4MavlinkDrone(DroneInterface):
    """Real-vehicle integration via raw MAVLink (`pip install pymavlink`)
    against a PX4 autopilot, for deployments that want direct MAVLink
    control rather than MAVSDK's higher-level API. Same contract, same
    integration point — implement using `pymavlink.mavutil.mavlink_connection`
    and PX4's COMMAND_LONG / SET_POSITION_TARGET_LOCAL_NED messages in
    place of the MAVSDK calls sketched above.
    """

    def __init__(self, drone_id: str) -> None:
        self.drone_id = drone_id

    async def connect(self) -> None:
        raise NotImplementedError("PX4/MAVLink integration not yet implemented.")

    async def apply_command(self, command: CommandName, target_state: DroneState) -> None:
        raise NotImplementedError("PX4/MAVLink integration not yet implemented.")

    async def tick(self, dt: float) -> None:
        raise NotImplementedError("PX4/MAVLink integration not yet implemented.")

    def get_telemetry(self) -> Telemetry:
        raise NotImplementedError("PX4/MAVLink integration not yet implemented.")

    def get_state(self) -> DroneState:
        raise NotImplementedError("PX4/MAVLink integration not yet implemented.")

    async def disconnect(self) -> None:
        raise NotImplementedError("PX4/MAVLink integration not yet implemented.")
