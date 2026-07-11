import { useFrame } from '@react-three/fiber';
import type { KeyboardInputManager } from '@/core/keyboardInputManager';
import { useDroneStore } from '@/state/droneStore';

const MAX_DT = 1 / 20; // clamp huge frame gaps (tab switch, etc.)

/**
 * Must be called from a component rendered inside <Canvas>. Each frame it:
 *   1. Polls held keys → enqueues continuous commands.
 *   2. Advances the physics simulation by dt.
 *
 * This is the "engine heartbeat" — everything else (dashboard, drone mesh,
 * cameras) simply reads the resulting telemetry from the store.
 */
export function useSimulationLoop(keyboard: KeyboardInputManager): void {
  const dispatchCommand = useDroneStore((s) => s.dispatchCommand);
  const tick = useDroneStore((s) => s.tick);

  useFrame((_, delta) => {
    keyboard.pollContinuous((type) => dispatchCommand(type, 'keyboard'));
    tick(Math.min(delta, MAX_DT));
  });
}
