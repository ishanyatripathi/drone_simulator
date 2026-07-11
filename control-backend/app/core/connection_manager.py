"""Simple broadcast registry for read-only WebSocket streams
(telemetry_stream, state_stream). Each stream endpoint owns its own
ConnectionManager instance so a slow/disconnected client on one stream
never affects the other.
"""

from __future__ import annotations

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for connection in list(self._connections):
            try:
                await connection.send_json(payload)
            except Exception:  # noqa: BLE001 - a broken client shouldn't break the broadcast
                stale.append(connection)
        for connection in stale:
            await self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        return len(self._connections)
