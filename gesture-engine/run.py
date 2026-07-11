"""Run with: python run.py  (or: uvicorn app.main:app --reload)"""

from __future__ import annotations

import os

import uvicorn

from app.config import settings

if __name__ == "__main__":
    reload_enabled = os.getenv("AERIS_GESTURE_RELOAD", "true").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=reload_enabled)
