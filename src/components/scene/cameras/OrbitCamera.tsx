import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import * as THREE from 'three';
import { useDroneStore } from '@/state/droneStore';
import { dampTo } from '@/utils/math';

export function OrbitCamera() {
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const target = useRef(new THREE.Vector3(0, 2, 0));

  useFrame((_, delta) => {
    const { telemetry } = useDroneStore.getState();
    target.current.x = dampTo(target.current.x, telemetry.position.x, 3, delta);
    target.current.y = dampTo(target.current.y, telemetry.position.y + 0.5, 3, delta);
    target.current.z = dampTo(target.current.z, telemetry.position.z, 3, delta);

    if (controlsRef.current) {
      controlsRef.current.target.copy(target.current);
      controlsRef.current.update();
    }
  });

  return (
    <>
      <PerspectiveCamera makeDefault fov={55} near={0.1} far={2000} position={[10, 6, 14]} />
      <OrbitControls
        ref={controlsRef}
        enableDamping
        dampingFactor={0.08}
        minDistance={3}
        maxDistance={80}
        maxPolarAngle={Math.PI / 2 - 0.02}
      />
    </>
  );
}
