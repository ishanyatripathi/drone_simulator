"""
TelemetryService — the background loop that advances a drone's simulation
(or, for a real vehicle, polls/refreshes cached telemetry) and broadcasts
snapshots to `/ws/telemetry_stream` subscribers at a steady rate.
"""

from __future__ import annotations

import asyncio
import logging
import time

from app.config import settings
from app.services.drone_runtime import DroneRuntime

logger = logging.getLogger("aeris.control_backend")


async def run_telemetry_loop(runtime: DroneRuntime) -> None:
    tick_interval = 1 / max(settings.tick_hz, 1e-3)
    broadcast_interval = 1 / max(settings.telemetry_broadcast_hz, 1e-3)

    last_tick = time.monotonic()
    last_broadcast = 0.0

    while True:
        now = time.monotonic()
        dt = now - last_tick
        last_tick = now

        try:
            await runtime.drone.tick(dt)
        except Exception:  # noqa: BLE001 - a tick failure must not kill the loop
            logger.exception("Telemetry tick failed for %s", runtime.drone_id)

        if now - last_broadcast >= broadcast_interval:
            last_broadcast = now
            telemetry = runtime.drone.get_telemetry()
            await runtime.telemetry_ws.broadcast_json(telemetry.model_dump(mode="json"))

        await asyncio.sleep(tick_interval)
