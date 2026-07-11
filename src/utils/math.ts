export const DEG2RAD = Math.PI / 180;
export const RAD2DEG = 180 / Math.PI;

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Framerate-independent exponential smoothing (critically damped feel). */
export function dampTo(current: number, target: number, smoothing: number, dt: number): number {
  const t = 1 - Math.exp(-smoothing * dt);
  return lerp(current, target, t);
}

export function shortestAngleDeltaRad(from: number, to: number): number {
  let diff = (to - from) % (Math.PI * 2);
  if (diff > Math.PI) diff -= Math.PI * 2;
  if (diff < -Math.PI) diff += Math.PI * 2;
  return diff;
}

export function normalizeHeadingDeg(deg: number): number {
  let h = deg % 360;
  if (h < 0) h += 360;
  return h;
}
