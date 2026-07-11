"""
DroneRuntime bundles everything needed to operate ONE drone: its
`DroneInterface`, its own `CommandValidator` (so duplicate-detection state
never leaks between drones), its own `CommandQueue`, and its own
telemetry/state broadcast channels.

Keyed by `drone_id` in a module-level registry. Only one drone is created
at startup by default (`settings.default_drone_id`), but the registry
supports more — `ensure_runtime_running` is the seam multi-drone fleets
extend from: it connects the drone AND starts its background command
consumer + telemetry loop the first time a given `drone_id` is used,
so a lazily-created runtime is immediately fully operational rather than
silently inert (a runtime that exists but never advances because nothing
is driving its queue or physics tick).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.config import settings
from app.core.command_queue import CommandQueue
from app.core.command_validator import CommandValidator
from app.core.connection_manager import ConnectionManager
from app.drone.drone_factory import create_drone
from app.drone.drone_interface import DroneInterface


@dataclass
class DroneRuntime:
    drone_id: str
    drone: DroneInterface
    validator: CommandValidator = field(default_factory=CommandValidator)
    queue: CommandQueue = field(default_factory=CommandQueue)
    telemetry_ws: ConnectionManager = field(default_factory=ConnectionManager)
    state_ws: ConnectionManager = field(default_factory=ConnectionManager)
    consumer_task: asyncio.Task | None = field(default=None, repr=False)
    telemetry_task: asyncio.Task | None = field(default=None, repr=False)
    started: bool = False


_runtimes: dict[str, DroneRuntime] = {}
_start_lock = asyncio.Lock()


def get_or_create_runtime(drone_id: str | None = None) -> DroneRuntime:
    """Synchronous lookup/creation ONLY — does not connect the drone or
    start its background tasks. Prefer `ensure_runtime_running` from any
    async context (every REST/WebSocket handler and app startup), which
    is what actually makes a runtime operational. This sync version
    exists for the rare case where only the object (not a running drone)
    is needed.
    """
    resolved_id = drone_id or settings.default_drone_id
    if resolved_id not in _runtimes:
        _runtimes[resolved_id] = DroneRuntime(drone_id=resolved_id, drone=create_drone(resolved_id))
    return _runtimes[resolved_id]


async def ensure_runtime_running(drone_id: str | None = None) -> DroneRuntime:
    """Returns a fully operational `DroneRuntime` for `drone_id`: connected,
    with its command consumer and telemetry loop already running. Safe to
    call repeatedly/concurrently — the connect+spawn step happens exactly
    once per drone_id.
    """
    runtime = get_or_create_runtime(drone_id)
    if runtime.started:
        return runtime

    async with _start_lock:
        if runtime.started:  # re-check after acquiring the lock
            return runtime

        # Deferred imports: both modules import `DroneRuntime` (the type)
        # from this file, so importing them at module load time here would
        # be circular. They're only needed once, at first-start.
        from app.services.command_service import run_command_consumer
        from app.services.telemetry_service import run_telemetry_loop

        await runtime.drone.connect()
        runtime.consumer_task = asyncio.create_task(run_command_consumer(runtime))
        runtime.telemetry_task = asyncio.create_task(run_telemetry_loop(runtime))
        runtime.started = True

    return runtime


async def shutdown_runtime(runtime: DroneRuntime) -> None:
    for task in (runtime.consumer_task, runtime.telemetry_task):
        if task is not None:
            task.cancel()
    await asyncio.gather(
        *(t for t in (runtime.consumer_task, runtime.telemetry_task) if t is not None),
        return_exceptions=True,
    )
    await runtime.drone.disconnect()


async def shutdown_all_runtimes() -> None:
    for runtime in all_runtimes():
        await shutdown_runtime(runtime)


def all_runtimes() -> list[DroneRuntime]:
    return list(_runtimes.values())

