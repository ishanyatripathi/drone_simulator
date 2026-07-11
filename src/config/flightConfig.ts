/**
 * Central tuning table for flight physics. Keeping every magic number here
 * makes the simulator easy to re-balance without hunting through the
 * physics engine logic.
 */
export const FLIGHT_CONFIG = {
  maxHorizontalSpeed: 9, // m/s
  maxVerticalSpeed: 4.5, // m/s
  maxYawRate: 110, // deg/s

  horizontalAccelSmoothing: 3.2, // higher = snappier response
  verticalAccelSmoothing: 2.6,
  yawSmoothing: 4.5,

  maxTiltAngleDeg: 24, // max pitch/roll lean while moving
  tiltSmoothing: 5,
  levelSmoothing: 3.5, // how fast it re-levels when hovering

  hoverAltitude: 6, // meters, default takeoff altitude
  takeoffClimbRate: 2.2, // m/s during automated takeoff
  landingDescendRate: 1.4, // m/s during automated landing
  groundLevel: 0,

  emergencyFallAccel: -14, // m/s^2, free-fall style drop

  batteryDrainHoverPerSec: 0.012, // % per second while airborne
  batteryDrainFlyingPerSec: 0.028, // % per second while actively moving
  batteryDrainIdlePerSec: 0.002,
  lowBatteryWarningPct: 20,
  criticalBatteryWarningPct: 8,

  motorIdleRPM: 0,
  motorHoverRPM: 3200,
  motorMaxRPM: 6400,
  motorRPMSmoothing: 6,

  maxFlightRadius: 220, // meters from home before "too far" warning
  gpsMetersPerDegLat: 111_320,

  worldBounds: 260, // soft collision boundary, meters from origin
} as const;
