import type { KeyboardInputManager } from '@/core/keyboardInputManager';
import { useSimulationLoop } from '@/hooks/useSimulationLoop';
import { useFPS } from '@/hooks/useFPS';
import { Drone } from './Drone';
import { Environment } from './Environment';
import { CameraManager } from './cameras/CameraManager';

interface SceneProps {
  keyboard: KeyboardInputManager;
}

/** Everything that lives inside <Canvas>. Must stay a child of the R3F tree
 * so hooks like useFrame / useThree are valid. */
export function Scene({ keyboard }: SceneProps) {
  useSimulationLoop(keyboard);
  useFPS();

  return (
    <>
      <CameraManager />
      <Environment />
      <Drone />
    </>
  );
}
