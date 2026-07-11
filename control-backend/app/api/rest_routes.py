from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user
from app.core.flight_log import flight_logger
from app.models.command import CommandName, CommandResult
from app.models.log import FlightLogEntry
from app.models.telemetry import Telemetry
from app.services.command_service import submit_command
from app.services.drone_runtime import ensure_runtime_running

router = APIRouter(tags=["control"], dependencies=[Depends(get_current_user)])


@router.get("/telemetry", response_model=Telemetry)
async def get_telemetry(drone_id: str | None = Query(default=None)) -> Telemetry:
    runtime = await ensure_runtime_running(drone_id)
    return runtime.drone.get_telemetry()


@router.get("/logs", response_model=list[FlightLogEntry])
def get_logs(
    limit: int = Query(default=100, ge=1, le=500),
    drone_id: str | None = Query(default=None),
) -> list[FlightLogEntry]:
    return flight_logger.list(limit=limit, drone_id=drone_id)


@router.get("/state")
async def get_state(drone_id: str | None = Query(default=None)) -> dict:
    runtime = await ensure_runtime_running(drone_id)
    return {"drone_id": runtime.drone_id, "state": runtime.drone.get_state().value}


async def _submit(command: CommandName, drone_id: str | None) -> CommandResult:
    runtime = await ensure_runtime_running(drone_id)
    result = await submit_command(runtime, command.value, source="rest")
    if not result.accepted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result.reason)
    return result


@router.post("/takeoff", response_model=CommandResult)
async def takeoff(drone_id: str | None = Query(default=None)) -> CommandResult:
    return await _submit(CommandName.TAKEOFF, drone_id)


@router.post("/land", response_model=CommandResult)
async def land(drone_id: str | None = Query(default=None)) -> CommandResult:
    return await _submit(CommandName.LAND, drone_id)


@router.post("/hover", response_model=CommandResult)
async def hover(drone_id: str | None = Query(default=None)) -> CommandResult:
    return await _submit(CommandName.HOVER, drone_id)


@router.post("/reset", response_model=CommandResult)
async def reset(drone_id: str | None = Query(default=None)) -> CommandResult:
    return await _submit(CommandName.RESET, drone_id)
