"""
CommandValidator — the gate every incoming command passes through before
it can reach the state machine's decision becomes real (queued and
applied to a `DroneInterface`).

Two independent rejection reasons, per spec:
  1. Impossible state transition (e.g. LAND while already DISARMED,
     TAKEOFF while already airborne) — delegated to `DroneStateMachine`.
  2. Duplicate command — the exact same command resubmitted for the same
     drone within `settings.duplicate_command_window_ms`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import settings
from app.core.state_machine import DroneStateMachine
from app.models.command import CommandName
from app.models.state import DroneState


@dataclass
class ValidationResult:
    accepted: bool
    new_state: DroneState | None
    reason: str | None


class CommandValidator:
    def __init__(self) -> None:
        # Per-drone "last accepted command" memory, for duplicate detection.
        self._last_accepted: dict[str, tuple[CommandName, float]] = {}

    def validate(self, drone_id: str, raw_command: str, current_state: DroneState) -> ValidationResult:
        try:
            command = CommandName(raw_command)
        except ValueError:
            return ValidationResult(False, None, f"Unknown command '{raw_command}'")

        now = time.monotonic()
        last = self._last_accepted.get(drone_id)
        if last is not None:
            last_command, last_time = last
            if last_command == command and (now - last_time) * 1000 < settings.duplicate_command_window_ms:
                return ValidationResult(
                    False,
                    None,
                    f"Duplicate '{command.value}' rejected "
                    f"(resubmitted within {settings.duplicate_command_window_ms}ms)",
                )

        new_state = DroneStateMachine.next_state(command, current_state)
        if new_state is None:
            return ValidationResult(
                False,
                None,
                f"Cannot execute '{command.value}' while drone is {current_state.value}",
            )

        self._last_accepted[drone_id] = (command, now)
        return ValidationResult(True, new_state, None)

    def reset(self, drone_id: str) -> None:
        self._last_accepted.pop(drone_id, None)
