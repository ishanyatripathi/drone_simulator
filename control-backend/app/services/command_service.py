"""
CommandService — implements the exact pipeline from the spec:

    Gesture Engine / REST
            |
            v
      Command Validator   (app/core/command_validator.py)
            |
            v
      State Machine        (app/core/state_machine.py, consulted BY the validator)
            |
            v
      Command Queue        (app/core/command_queue.py)
            |
            v
      Simulator / drone    (app/drone/*, via DroneInterface.apply_command)

`submit_command` runs the validate step synchronously (it's pure, in-
memory, and fast) and, if accepted, enqueues onto the drone's
`CommandQueue` for the background consumer to apply — decoupling
ingestion from actuation exactly as the architecture requires. Every
attempt, accepted or not, is written to the flight log.
"""

from __future__ import annotations

import logging

from app.core.command_queue import QueuedCommand
from app.core.flight_log import flight_logger
from app.models.command import CommandName, CommandResult
from app.models.log import FlightLogEntry
from app.models.state import StateTransitionEvent
from app.services.drone_runtime import DroneRuntime

logger = logging.getLogger("aeris.control_backend")


async def submit_command(
    runtime: DroneRuntime,
    raw_command: str,
    source: str,
    gesture: str | None = None,
    confidence: float | None = None,
) -> CommandResult:
    current_state = runtime.drone.get_state()
    result = runtime.validator.validate(runtime.drone_id, raw_command, current_state)

    flight_logger.record(
        FlightLogEntry(
            drone_id=runtime.drone_id,
            gesture=gesture,
            confidence=confidence,
            command=raw_command,
            accepted=result.accepted,
            reason=result.reason,
            drone_state=(result.new_state or current_state).value,
            source=source,
        )
    )

    if not result.accepted:
        logger.info("REJECTED %s for %s: %s", raw_command, runtime.drone_id, result.reason)
        return CommandResult(
            accepted=False,
            command=raw_command,
            reason=result.reason,
            previous_state=current_state.value,
            new_state=None,
        )

    await runtime.queue.put(
        QueuedCommand(
            drone_id=runtime.drone_id,
            command=CommandName(raw_command),
            target_state=result.new_state,  # type: ignore[arg-type]
            source=source,
            gesture=gesture,
            confidence=confidence,
        )
    )

    return CommandResult(
        accepted=True,
        command=raw_command,
        reason=None,
        previous_state=current_state.value,
        new_state=result.new_state.value if result.new_state else None,  # type: ignore[union-attr]
    )


async def run_command_consumer(runtime: DroneRuntime) -> None:
    """Background task: drains `runtime.queue` and applies each command to
    the drone, broadcasting the resulting state transition. This is the
    ONLY place `DroneInterface.apply_command` is called, which matters
    once that interface is a real, latency-sensitive MAVLink link.
    """
    while True:
        queued = await runtime.queue.get()
        previous_state = runtime.drone.get_state()
        try:
            await runtime.drone.apply_command(queued.command, queued.target_state)
        except Exception:  # noqa: BLE001 - never let one bad command kill the consumer loop
            logger.exception("Failed to apply command %s to %s", queued.command, runtime.drone_id)
        else:
            new_state = runtime.drone.get_state()
            if new_state != previous_state:
                await runtime.state_ws.broadcast_json(
                    StateTransitionEvent(
                        drone_id=runtime.drone_id,
                        previous_state=previous_state,
                        new_state=new_state,
                        trigger_command=queued.command.value,
                    ).model_dump(mode="json")
                )
        finally:
            runtime.queue.task_done()
