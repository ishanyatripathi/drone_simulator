import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Group } from 'three';

interface PropellerProps {
  rpmRef: React.MutableRefObject<number>;
  spinDirection?: 1 | -1;
}

/** A twin-blade propeller that spins continuously at a rate derived from motor RPM. */
export function Propeller({ rpmRef, spinDirection = 1 }: PropellerProps) {
  const groupRef = useRef<Group>(null);

  useFrame((_, delta) => {
    if (!groupRef.current) return;
    const rpm = rpmRef.current;
    const radiansPerSecond = (rpm / 60) * Math.PI * 2;
    groupRef.current.rotation.y += radiansPerSecond * delta * spinDirection;
  });

  return (
    <group ref={groupRef}>
      <mesh castShadow>
        <boxGeometry args={[0.62, 0.008, 0.045]} />
        <meshStandardMaterial color="#12151a" roughness={0.35} metalness={0.2} />
      </mesh>
      <mesh castShadow rotation={[0, Math.PI / 2, 0]}>
        <boxGeometry args={[0.62, 0.008, 0.045]} />
        <meshStandardMaterial color="#12151a" roughness={0.35} metalness={0.2} />
      </mesh>
      <mesh position={[0, 0.01, 0]}>
        <cylinderGeometry args={[0.03, 0.03, 0.02, 12]} />
        <meshStandardMaterial color="#1a1d24" metalness={0.8} roughness={0.25} />
      </mesh>
    </group>
  );
}
