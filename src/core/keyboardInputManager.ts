import { CommandType } from '@/types/command.types';

/**
 * Keys that should keep emitting their command every frame while held down
 * (continuous stick-style input): movement, yaw, throttle.
 */
const CONTINUOUS_KEY_MAP: Record<string, CommandType> = {
  KeyW: CommandType.MOVE_FORWARD,
  KeyS: CommandType.MOVE_BACKWARD,
  KeyA: CommandType.MOVE_LEFT,
  KeyD: CommandType.MOVE_RIGHT,
  KeyQ: CommandType.YAW_LEFT,
  KeyE: CommandType.YAW_RIGHT,
  Space: CommandType.ASCEND,
  ShiftLeft: CommandType.DESCEND,
  ShiftRight: CommandType.DESCEND,
};

/**
 * Keys that represent a discrete, one-shot event (fire once per press, not
 * once per frame): takeoff, land, hover, reset.
 */
const ONE_SHOT_KEY_MAP: Record<string, CommandType> = {
  KeyT: CommandType.TAKEOFF,
  KeyL: CommandType.LAND,
  KeyH: CommandType.HOVER,
  KeyR: CommandType.RESET,
};

/**
 * KeyboardInputManager
 * ---------------------
 * This is a Phase-1-only input adapter. It knows nothing about physics or
 * rendering — its sole job is turning raw browser KeyboardEvents into
 * CommandType values pushed onto the CommandQueue. In Phase 2 a gesture
 * recognizer will be a parallel adapter with the exact same
 * responsibility, so nothing downstream needs to change.
 */
export class KeyboardInputManager {
  private pressed = new Set<string>();
  private onOneShot: (type: CommandType) => void;
  private keydownHandler: (e: KeyboardEvent) => void;
  private keyupHandler: (e: KeyboardEvent) => void;

  constructor(onOneShot: (type: CommandType) => void) {
    this.onOneShot = onOneShot;

    this.keydownHandler = (e: KeyboardEvent) => {
      if (e.repeat) return;
      this.pressed.add(e.code);
      const oneShot = ONE_SHOT_KEY_MAP[e.code];
      if (oneShot) this.onOneShot(oneShot);
    };

    this.keyupHandler = (e: KeyboardEvent) => {
      this.pressed.delete(e.code);
    };
  }

  attach(): () => void {
    window.addEventListener('keydown', this.keydownHandler);
    window.addEventListener('keyup', this.keyupHandler);
    return () => this.detach();
  }

  detach(): void {
    window.removeEventListener('keydown', this.keydownHandler);
    window.removeEventListener('keyup', this.keyupHandler);
    this.pressed.clear();
  }

  /** Called once per animation frame — emits a command for every held key. */
  pollContinuous(dispatch: (type: CommandType) => void): void {
    for (const code of this.pressed) {
      const type = CONTINUOUS_KEY_MAP[code];
      if (type) dispatch(type);
    }
  }

  isHeld(code: string): boolean {
    return this.pressed.has(code);
  }

  get activeKeys(): readonly string[] {
    return Array.from(this.pressed);
  }
}

export const KEY_BINDINGS_HELP: { key: string; label: string }[] = [
  { key: 'W / S', label: 'Pitch forward / backward' },
  { key: 'A / D', label: 'Roll left / right' },
  { key: 'Q / E', label: 'Yaw left / right' },
  { key: 'SPACE', label: 'Ascend' },
  { key: 'SHIFT', label: 'Descend' },
  { key: 'H', label: 'Hover / hold position' },
  { key: 'T', label: 'Takeoff' },
  { key: 'L', label: 'Land' },
  { key: 'R', label: 'Reset simulation' },
];
