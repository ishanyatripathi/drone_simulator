import { FLIGHT_CONFIG as CFG } from '@/config/flightConfig';
import type { ControlInput } from '@/types/command.types';
import type { DroneTelemetry, FlightMode } from '@/types/drone.types';
import { HOME_GPS } from '@/types/drone.types';
import { clamp, dampTo, normalizeHeadingDeg, DEG2RAD, RAD2DEG } from '@/utils/math';

/**
 * PhysicsEngine
 * -------------
 * The final stage of the pipeline:
 *
 *   Keyboard → CommandQueue → DroneController → PhysicsEngine → Drone
 *
 * Takes a resolved ControlInput plus the previous tick's DroneTelemetry and
 * integrates a new telemetry snapshot: position, velocity, attitude
 * (pitch/roll/yaw), motor RPM, battery, and flight-mode state machine.
 * Nothing in this file knows about keyboards, gestures, or React — it is a
 * pure simulation core so it can be unit tested and reused untouched by
 * Phase 2.
 */
export class PhysicsEngine {
  private maxTiltRad = CFG.maxTiltAngleDeg * DEG2RAD;

  step(input: ControlInput, prev: DroneTelemetry, dt: number, lastCommand: string): DroneTelemetry {
    const t: DroneTelemetry = structuredCloneTelemetry(prev);
    t.lastCommand = lastCommand;
    t.warnings = [];

    if (input.reset) {
      return resetTelemetry();
    }

    if (input.emergencyStop && t.flightMode !== 'EMERGENCY' && t.flightMode !== 'DISARMED') {
      t.flightMode = 'EMERGENCY';
      t.warnings.push('EMERGENCY STOP ENGAGED');
    }

    t.flightMode = this.updateFlightMode(t.flightMode, input, t.altitude);
    t.armed = t.flightMode !== 'DISARMED';

    this.integrateVertical(t, dt);
    this.integrateHorizontal(t, input, dt);
    this.integrateAttitude(t, input, dt);
    this.integrateMotorRPM(t, dt);
    this.integrateBattery(t, dt);
    this.integrateGPS(t);

    t.flightTimeSeconds = t.armed ? prev.flightTimeSeconds + dt : prev.flightTimeSeconds;
    t.speed = Math.hypot(t.velocity.x, t.velocity.z);
    t.verticalSpeed = t.velocity.y;
    t.heading = normalizeHeadingDeg(t.rotation.y * RAD2DEG);
    t.distanceFromHome = Math.hypot(t.position.x - t.homePosition.x, t.position.z - t.homePosition.z);

    this.collectWarnings(t);

    return t;
  }

  private updateFlightMode(mode: FlightMode, input: ControlInput, altitude: number): FlightMode {
    if (mode === 'EMERGENCY') {
      return altitude <= 0.05 ? 'DISARMED' : 'EMERGENCY';
    }

    switch (mode) {
      case 'DISARMED':
        return input.takeoff ? 'TAKING_OFF' : 'DISARMED';
      case 'IDLE':
      case 'LANDED':
        return input.takeoff ? 'TAKING_OFF' : 'DISARMED';
      case 'TAKING_OFF':
        return altitude >= CFG.hoverAltitude - 0.15 ? 'HOVER' : 'TAKING_OFF';
      case 'HOVER': {
        if (input.land) return 'LANDING';
        const hasStickInput = input.pitch !== 0 || input.roll !== 0 || input.yaw !== 0 || input.throttle !== 0;
        return hasStickInput ? 'FLYING' : 'HOVER';
      }
      case 'FLYING': {
        if (input.land) return 'LANDING';
        const hasStickInput = input.pitch !== 0 || input.roll !== 0 || input.yaw !== 0 || input.throttle !== 0;
        return hasStickInput || input.hover === false ? (hasStickInput ? 'FLYING' : 'HOVER') : 'HOVER';
      }
      case 'LANDING':
        return altitude <= 0.05 ? 'DISARMED' : 'LANDING';
      default:
        return mode;
    }
  }

  private integrateVertical(t: DroneTelemetry, dt: number): void {
    let targetVy = 0;

    if (t.flightMode === 'TAKING_OFF') {
      targetVy = CFG.takeoffClimbRate;
    } else if (t.flightMode === 'LANDING') {
      targetVy = -CFG.landingDescendRate;
    } else if (t.flightMode === 'EMERGENCY') {
      t.velocity.y = clamp(t.velocity.y + CFG.emergencyFallAccel * dt, -12, 0);
      t.position.y = Math.max(CFG.groundLevel, t.position.y + t.velocity.y * dt);
      return;
    } else if (t.flightMode === 'HOVER' || t.flightMode === 'FLYING') {
      targetVy = 0; // overridden below via manual throttle
    } else {
      t.velocity.y = dampTo(t.velocity.y, 0, CFG.verticalAccelSmoothing, dt);
      t.position.y = Math.max(CFG.groundLevel, t.position.y + t.velocity.y * dt);
      return;
    }

    t.velocity.y = dampTo(t.velocity.y, targetVy, CFG.verticalAccelSmoothing, dt);
    t.position.y = Math.max(CFG.groundLevel, t.position.y + t.velocity.y * dt);
    t.altitude = t.position.y;
  }

  private integrateHorizontal(t: DroneTelemetry, input: ControlInput, dt: number): void {
    const flyable = t.flightMode === 'HOVER' || t.flightMode === 'FLYING';
    const yaw = t.rotation.y;

    let targetVx = 0;
    let targetVz = 0;
    let targetVy = t.velocity.y;

    if (flyable) {
      const forwardX = Math.sin(yaw);
      const forwardZ = -Math.cos(yaw);
      const rightX = Math.cos(yaw);
      const rightZ = Math.sin(yaw);

      targetVx = (input.pitch * forwardX + input.roll * rightX) * CFG.maxHorizontalSpeed;
      targetVz = (input.pitch * forwardZ + input.roll * rightZ) * CFG.maxHorizontalSpeed;
      targetVy = dampTo(t.velocity.y, input.throttle * CFG.maxVerticalSpeed, CFG.verticalAccelSmoothing, dt);
    } else {
      targetVy = t.velocity.y;
    }

    t.velocity.x = dampTo(t.velocity.x, targetVx, CFG.horizontalAccelSmoothing, dt);
    t.velocity.z = dampTo(t.velocity.z, targetVz, CFG.horizontalAccelSmoothing, dt);
    if (flyable) {
      t.velocity.y = targetVy;
    }

    const bound = CFG.worldBounds;
    t.position.x = clamp(t.position.x + t.velocity.x * dt, -bound, bound);
    t.position.z = clamp(t.position.z + t.velocity.z * dt, -bound, bound);

    if (flyable) {
      t.position.y = Math.max(CFG.groundLevel, t.position.y + t.velocity.y * dt);
      t.altitude = t.position.y;
    }
  }

  private integrateAttitude(t: DroneTelemetry, input: ControlInput, dt: number): void {
    const flyable = t.flightMode === 'HOVER' || t.flightMode === 'FLYING' || t.flightMode === 'TAKING_OFF';

    // Yaw is integrated (a rate), not smoothed toward a target angle.
    if (flyable && (t.flightMode === 'FLYING' || t.flightMode === 'HOVER')) {
      const yawRateRad = (CFG.maxYawRate * DEG2RAD) * input.yaw;
      t.rotation.y += yawRateRad * dt;
    }

    // Pitch/roll lean proportional to commanded stick deflection — this is
    // what makes the drone "lean into" the direction of travel instead of
    // moving like a rigid, robotic box.
    const targetPitch = flyable ? -input.pitch * this.maxTiltRad : 0;
    const targetRoll = flyable ? input.roll * this.maxTiltRad : 0;

    const smoothing = flyable && (input.pitch !== 0 || input.roll !== 0) ? CFG.tiltSmoothing : CFG.levelSmoothing;

    t.rotation.x = dampTo(t.rotation.x, targetPitch, smoothing, dt);
    t.rotation.z = dampTo(t.rotation.z, targetRoll, smoothing, dt);

    t.targetRotation = { x: targetPitch, y: t.rotation.y, z: targetRoll };
  }

  private integrateMotorRPM(t: DroneTelemetry, dt: number): void {
    let target: number = CFG.motorIdleRPM;

    if (t.flightMode === 'EMERGENCY') {
      target = CFG.motorIdleRPM;
    } else if (t.flightMode === 'TAKING_OFF' || t.flightMode === 'LANDING') {
      target = CFG.motorHoverRPM * 1.08;
    } else if (t.flightMode === 'HOVER') {
      target = CFG.motorHoverRPM;
    } else if (t.flightMode === 'FLYING') {
      const activity = clamp(t.speed / CFG.maxHorizontalSpeed, 0, 1);
      target = CFG.motorHoverRPM + activity * (CFG.motorMaxRPM - CFG.motorHoverRPM);
    }

    const base = dampTo(t.motorRPM[0], target, CFG.motorRPMSmoothing, dt);
    // Slight per-motor variance for realism (different corners work harder
    // during roll/pitch maneuvers).
    const variance = clamp(Math.abs(t.rotation.z) + Math.abs(t.rotation.x), 0, 1) * 220;
    t.motorRPM = [base + variance, base - variance, base - variance, base + variance] as [
      number,
      number,
      number,
      number,
    ];
  }

  private integrateBattery(t: DroneTelemetry, dt: number): void {
    let drain: number = CFG.batteryDrainIdlePerSec;
    if (t.flightMode === 'FLYING') drain = CFG.batteryDrainFlyingPerSec;
    else if (t.flightMode === 'HOVER' || t.flightMode === 'TAKING_OFF' || t.flightMode === 'LANDING')
      drain = CFG.batteryDrainHoverPerSec;

    t.batteryPercent = clamp(t.batteryPercent - drain * dt, 0, 100);
  }

  private integrateGPS(t: DroneTelemetry): void {
    const metersPerDegLat = CFG.gpsMetersPerDegLat;
    const metersPerDegLon = metersPerDegLat * Math.cos(HOME_GPS.lat * DEG2RAD);
    t.gps = {
      lat: HOME_GPS.lat + t.position.z / metersPerDegLat,
      lon: HOME_GPS.lon + t.position.x / metersPerDegLon,
      satellites: t.gps.satellites,
    };
  }

  private collectWarnings(t: DroneTelemetry): void {
    if (t.batteryPercent <= CFG.criticalBatteryWarningPct) {
      t.warnings.push('CRITICAL BATTERY');
    } else if (t.batteryPercent <= CFG.lowBatteryWarningPct) {
      t.warnings.push('LOW BATTERY');
    }
    if (t.distanceFromHome > CFG.maxFlightRadius) {
      t.warnings.push('OUT OF RANGE');
    }
    if (t.flightMode === 'EMERGENCY') {
      t.warnings.push('MOTORS CUT — DESCENDING');
    }
    if (t.altitude > 45) {
      t.warnings.push('ALTITUDE LIMIT APPROACHING');
    }
  }
}

function structuredCloneTelemetry(t: DroneTelemetry): DroneTelemetry {
  return {
    position: { ...t.position },
    velocity: { ...t.velocity },
    rotation: { ...t.rotation },
    targetRotation: { ...t.targetRotation },
    altitude: t.altitude,
    speed: t.speed,
    verticalSpeed: t.verticalSpeed,
    heading: t.heading,
    batteryPercent: t.batteryPercent,
    motorRPM: [...t.motorRPM] as [number, number, number, number],
    flightMode: t.flightMode,
    armed: t.armed,
    gps: { ...t.gps },
    homePosition: { ...t.homePosition },
    distanceFromHome: t.distanceFromHome,
    flightTimeSeconds: t.flightTimeSeconds,
    warnings: [...t.warnings],
    lastCommand: t.lastCommand,
    connectionQuality: t.connectionQuality,
  };
}

function resetTelemetry(): DroneTelemetry {
  return {
    position: { x: 0, y: 0, z: 0 },
    velocity: { x: 0, y: 0, z: 0 },
    rotation: { x: 0, y: 0, z: 0 },
    targetRotation: { x: 0, y: 0, z: 0 },
    altitude: 0,
    speed: 0,
    verticalSpeed: 0,
    heading: 0,
    batteryPercent: 100,
    motorRPM: [0, 0, 0, 0],
    flightMode: 'DISARMED',
    armed: false,
    gps: { lat: HOME_GPS.lat, lon: HOME_GPS.lon, satellites: 14 },
    homePosition: { x: 0, y: 0, z: 0 },
    distanceFromHome: 0,
    flightTimeSeconds: 0,
    warnings: [],
    lastCommand: 'RESET',
    connectionQuality: 100,
  };
}
