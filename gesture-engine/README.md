# AERIS Gesture Engine (Phase 2)

A Python computer-vision service that replaces keyboard input with hand
gesture recognition for the AERIS simulator. It opens a webcam, detects
hands with MediaPipe, classifies static and dynamic gestures, debounces
them for safety, and streams confirmed commands to the frontend over a
WebSocket — it never controls the drone directly.

```
Webcam → OpenCV → MediaPipe Hands → Gesture Classifiers → Stability Filter
                                                                 ↓
                                                          WebSocket (JSON)
                                                                 ↓
                                              Frontend GestureInputManager
                                                                 ↓
                                         Existing CommandQueue (Phase 1, untouched)
                                                                 ↓
                                              DroneController → PhysicsEngine
```

Simulator physics, the command queue, and the drone controller from Phase
1 are **not modified**. This service only ever emits abstract command
envelopes; `src/core/gestureCommandMap.ts` in the frontend decides how
each one is (or isn't) translated into an existing `CommandType`.

## Setup

```bash
cd gesture-engine
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # http://localhost:8000
```

Requires a webcam accessible to OpenCV (`cv2.VideoCapture`). No GPU
required — MediaPipe Hands runs on CPU in real time.

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Service status |
| `GET /api/health` | Health check + active session count |
| `GET /api/cameras` | Best-effort enumeration of available camera indices |
| `GET /api/gestures` | Full supported gesture vocabulary (id, kind, label, command) |
| `WS /ws/gestures?camera=<index>` | Live pipeline: streams `frame` and `command` messages |

## WebSocket Message Types

```jsonc
// Sent once per connection
{ "type": "status", "payload": { "state": "connected", "session_id": "..." } }

// Sent every processed frame (annotated JPEG + landmarks, for the live preview UI)
{ "type": "frame", "payload": {
    "frame_jpeg_b64": "...",
    "hands": [{ "hand": "Right", "handedness_confidence": 0.98, "landmarks": [...21 pts...], "bounding_box": [x,y,w,h] }],
    "fps": 28.4,
    "frame_index": 512
} }

// Sent only when a gesture is CONFIRMED (post safety-gate)
{ "type": "command", "payload": {
    "command": "TAKEOFF",
    "gesture": "Thumbs Up",
    "confidence": 0.99,
    "timestamp": 1735689600000,
    "kind": "static",
    "hand": "Right",
    "session_id": "..."
} }
```

## Architecture (`app/`)

```
config.py                  # every tunable threshold/timing constant in one place
models/                    # pydantic wire-format models
vision/
  camera_manager.py        # threaded, multi-camera-capable frame capture
  hand_tracker.py          # MediaPipe Hands wrapper: detect + draw + confidence
gestures/
  landmark_utils.py        # geometry helpers (finger extension, spread, angles, thumb direction)
  static_classifier.py     # single-frame hand pose -> gesture (handedness-aware)
  motion_tracker.py         # rolling position/rotation history per hand (currently unused — no dynamic gestures in the active vocabulary; kept for a future phase)
  dynamic_classifier.py    # motion history -> swipe/rotate/circle/orbit/wave (currently unused, see above)
  stability_filter.py      # >95% confidence, 500ms hold, 300ms cooldown gate
  gesture_engine.py        # per-hand + two-hand combined gesture resolution, per session
commands/
  command_mapper.py        # canonical gesture -> command vocabulary registry
session/
  session_manager.py       # one isolated GestureEngine + camera ref per connection
server/
  websocket_routes.py      # the real-time capture/classify/broadcast loop
  rest_routes.py           # health/camera/gesture-list endpoints
```

### Why sessions exist

Each WebSocket connection gets its own `GestureSession`, which owns its
own `HandTracker` and `GestureEngine` (and therefore its own debounce
state). Multiple sessions can point at the same physical camera (shared
via `CameraManager`, keyed by camera index) or different ones. This is
what makes multi-user and multi-camera support additive rather than a
rewrite: supporting another concurrent operator is just "accept another
WebSocket connection."

## Safety Behavior

Per spec, every confirmed command satisfies all of:

- **Confidence > 95%** — computed as `pose_or_motion_score × handedness_confidence`, both of which must be high.
- **500ms confirmation** — the *same* gesture must be observed continuously (with a small tolerance for dropped frames) before it counts.
- **300ms cooldown** — after emitting, no new command emits until the cooldown elapses AND the gesture is freshly re-confirmed, which naturally throttles a held gesture to roughly one command per ~800ms rather than flooding the queue.

This logic lives entirely in `gestures/stability_filter.py` and is
covered by the behavior described in its docstring — it is intentionally
independent of any specific gesture, so it applies uniformly to static
and dynamic channels.

## Gesture Vocabulary (Phase 2.1 remap)

Every gesture below is a static hand pose — there are no motion/dynamic
gestures in the current vocabulary. Ten are single-hand (handedness
matters: the *same* finger pose can mean something different on the left
vs. right hand), and two are two-hand combined gestures.

### Single-hand

| Gesture | Pose | Hand | Command |
|---|---|---|---|
| 👍 Thumbs Up | Thumb only extended, pointing up | Right | `TAKEOFF` |
| 👎 Thumbs Down | Thumb only extended, pointing down | Right | `LAND` |
| 👍→ Thumb Right | Thumb only extended, pointing right | Right | `ROTATE_RIGHT` |
| ←👍 Thumb Left | Thumb only extended, pointing left | Left | `ROTATE_LEFT` |
| 🤘 Rock Sign | Index + pinky extended, others curled | Right | `MOVE_FORWARD` |
| 🤘 Rock Sign | Index + pinky extended, others curled | Left | `MOVE_BACKWARD` |
| 🤙 Pinky Out | Pinky only extended | Right | `ASCEND` |
| 🤙 Pinky Out | Pinky only extended | Left | `DESCEND` |
| ✋ Open Palm | All 5 fingers extended | Right | `MOVE_RIGHT` |
| 🤚 Open Palm | All 5 fingers extended | Left | `MOVE_LEFT` |

### Two-hand (resolved in `gesture_engine.py`, not the per-hand classifier)

| Gesture | Motion/Pose | Command |
|---|---|---|
| 👐 Both Open Palms | Both hands open, held apart | `HOVER` |
| ❌ Crossed Hands | Both hands open, palms overlapping/crossed in frame | `EMERGENCY_STOP` (highest priority) |

Two-hand gestures take priority over single-hand readings: when both
hands are simultaneously open, each hand's individual "open palm ->
MOVE_LEFT/MOVE_RIGHT" reading is suppressed in favor of the combined
gesture, so they never fire at the same time. "Crossed" is detected as a
pragmatic proxy — palm-center proximity/overlap — since MediaPipe Hands
tracks hands only, not forearms; see `GestureEngine._evaluate_two_hand_state`.

MediaPipe is configured for `max_num_hands=2` (see `app/config.py`) to
support these two-hand gestures.


## Configuration

All thresholds are overridable via environment variables prefixed
`AERIS_GESTURE_`, e.g.:

```bash
AERIS_GESTURE_MIN_GESTURE_CONFIDENCE=0.97 AERIS_GESTURE_PORT=8001 python run.py
```

See `app/config.py` for the full list.
