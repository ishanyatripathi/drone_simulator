import { useEffect, useMemo } from 'react';
import { KeyboardInputManager } from '@/core/keyboardInputManager';
import { useDroneStore } from '@/state/droneStore';

/**
 * Mounts the keyboard listener for the lifetime of the app shell (outside
 * the Canvas). Returns the manager instance so the R3F render loop can poll
 * held keys once per frame via `pollContinuous`.
 */
export function useKeyboardInput(): KeyboardInputManager {
  const dispatchCommand = useDroneStore((s) => s.dispatchCommand);

  const manager = useMemo(
    () => new KeyboardInputManager((type) => dispatchCommand(type, 'keyboard')),
    [dispatchCommand],
  );

  useEffect(() => {
    const detach = manager.attach();
    return detach;
  }, [manager]);

  return manager;
}
