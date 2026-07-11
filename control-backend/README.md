# AERIS Control Backend (Phase 3)

The control-plane service between the gesture engine (or any input
source) and a drone — simulated today, a real MAVLink/PX4 vehicle
tomorrow, with **no API changes** either way.

```
Gesture Engine (Phase 2) / REST clients
              |
              v
     /ws/gesture_stream, POST /takeoff|/land|/hover|/reset
              |
              v
     CommandValidator   (rejects impossible transitions + duplicates)
              |
              v
     DroneStateMachine  (pure transition table, consulted BY the validator)
              |
              v
     CommandQueue        (asyncio.Queue — decouples ingestion from actuation)
              |
              v
     DroneInterface.apply_command()
              |
              v
     SimulatedDrone  (today)  ──or──  MAVSDKDrone / PX4MavlinkDrone (future)
```

## Setup

```bash
cd control-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # http://localhost:8100
```

Demo credentials (see `app/config.py`, override via env vars):
`operator` / `aeris123`.

## Authentication

`POST /api/auth/token` with `{"username": "...", "password": "..."}`
returns a JWT bearer token. Every REST endpoint below requires
`Authorization: Bearer <token>`. Every WebSocket requires the same token
as a `?token=` query parameter (browsers can't set arbitrary headers on a
plain WebSocket handshake, so a query param is the standard pragmatic
approach) — connections without a valid token are closed with code
`4401`.

## REST Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/token` | Log in, get a bearer token |
| GET | `/telemetry` | Current telemetry snapshot |
| GET | `/logs?limit=100` | Recent flight log entries |
| GET | `/state` | Current state-machine state |
| POST | `/takeoff` | Submit `TAKEOFF` |
| POST | `/land` | Submit `LAND` |
| POST | `/hover` | Submit `HOVER` |
| POST | `/reset` | Submit `RESET` |

All accept an optional `?drone_id=` query param (defaults to
`settings.default_drone_id`, `"sim-01"`). A rejected command returns
**HTTP 409** with the rejection reason in `detail`.

## WebSocket Streams

| Path | Direction | Purpose |
|---|---|---|
| `/ws/gesture_stream` | inbound | Submit commands: `{"command": "TAKEOFF", "gesture": "Right Thumbs Up", "confidence": 0.99}`. Acknowledged with `{"type": "command_result", "payload": {...}}` per message. |
| `/ws/telemetry_stream` | outbound | Broadcasts a `Telemetry` snapshot ~10x/sec (`settings.telemetry_broadcast_hz`). |
| `/ws/state_stream` | outbound | Broadcasts a `StateTransitionEvent` every time the state machine actually changes state. |

The gesture engine's own WebSocket schema (`gesture-engine/app/models/command.py`)
already matches the `{command, gesture, confidence}` shape `/ws/gesture_stream`
expects — pointing the gesture engine (or the frontend's `GestureInputManager`)
at this endpoint instead of connecting straight to the frontend requires no
schema translation.

## The Drone State Machine

Eight states, per spec: `DISCONNECTED → CONNECTED → ARMED → TAKEOFF →
HOVER ⇄ MISSION → LANDING → DISARMED`. The full legal-transition table
lives in `app/core/state_machine.py`. Two commands are special-cased:

- `RESET` is legal from **any** state and always returns to `CONNECTED`.
- `EMERGENCY_STOP` is legal from any armed/airborne state (`ARMED`,
  `TAKEOFF`, `HOVER`, `MISSION`, `LANDING`) and forces `LANDING` at an
  accelerated descent rate.

`ARMED → TAKEOFF → HOVER` and `LANDING → DISARMED` happen automatically
(no command needed) as the simulated drone's altitude crosses thresholds
— see `SimulatedDrone._auto_advance_state`.

## Command Validation

`app/core/command_validator.py` rejects two classes of command, per spec:

1. **Impossible state transitions** — e.g. `LAND` while already
   `DISARMED`/`CONNECTED`, or `TAKEOFF` while already `ARMED`/`HOVER`/
   `MISSION`. Determined by asking `DroneStateMachine.next_state()`
   whether the current state is in the command's legal source-state set;
   `None` means illegal.
2. **Duplicate commands** — the exact same command resubmitted for the
   same drone within `settings.duplicate_command_window_ms` (400ms
   default) is rejected, independent of state legality.

Every attempt — accepted or rejected — is written to the flight log
(`app/core/flight_log.py`, `GET /logs`), including the gesture and
confidence when the source was `/ws/gesture_stream`.

## Where Real Drone Integration Happens

This is the answer to "where does MAVLink/PX4 support go":

1. **`app/drone/drone_interface.py`** — the abstract contract
   (`connect`, `apply_command`, `tick`, `get_telemetry`, `get_state`,
   `disconnect`). This is the ONLY boundary the rest of the backend
   depends on. Nothing in `core/`, `services/`, or `api/` imports
   `SimulatedDrone` directly — they all talk to a `DroneInterface`.

2. **`app/drone/real_drone_stub.py`** — `MAVSDKDrone` and
   `PX4MavlinkDrone`, two classes that already implement this contract's
   *shape* but raise `NotImplementedError` in every method. Each
   docstring sketches exactly which MAVSDK/pymavlink call belongs in each
   method (e.g. `apply_command(TAKEOFF, ...)` → `action.arm()` then
   `action.takeoff()`; `MOVE_FORWARD` → `offboard.set_velocity_body(...)`).
   Implementing real drone support is filling in these method bodies —
   nothing else in the codebase needs to change.

3. **`app/drone/drone_factory.py`** — the single switch. Once a stub
   class above is implemented, setting
   `AERIS_BACKEND_DRONE_BACKEND=mavsdk` (or `px4`) in the environment is
   the entire cutover from simulated to real flight. `app/config.py`'s
   `drone_backend` setting is the only thing that changes.

4. **Everything upstream is already vehicle-agnostic.** The REST
   responses, WebSocket message shapes, state machine, validator, and
   flight log all operate purely in terms of `DroneInterface`,
   `Telemetry`, `DroneState`, and `CommandName` — none of which reference
   the simulator. The frontend (and the gesture engine) never need to
   know or care whether `/telemetry` is being served by `SimulatedDrone`
   or a real PX4 vehicle over MAVLink.

## Folder Structure

```
app/
  config.py              # every tunable in one place, including drone_backend
  models/                # pydantic wire-format models (auth, command, state, telemetry, log)
  auth/                  # JWT issuing/verification, REST + WebSocket auth dependencies
  core/
    state_machine.py      # pure 8-state transition table
    command_validator.py  # state-legality + duplicate rejection
    command_queue.py       # asyncio.Queue decoupling validation from actuation
    flight_log.py          # in-memory + JSONL-persisted flight log
    connection_manager.py  # WebSocket broadcast registry (telemetry/state streams)
  drone/
    drone_interface.py     # <-- the real-drone integration boundary
    simulated_drone.py     # default DroneInterface implementation
    real_drone_stub.py     # <-- MAVSDK/PX4 integration goes here
    drone_factory.py       # <-- the one-line cutover switch
  services/
    drone_runtime.py       # per-drone bundle: interface + validator + queue + broadcasters
    command_service.py     # orchestrates validate -> queue -> apply -> log -> broadcast
    telemetry_service.py   # background tick + telemetry broadcast loop
  api/
    auth_routes.py
    rest_routes.py
    websocket_routes.py
```
