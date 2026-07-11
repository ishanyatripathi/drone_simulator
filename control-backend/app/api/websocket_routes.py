"""
The three WebSocket streams from the spec:

  /ws/gesture_stream    inbound  — gesture engine (or any client) submits
                                    commands, each run through
                                    submit_command() and acknowledged.
  /ws/telemetry_stream  outbound — subscribes to periodic telemetry
                                    broadcasts from `telemetry_service.py`.
  /ws/state_stream      outbound — subscribes to state-machine transition
                                    events broadcast by `command_service.py`.

All three require a valid bearer token as a `?token=` query parameter
(see `auth/dependencies.py::authenticate_websocket`), closing with code
4401 if missing/invalid.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.dependencies import authenticate_websocket
from app.services.command_service import submit_command
from app.services.drone_runtime import ensure_runtime_running

logger = logging.getLogger("aeris.control_backend")
router = APIRouter()

_UNAUTHORIZED_CLOSE_CODE = 4401


@router.websocket("/ws/gesture_stream")
async def gesture_stream(websocket: WebSocket, drone_id: str | None = None):
    user = await authenticate_websocket(websocket)
    if user is None:
        await websocket.close(code=_UNAUTHORIZED_CLOSE_CODE)
        return

    await websocket.accept()
    runtime = await ensure_runtime_running(drone_id)
    logger.info("gesture_stream connected (user=%s, drone=%s)", user, runtime.drone_id)

    try:
        while True:
            try:
                payload = await websocket.receive_json()
            except ValueError:
                # Malformed JSON from the client — report it and keep the
                # connection alive rather than crashing the loop.
                await websocket.send_json({"type": "error", "detail": "Malformed JSON message"})
                continue

            if not isinstance(payload, dict):
                await websocket.send_json({"type": "error", "detail": "Message must be a JSON object"})
                continue

            command = payload.get("command")
            if not command:
                await websocket.send_json({"type": "error", "detail": "Missing 'command' field"})
                continue

            try:
                result = await submit_command(
                    runtime,
                    raw_command=command,
                    source="gesture_stream",
                    gesture=payload.get("gesture"),
                    confidence=payload.get("confidence"),
                )
            except WebSocketDisconnect:
                raise
            except Exception:  # noqa: BLE001 - one bad command must not kill the connection
                logger.exception("gesture_stream failed to process command for %s", runtime.drone_id)
                await websocket.send_json({"type": "error", "detail": "Internal error processing command"})
                continue

            await websocket.send_json({"type": "command_result", "payload": result.model_dump(mode="json")})
    except WebSocketDisconnect:
        logger.info("gesture_stream disconnected (user=%s, drone=%s)", user, runtime.drone_id)


@router.websocket("/ws/telemetry_stream")
async def telemetry_stream(websocket: WebSocket, drone_id: str | None = None):
    user = await authenticate_websocket(websocket)
    if user is None:
        await websocket.close(code=_UNAUTHORIZED_CLOSE_CODE)
        return

    await websocket.accept()
    runtime = await ensure_runtime_running(drone_id)
    await runtime.telemetry_ws.connect(websocket)
    logger.info("telemetry_stream connected (user=%s, drone=%s)", user, runtime.drone_id)

    try:
        # This stream is output-only; we just wait for the client to
        # disconnect (or send anything, which is ignored) to keep the
        # connection alive.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await runtime.telemetry_ws.disconnect(websocket)
        logger.info("telemetry_stream disconnected (user=%s, drone=%s)", user, runtime.drone_id)


@router.websocket("/ws/state_stream")
async def state_stream(websocket: WebSocket, drone_id: str | None = None):
    user = await authenticate_websocket(websocket)
    if user is None:
        await websocket.close(code=_UNAUTHORIZED_CLOSE_CODE)
        return

    await websocket.accept()
    runtime = await ensure_runtime_running(drone_id)
    await runtime.state_ws.connect(websocket)
    logger.info("state_stream connected (user=%s, drone=%s)", user, runtime.drone_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await runtime.state_ws.disconnect(websocket)
        logger.info("state_stream disconnected (user=%s, drone=%s)", user, runtime.drone_id)
