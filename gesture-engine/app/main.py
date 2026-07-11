from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.server import rest_routes, websocket_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="AERIS Gesture Engine",
    description="Computer-vision gesture recognition service for the AERIS UAV command system (Phase 2).",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest_routes.router, prefix="/api")
app.include_router(websocket_routes.router)


@app.get("/")
def root() -> dict:
    return {"service": "aeris-gesture-engine", "status": "running"}
