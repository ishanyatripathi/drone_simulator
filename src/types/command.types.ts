/**
 * CommandType enumerates every high-level intent that can be issued to the
 * drone. This is the contract between ANY input source (keyboard in Phase 1,
 * hand-gesture recognition in Phase 2) and the DroneController.
 *
 * Input sources must never touch the drone or physics engine directly —
 * they only ever produce Commands.
 */
export enum CommandType {
  MOVE_FORWARD = 'MOVE_FORWARD',
  MOVE_BACKWARD = 'MOVE_BACKWARD',
  MOVE_LEFT = 'MOVE_LEFT',
  MOVE_RIGHT = 'MOVE_RIGHT',
  YAW_LEFT = 'YAW_LEFT',
  YAW_RIGHT = 'YAW_RIGHT',
  ASCEND = 'ASCEND',
  DESCEND = 'DESCEND',
  HOVER = 'HOVER',
  TAKEOFF = 'TAKEOFF',
  LAND = 'LAND',
  RESET = 'RESET',
  EMERGENCY_STOP = 'EMERGENCY_STOP',
}

/** Where a command originated: keyboard (Phase 1), gesture engine (Phase 2), or system/UI buttons. */
export type CommandSource = 'keyboard' | 'gesture' | 'system';

export interface Command {
  readonly type: CommandType;
  readonly source: CommandSource;
  /** Milliseconds since epoch, set at enqueue time. */
  readonly timestamp: number;
  /** Optional analog intensity 0..1 (digital keys always send 1). */
  readonly intensity?: number;
}

/** A single frame's worth of resolved control intent, produced by the
 * DroneController after collapsing all queued commands. This is what the
 * PhysicsEngine actually consumes. */
export interface ControlInput {
  pitch: number; // -1 (backward) .. 1 (forward)
  roll: number; // -1 (left) .. 1 (right)
  yaw: number; // -1 (left) .. 1 (right)
  throttle: number; // -1 (descend) .. 1 (ascend)
  hover: boolean;
  takeoff: boolean;
  land: boolean;
  reset: boolean;
  emergencyStop: boolean;
}

export const NEUTRAL_CONTROL_INPUT: ControlInput = {
  pitch: 0,
  roll: 0,
  yaw: 0,
  throttle: 0,
  hover: false,
  takeoff: false,
  land: false,
  reset: false,
  emergencyStop: false,
};
