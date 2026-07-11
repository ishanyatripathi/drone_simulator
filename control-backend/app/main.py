from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_routes, rest_routes, websocket_routes
from app.config import settings
from app.services.drone_runtime import ensure_runtime_running, get_or_create_runtime, shutdown_all_runtimes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("aeris.control_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = await ensure_runtime_running(settings.default_drone_id)
    logger.info("Default drone '%s' connected; background tasks started.", runtime.drone_id)

    yield

    await shutdown_all_runtimes()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="AERIS Control Backend",
    description=(
        "Control-plane service between the gesture engine and the drone "
        "(simulated today; MAVLink/PX4-ready — see app/drone/)."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api")
app.include_router(rest_routes.router)
app.include_router(websocket_routes.router)


@app.get("/")
def root() -> dict:
    return {"service": "aeris-control-backend", "status": "running"}


@app.get("/health")
def health() -> dict:
    # Safe as a synchronous lookup: the default drone is always started by
    # `lifespan` before the app begins serving requests, so this never
    # creates a fresh, unconnected runtime — it only ever finds the
    # already-running one.
    runtime = get_or_create_runtime(settings.default_drone_id)
    return {
        "status": "ok",
        "default_drone": runtime.drone_id,
        "drone_state": runtime.drone.get_state().value,
        "drone_backend": settings.drone_backend,
    }

