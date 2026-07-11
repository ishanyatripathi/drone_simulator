import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useDroneStore } from '@/state/droneStore';

/** Updates the store's fps value roughly 4x per second to avoid re-render spam. */
export function useFPS(): void {
  const setFps = useDroneStore((s) => s.setFps);
  const frames = useRef(0);
  const elapsed = useRef(0);

  useFrame((_, delta) => {
    frames.current += 1;
    elapsed.current += delta;
    if (elapsed.current >= 0.25) {
      setFps(Math.round(frames.current / elapsed.current));
      frames.current = 0;
      elapsed.current = 0;
    }
  });
}
