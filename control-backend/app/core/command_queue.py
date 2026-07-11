"""
CommandQueue — decouples "a command was validated and approved" from
"the command was actually applied to the drone".

This matters most once the drone is real: a MAVLink/MAVSDK link has its
own latency and rate limits, and shouldn't block whoever submitted the
command (a REST caller or the gesture WebSocket). Validated commands are
placed on this queue immediately; a single background consumer task
(`services/command_service.py: run_command_consumer`) drains it and talks
to the `DroneInterface` at whatever pace that interface can handle.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.models.command import CommandName
from app.models.state import DroneState


@dataclass
class QueuedCommand:
    drone_id: str
    command: CommandName
    target_state: DroneState
    source: str
    gesture: str | None
    confidence: float | None


class CommandQueue:
    def __init__(self, max_size: int = 256) -> None:
        self._queue: asyncio.Queue[QueuedCommand] = asyncio.Queue(maxsize=max_size)

    async def put(self, item: QueuedCommand) -> None:
        await self._queue.put(item)

    async def get(self) -> QueuedCommand:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    @property
    def size(self) -> int:
        return self._queue.qsize()
