import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { useDroneStore } from '@/state/droneStore';

const NOSE_OFFSET = new THREE.Vector3(0, 0.05, 0.22);

export function FPVCamera() {
  const camRef = useRef<THREE.PerspectiveCamera>(null);

  useFrame(() => {
    const cam = camRef.current;
    if (!cam) return;
    const { telemetry } = useDroneStore.getState();

    const euler = new THREE.Euler(telemetry.rotation.x, telemetry.rotation.y, telemetry.rotation.z, 'YXZ');
    const offset = NOSE_OFFSET.clone().applyEuler(euler);

    cam.position.set(
      telemetry.position.x + offset.x,
      telemetry.position.y + offset.y,
      telemetry.position.z + offset.z,
    );

    cam.rotation.copy(euler);
    // Slight nose-down bias like a real FPV camera tilt.
    cam.rotateX(-0.12);
  });

  return <PerspectiveCamera ref={camRef} makeDefault fov={100} near={0.05} far={2000} />;
}
