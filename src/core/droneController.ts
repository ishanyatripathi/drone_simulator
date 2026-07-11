import { CommandType, NEUTRAL_CONTROL_INPUT } from '@/types/command.types';
import type { Command, ControlInput } from '@/types/command.types';
import type { CommandQueue } from './commandQueue';

/**
 * DroneController
 * ----------------
 * Consumes a batch of Commands (drained once per tick from the
 * CommandQueue) and collapses them into a single, normalized ControlInput
 * describing this tick's flight intent. This is the ONLY component that
 * understands what a "command" means in terms of stick deflection — the
 * PhysicsEngine below only knows about pitch/roll/yaw/throttle numbers.
 *
 * This separation is what allows Phase 2 gesture recognition to plug in:
 * a gesture classifier only needs to enqueue the same CommandType values
 * onto the same CommandQueue and this controller needs no changes.
 */
export class DroneController {
  private lastResolvedCommand = 'NONE';

  /** Reads every command queued this tick and resolves a ControlInput. */
  resolve(queue: CommandQueue): ControlInput {
    const commands = queue.drainAll();
    return this.resolveFromCommands(commands);
  }

  resolveFromCommands(commands: readonly Command[]): ControlInput {
    const input: ControlInput = { ...NEUTRAL_CONTROL_INPUT };

    if (commands.length === 0) {
      this.lastResolvedCommand = 'NONE';
      return input;
    }

    let mostRecentType: CommandType | null = null;
    let mostRecentTs = -Infinity;

    for (const cmd of commands) {
      const magnitude = cmd.intensity ?? 1;

      switch (cmd.type) {
        case CommandType.MOVE_FORWARD:
          input.pitch = Math.max(input.pitch, magnitude);
          break;
        case CommandType.MOVE_BACKWARD:
          input.pitch = Math.min(input.pitch, -magnitude);
          break;
        case CommandType.MOVE_LEFT:
          input.roll = Math.min(input.roll, -magnitude);
          break;
        case CommandType.MOVE_RIGHT:
          input.roll = Math.max(input.roll, magnitude);
          break;
        case CommandType.YAW_LEFT:
          input.yaw = Math.min(input.yaw, -magnitude);
          break;
        case CommandType.YAW_RIGHT:
          input.yaw = Math.max(input.yaw, magnitude);
          break;
        case CommandType.ASCEND:
          input.throttle = Math.max(input.throttle, magnitude);
          break;
        case CommandType.DESCEND:
          input.throttle = Math.min(input.throttle, -magnitude);
          break;
        case CommandType.HOVER:
          input.hover = true;
          break;
        case CommandType.TAKEOFF:
          input.takeoff = true;
          break;
        case CommandType.LAND:
          input.land = true;
          break;
        case CommandType.RESET:
          input.reset = true;
          break;
        case CommandType.EMERGENCY_STOP:
          input.emergencyStop = true;
          break;
      }

      if (cmd.timestamp >= mostRecentTs) {
        mostRecentTs = cmd.timestamp;
        mostRecentType = cmd.type;
      }
    }

    this.lastResolvedCommand = mostRecentType ?? 'NONE';
    return input;
  }

  get lastCommand(): string {
    return this.lastResolvedCommand;
  }
}
