"""
Factory for the active `DroneInterface` implementation.

This is the SECOND (and only other) place real-drone integration touches:
once `MAVSDKDrone` or `PX4MavlinkDrone` (see `real_drone_stub.py`) is
actually implemented, switching production traffic from the simulator to
a real vehicle is exactly:

    AERIS_BACKEND_DRONE_BACKEND=mavsdk

...with zero changes anywhere else in this backend, and zero changes in
the frontend.
"""

from __future__ import annotations

from app.config import settings
from app.drone.drone_interface import DroneInterface
from app.drone.simulated_drone import SimulatedDrone


def create_drone(drone_id: str) -> DroneInterface:
    backend = settings.drone_backend.lower()

    if backend == "simulated":
        return SimulatedDrone(drone_id)

    if backend == "mavsdk":
        from app.drone.real_drone_stub import MAVSDKDrone

        return MAVSDKDrone(drone_id)

    if backend == "px4":
        from app.drone.real_drone_stub import PX4MavlinkDrone

        return PX4MavlinkDrone(drone_id)

    raise ValueError(f"Unknown AERIS_BACKEND_DRONE_BACKEND: '{settings.drone_backend}'")
