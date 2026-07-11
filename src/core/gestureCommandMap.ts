import { CommandType } from '@/types/command.types';

/**
 * Translates the gesture-engine's command vocabulary (see
 * gesture-engine/app/commands/command_mapper.py) into the simulator's
 * existing `CommandType` enum. This is the ONLY place that knows both
 * vocabularies — everything downstream of the CommandQueue is unchanged
 * from Phase 1.
 *
 * The gesture engine's ROTATE_LEFT/ROTATE_RIGHT commands map onto the
 * simulator's existing YAW_LEFT/YAW_RIGHT — rotating the drone in place
 * is a yaw maneuver, and Phase 1's physics engine has no separate
 * "rotate" flight mode, so no simulator changes were needed.
 */
export const GESTURE_COMMAND_MAP: Partial<Record<string, CommandType>> = {
  TAKEOFF: CommandType.TAKEOFF,
  LAND: CommandType.LAND,
  HOVER: CommandType.HOVER,
  MOVE_FORWARD: CommandType.MOVE_FORWARD,
  MOVE_BACKWARD: CommandType.MOVE_BACKWARD,
  MOVE_LEFT: CommandType.MOVE_LEFT,
  MOVE_RIGHT: CommandType.MOVE_RIGHT,
  ASCEND: CommandType.ASCEND,
  DESCEND: CommandType.DESCEND,
  EMERGENCY_STOP: CommandType.EMERGENCY_STOP,
  ROTATE_LEFT: CommandType.YAW_LEFT,
  ROTATE_RIGHT: CommandType.YAW_RIGHT,
};

export function resolveGestureCommand(backendCommand: string): CommandType | null {
  return GESTURE_COMMAND_MAP[backendCommand] ?? null;
}
