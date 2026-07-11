"""
FlightLogger — records every command attempt, accepted or rejected, per
spec: timestamp, gesture, confidence, executed command, and resulting
drone state.

Kept in an in-memory ring buffer (fast reads for `GET /logs`) and
appended to a JSON Lines file so history survives a process restart.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from app.config import settings
from app.models.log import FlightLogEntry


class FlightLogger:
    def __init__(self, path: str | None = None, max_in_memory: int | None = None) -> None:
        self._path = Path(path or settings.flight_log_path)
        self._entries: deque[FlightLogEntry] = deque(maxlen=max_in_memory or settings.flight_log_max_in_memory)

    def record(self, entry: FlightLogEntry) -> None:
        self._entries.append(entry)
        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except OSError:
            # Persistence is best-effort — an unwritable log path should
            # never take down command processing.
            pass

    def list(self, limit: int = 100, drone_id: str | None = None) -> list[FlightLogEntry]:
        entries = list(self._entries)
        if drone_id is not None:
            entries = [e for e in entries if e.drone_id == drone_id]
        return list(reversed(entries))[:limit]

    @staticmethod
    def load_from_disk(path: str | None = None, limit: int = 500) -> list[FlightLogEntry]:
        """Best-effort load of the most recent `limit` entries from the
        JSONL file, e.g. to warm the in-memory cache on startup."""
        p = Path(path or settings.flight_log_path)
        if not p.exists():
            return []
        lines = p.read_text(encoding="utf-8").splitlines()[-limit:]
        entries: list[FlightLogEntry] = []
        for line in lines:
            try:
                entries.append(FlightLogEntry(**json.loads(line)))
            except (json.JSONDecodeError, ValueError):
                continue
        return entries


flight_logger = FlightLogger()
