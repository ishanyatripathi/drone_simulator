"""
Central configuration for the AERIS Control Backend.

This service sits between input sources (gesture engine, REST clients)
and a drone — simulated today, a real MAVLink/PX4 vehicle tomorrow — via
the `DroneInterface` abstraction in `app/drone/`. Every tunable lives here
so swapping the backing drone implementation never requires touching
validation, state-machine, or API code.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8100
    cors_origins: list[str] = ["*"]  # tighten in production deployments

    # --- Auth ---
    # Demo credentials for Phase 3. Replace with a real user store before
    # any production deployment.
    demo_username: str = "operator"
    demo_password: str = "aeris123"
    jwt_secret: str = "aeris-control-backend-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 120

    # --- Drone backend selection ---
    # "simulated" today; "mavsdk" / "px4" are reserved for real-vehicle
    # integration — see app/drone/drone_factory.py and real_drone_stub.py.
    drone_backend: str = "simulated"
    default_drone_id: str = "sim-01"

    # --- Simulated drone physics tick ---
    tick_hz: float = 20.0
    hover_altitude_m: float = 6.0
    climb_rate_mps: float = 2.2
    descend_rate_mps: float = 1.4
    max_horizontal_speed_mps: float = 9.0
    max_yaw_rate_deg_s: float = 110.0
    battery_drain_airborne_pct_s: float = 0.02
    battery_drain_idle_pct_s: float = 0.002

    # --- Command validation ---
    # Minimum time (ms) that must pass before the SAME command can be
    # resubmitted, to reject accidental duplicate submissions.
    duplicate_command_window_ms: int = 400

    # --- Telemetry / state broadcast ---
    telemetry_broadcast_hz: float = 10.0

    # --- Flight logs ---
    flight_log_path: str = "flight_logs.jsonl"
    flight_log_max_in_memory: int = 500

    class Config:
        env_prefix = "AERIS_BACKEND_"
        protected_namespaces = ()


settings = Settings()
