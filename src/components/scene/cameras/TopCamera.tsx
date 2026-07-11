import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { useDroneStore } from '@/state/droneStore';
import { dampTo } from '@/utils/math';

export function TopCamera() {
  const camRef = useRef<THREE.PerspectiveCamera>(null);
  const current = useRef(new THREE.Vector3(0, 60, 0));

  useFrame((_, delta) => {
    const cam = camRef.current;
    if (!cam) return;
    const { telemetry } = useDroneStore.getState();

    current.current.x = dampTo(current.current.x, telemetry.position.x, 2, delta);
    current.current.z = dampTo(current.current.z, telemetry.position.z, 2, delta);
    current.current.y = 60;

    cam.position.copy(current.current);
    cam.lookAt(current.current.x, 0, current.current.z);
    cam.rotation.z = telemetry.rotation.y;
  });

  return <PerspectiveCamera ref={camRef} makeDefault fov={50} near={0.1} far={2000} position={[0, 60, 0]} />;
}
