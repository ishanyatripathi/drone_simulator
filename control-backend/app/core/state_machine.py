"""
DroneStateMachine — a pure, stateless transition table.

Given a command and the drone's CURRENT state, returns the state that
command would result in, or None if the transition is illegal. This file
holds no mutable state of its own and performs no I/O — it is consulted
by `command_validator.py` before anything is queued or applied to a
`DroneInterface`, so both the simulator and a future real vehicle share
identical flight-lifecycle rules.
"""

from __future__ import annotations

from app.models.command import CommandName
from app.models.state import DroneState

# command -> (states it's legal from, the state it results in)
_TRANSITION_TABLE: dict[CommandName, tuple[frozenset[DroneState], DroneState]] = {
    CommandName.TAKEOFF: (frozenset({DroneState.CONNECTED, DroneState.DISARMED}), DroneState.ARMED),
    CommandName.LAND: (
        frozenset({DroneState.ARMED, DroneState.TAKEOFF, DroneState.HOVER, DroneState.MISSION}),
        DroneState.LANDING,
    ),
    CommandName.HOVER: (frozenset({DroneState.TAKEOFF, DroneState.MISSION}), DroneState.HOVER),
    CommandName.MOVE_FORWARD: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.MOVE_BACKWARD: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.MOVE_LEFT: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.MOVE_RIGHT: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.ASCEND: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.DESCEND: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.ROTATE_LEFT: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
    CommandName.ROTATE_RIGHT: (frozenset({DroneState.HOVER, DroneState.MISSION}), DroneState.MISSION),
}

# EMERGENCY_STOP is legal from any state where the vehicle is actually
# armed/airborne — forces an immediate (fast) landing regardless of what
# the drone was doing.
_EMERGENCY_ALLOWED_FROM = frozenset(
    {DroneState.ARMED, DroneState.TAKEOFF, DroneState.HOVER, DroneState.MISSION, DroneState.LANDING}
)


class DroneStateMachine:
    @staticmethod
    def next_state(command: CommandName, current_state: DroneState) -> DroneState | None:
        """Returns the resulting state if `command` is legal from
        `current_state`, else None."""
        if command == CommandName.RESET:
            # The universal safety reset is legal from any state.
            return DroneState.CONNECTED

        if command == CommandName.EMERGENCY_STOP:
            return DroneState.LANDING if current_state in _EMERGENCY_ALLOWED_FROM else None

        entry = _TRANSITION_TABLE.get(command)
        if entry is None:
            return None

        allowed_from, resulting_state = entry
        return resulting_state if current_state in allowed_from else None

    @staticmethod
    def allowed_states_for(command: CommandName) -> frozenset[DroneState]:
        if command == CommandName.RESET:
            return frozenset(DroneState)
        if command == CommandName.EMERGENCY_STOP:
            return _EMERGENCY_ALLOWED_FROM
        entry = _TRANSITION_TABLE.get(command)
        return entry[0] if entry else frozenset()
