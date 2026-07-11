import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { useDroneStore } from '@/state/droneStore';
import { dampTo } from '@/utils/math';

const OFFSET = new THREE.Vector3(0, 3.2, 7.5);

export function FollowCamera() {
  const camRef = useRef<THREE.PerspectiveCamera>(null);
  const currentPos = useRef(new THREE.Vector3(0, 4, 10));
  const currentLookAt = useRef(new THREE.Vector3());

  useFrame((_, delta) => {
    const cam = camRef.current;
    if (!cam) return;
    const { telemetry } = useDroneStore.getState();

    const yaw = telemetry.rotation.y;
    const rotatedOffset = OFFSET.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
    const desiredPos = new THREE.Vector3(
      telemetry.position.x + rotatedOffset.x,
      telemetry.position.y + rotatedOffset.y,
      telemetry.position.z + rotatedOffset.z,
    );

    currentPos.current.x = dampTo(currentPos.current.x, desiredPos.x, 2.4, delta);
    currentPos.current.y = dampTo(currentPos.current.y, desiredPos.y, 2.4, delta);
    currentPos.current.z = dampTo(currentPos.current.z, desiredPos.z, 2.4, delta);

    const desiredLookAt = new THREE.Vector3(telemetry.position.x, telemetry.position.y + 0.4, telemetry.position.z);
    currentLookAt.current.x = dampTo(currentLookAt.current.x, desiredLookAt.x, 3, delta);
    currentLookAt.current.y = dampTo(currentLookAt.current.y, desiredLookAt.y, 3, delta);
    currentLookAt.current.z = dampTo(currentLookAt.current.z, desiredLookAt.z, 3, delta);

    cam.position.copy(currentPos.current);
    cam.lookAt(currentLookAt.current);
  });

  return (
    <PerspectiveCamera
      ref={camRef}
      makeDefault
      fov={55}
      near={0.1}
      far={2000}
      position={[0, 4, 10]}
    />
  );
}
