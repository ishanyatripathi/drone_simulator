"""
DroneInterface — the single abstraction point between this backend's API
surface (REST + WebSockets, command validation, state machine, flight
logs) and whatever is actually flying.

>>> THIS IS EXACTLY WHERE REAL DRONE INTEGRATION HAPPENS. <<<

`SimulatedDrone` (simulated_drone.py) implements this contract with an
in-process physics approximation. A real vehicle integration — MAVSDK,
pymavlink, PX4's ROS 2 bridge, whatever — is a NEW class that implements
the same contract (see `real_drone_stub.py` for exactly which methods to
fill in) and is registered in `drone_factory.py`. Nothing in
`core/`, `services/`, or `api/` needs to change, and the frontend's API
contract (REST responses, WebSocket message shapes) is identical either
way — that's the whole point of this abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.command import CommandName
from app.models.state import DroneState
from app.models.telemetry import Telemetry


class DroneInterface(ABC):
    """Every concrete drone backend (simulated or real) implements this."""

    drone_id: str

    @abstractmethod
    async def connect(self) -> None:
        """Establish the underlying connection (open the sim, or connect
        to a real vehicle's MAVLink/MAVSDK link) and transition out of
        DISCONNECTED."""

    @abstractmethod
    async def apply_command(self, command: CommandName, target_state: DroneState) -> None:
        """Actuate a command that has ALREADY been validated and approved
        by the state machine. `target_state` is the state the command
        should result in; this method is responsible for making that
        happen (immediately for discrete commands, or by setting a target
        the physics/vehicle converges toward for continuous ones) and for
        updating whatever this implementation considers its own current
        state.
        """

    @abstractmethod
    async def tick(self, dt: float) -> None:
        """Advance one simulation step (for a simulated drone) or poll/
        refresh cached telemetry (for a real vehicle). Called on a fixed
        interval by `services/telemetry_service.py`."""

    @abstractmethod
    def get_telemetry(self) -> Telemetry:
        """Returns the current cached telemetry snapshot."""

    @abstractmethod
    def get_state(self) -> DroneState:
        """Returns the current authoritative flight state."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down the connection cleanly."""
