export type FlightMode =
  | 'DISARMED'
  | 'IDLE'
  | 'TAKING_OFF'
  | 'HOVER'
  | 'FLYING'
  | 'LANDING'
  | 'LANDED'
  | 'EMERGENCY';

export interface Vector3Tuple {
  x: number;
  y: number;
  z: number;
}

export interface DroneTelemetry {
  /** World position in meters. y = altitude. */
  position: Vector3Tuple;
  /** Linear velocity in m/s. */
  velocity: Vector3Tuple;
  /** Euler angles in radians. */
  rotation: Vector3Tuple; // pitch (x), yaw (y), roll (z)
  /** Target euler angles the physics engine is smoothing towards. */
  targetRotation: Vector3Tuple;
  altitude: number; // meters AGL
  speed: number; // horizontal speed magnitude, m/s
  verticalSpeed: number; // m/s
  heading: number; // degrees 0-360
  batteryPercent: number;
  motorRPM: [number, number, number, number];
  flightMode: FlightMode;
  armed: boolean;
  gps: { lat: number; lon: number; satellites: number };
  homePosition: Vector3Tuple;
  distanceFromHome: number;
  flightTimeSeconds: number;
  warnings: string[];
  lastCommand: string;
  connectionQuality: number; // 0-100
}

export const HOME_GPS = { lat: 19.076, lon: 72.8777 } as const;

export function createInitialTelemetry(): DroneTelemetry {
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
    lastCommand: 'NONE',
    connectionQuality: 100,
  };
}

export type CameraMode = 'FOLLOW' | 'FPV' | 'TOP' | 'ORBIT' | 'FREE';
