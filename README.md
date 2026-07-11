# AERIS — AI Enabled Gesture-Based UAV Command System

### Phase 1: Browser-Based Flight Simulator Core

AERIS Phase 1 is a production-grade, fully browser-based quadcopter flight
simulator — the foundation for a future gesture-controlled UAV command
system. This phase implements **no computer vision, no gesture recognition,
and no backend**. It is a self-contained React + Three.js simulator with a
modular input architecture designed so Phase 2 (hand-gesture control via
webcam/OpenCV) can be dropped in without touching flight logic.

---

## Tech Stack

- React 18 + TypeScript (strict mode)
- Vite 5
- Tailwind CSS
- Three.js + React Three Fiber + Drei
- Framer Motion
- Zustand (simulation state store)

## Getting Started

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production build -> dist/
npm run preview   # preview the production build
```

No environment variables or backend services are required.

## Architecture

Input is fully decoupled from flight physics via a four-stage pipeline:

```
Keyboard  →  CommandQueue  →  DroneController  →  PhysicsEngine  →  Drone
(input)      (buffer)          (intent resolver)   (simulation)     (render)
```

- **`core/keyboardInputManager.ts`** — the *only* file that knows about
  browser keyboard events. It maps keys to `CommandType` values and pushes
  them onto the queue. Nothing else touches raw input.
- **`core/commandQueue.ts`** — a source-agnostic FIFO buffer. Any future
  input adapter (e.g. a Phase 2 gesture classifier) enqueues the same
  `CommandType` values here — no other code changes.
- **`core/droneController.ts`** — drains the queue once per frame and
  collapses it into a normalized `ControlInput` (pitch/roll/yaw/throttle
  plus discrete flags like takeoff/land/hover/reset).
- **`core/physicsEngine.ts`** — a pure simulation core (no React, no Three.js)
  that integrates `ControlInput` into smooth position, velocity, attitude,
  motor RPM, battery, and flight-mode state every tick, using
  framerate-independent exponential damping for inertia and lean.
- **`state/droneStore.ts`** — a Zustand store gluing the pipeline together
  and exposing `telemetry` to both the 3D scene and the dashboard.

Because the physics engine only ever consumes a `ControlInput`, Phase 2 can
introduce a `GestureInputManager` that enqueues the same commands and the
entire simulation core remains unchanged.

## Controls (temporary — keyboard only, Phase 1)

| Key | Action |
|---|---|
| `W` / `S` | Pitch forward / backward |
| `A` / `D` | Roll left / right |
| `Q` / `E` | Yaw left / right |
| `SPACE` | Ascend |
| `SHIFT` | Descend |
| `H` | Hover / hold position |
| `T` | Takeoff |
| `L` | Land |
| `R` | Reset simulation |

On-screen buttons in the dashboard mirror the discrete commands (Takeoff /
Hover / Land / Reset) and an Emergency Stop control cuts the motors
immediately, for non-keyboard interaction.

## Cameras

Switchable from the top-right HUD control: **Follow**, **FPV** (nose gimbal
view), **Top** (surveillance view), **Orbit** (drone-locked orbit), and
**Free** (fully independent fly-around camera).

## Folder Structure

```
src/
  core/            # input adapters, command queue, controller, physics engine
  state/           # zustand store (single source of simulation truth)
  types/           # shared TypeScript contracts
  config/          # tunable flight-physics constants
  hooks/           # React glue (keyboard, simulation loop, FPS)
  components/
    scene/         # drone mesh, environment, cameras (R3F/Three.js)
    dashboard/      # glassmorphism HUD panels
    ui/            # generic reusable UI primitives
```

## Deployment (Vercel)

This project deploys to Vercel with zero configuration changes:

```bash
vercel deploy
```

`vercel.json` pins the framework to Vite, sets `dist` as the output
directory, and adds an SPA rewrite so client-side routing (if added later)
resolves correctly. `npm run build` is the exact command Vercel will run.

## Explicitly Out of Scope for Phase 1

- Gesture recognition / computer vision
- OpenCV or any camera/ML pipeline
- Any backend, API, or persistence layer

These are reserved for Phase 2, which will replace only the keyboard input
adapter — the command queue, controller, physics engine, dashboard, and
scene are all designed to remain untouched.

---

## Phase 2 — Gesture Recognition (added)

Phase 2 adds a standalone Python CV service in **`gesture-engine/`**
(FastAPI + OpenCV + MediaPipe + WebSockets) that recognizes static and
dynamic hand gestures from a webcam and streams confirmed commands to the
frontend in real time. See `gesture-engine/README.md` for full setup,
architecture, and the complete gesture vocabulary.

Nothing from Phase 1 was modified. The integration is entirely additive:

- `src/types/gesture.types.ts` — wire types matching the backend's JSON schema.
- `src/core/gestureCommandMap.ts` — maps the gesture engine's command vocabulary onto the existing `CommandType` enum.
- `src/core/gestureInputManager.ts` — a WebSocket client adapter, architecturally identical in role to `keyboardInputManager.ts`: it only ever enqueues commands via the same `dispatchCommand` the keyboard uses.
- `src/hooks/useGestureInput.ts` — React glue exposing connection state, the live annotated frame, and gesture history to the UI.
- `src/components/dashboard/GesturePanel.tsx` — a new dashboard panel (live webcam feed with landmarks, current gesture/confidence/command, history) — wired in via a two-line addition to `Dashboard.tsx`.

Keyboard input still works exactly as it did in Phase 1; gesture input is
a second, parallel adapter feeding the same `CommandQueue`, so both can be
used interchangeably or side by side.

To run both together:

```bash
# Terminal 1 — simulator
npm run dev

# Terminal 2 — gesture engine
cd gesture-engine && python run.py
```

Then open the app and click the ✋ button in the dashboard's top-right to
connect the camera.

---

## Phase 3 — Control Backend (added)

Phase 3 adds a second standalone Python service, **`control-backend/`**
(FastAPI + WebSockets + Pydantic + asyncio, JWT auth), that sits between
any command source (the Phase 2 gesture engine, or REST/manual calls) and
a drone — simulated today, MAVLink/PX4-ready by design. See
`control-backend/README.md` for full API reference and, most importantly,
**exactly where real-drone integration happens**
(`control-backend/app/drone/`).

Nothing from Phase 1 or Phase 2 was modified — this is a fully
independent service with its own auth, validation, state machine, and
simulated drone. It is not yet wired into the React frontend or the
gesture engine (that would be a Phase 4 integration step); today it's a
complete, independently runnable and testable control-plane API.

```bash
cd control-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py   # http://localhost:8100
```

Quick smoke test:

```bash
curl -X POST http://localhost:8100/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "operator", "password": "aeris123"}'
# -> {"access_token": "...", ...}

curl -X POST http://localhost:8100/takeoff \
  -H "Authorization: Bearer <token>"
```

