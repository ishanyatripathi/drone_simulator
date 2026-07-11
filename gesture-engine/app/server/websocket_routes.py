"""
The real-time pipeline, per connection:

  camera frame -> HandTracker.process -> GestureEngine.process
      -> confirmed gestures -> GestureCommand -> WebSocket (JSON)
  (annotated frame is also JPEG-encoded and streamed alongside, at a
   throttled rate, purely for the frontend's live preview panel.)

This file intentionally contains almost no logic of its own — it is glue
between the vision/gesture layers and the wire format.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time

import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.commands.command_mapper import build_gesture_command
from app.config import settings
from app.models.landmarks import FrameMessage, HandDetection, Landmark
from app.session.session_manager import session_manager

logger = logging.getLogger("aeris.gesture_engine")
router = APIRouter()


def _encode_frame_b64(frame) -> str:
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, settings.jpeg_quality])
    if not ok:
        return ""
    return base64.b64encode(buf).decode("ascii")


def _to_hand_detection(hand) -> HandDetection:
    return HandDetection(
        hand=hand.hand_label,
        handedness_confidence=round(hand.handedness_confidence, 4),
        landmarks=[Landmark(x=p[0], y=p[1], z=p[2]) for p in hand.landmarks],
        bounding_box=hand.bounding_box,
    )


@router.websocket("/ws/gestures")
async def gesture_socket(websocket: WebSocket, camera: int | None = Query(default=None)):
    await websocket.accept()
    session = session_manager.create(camera_index=camera)
    logger.info(
        "session %s opened (camera=%s, active=%s)",
        session.session_id,
        session.camera_index,
        session_manager.active_count,
    )

    await websocket.send_json({"type": "status", "payload": {"state": "connected", "session_id": session.session_id}})

    frame_interval = 1 / max(settings.target_fps, 1)
    fps_smoothed = float(settings.target_fps)
    last_loop_t = time.monotonic()

    try:
        while True:
            loop_start = time.monotonic()

            frame = session.camera.read()
            if frame is None:
                await asyncio.sleep(0.05)
                continue

            annotated, hand_results = session.hand_tracker.process(frame)
            h, w = frame.shape[:2]

            confirmed = session.gesture_engine.process(hand_results, frame_w=w, frame_h=h)

            for gesture in confirmed:
                command = build_gesture_command(gesture, session_id=session.session_id)
                await websocket.send_json({"type": "command", "payload": command.model_dump()})
                logger.info(
                    "session %s CONFIRMED %s (%s) -> %s @ %.1f%%",
                    session.session_id,
                    gesture.label,
                    gesture.kind,
                    gesture.command,
                    gesture.confidence * 100,
                )

            session.frame_index += 1
            now = time.monotonic()
            dt = max(now - last_loop_t, 1e-6)
            last_loop_t = now
            fps_smoothed = fps_smoothed * 0.9 + (1 / dt) * 0.1

            frame_msg = FrameMessage(
                frame_jpeg_b64=_encode_frame_b64(annotated),
                hands=[_to_hand_detection(h) for h in hand_results],
                fps=round(fps_smoothed, 1),
                frame_index=session.frame_index,
            )
            await websocket.send_json({"type": "frame", "payload": frame_msg.model_dump()})

            elapsed = time.monotonic() - loop_start
            await asyncio.sleep(max(0.0, frame_interval - elapsed))

    except WebSocketDisconnect:
        logger.info("session %s disconnected", session.session_id)
    except Exception:  # noqa: BLE001 - log and let the connection close cleanly
        logger.exception("session %s crashed", session.session_id)
    finally:
        session_manager.destroy(session.session_id)
