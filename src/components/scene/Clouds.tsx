import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Cloud } from '@react-three/drei';
import type { Group } from 'three';

interface CloudLayerSpec {
  position: [number, number, number];
  scale: number;
  speed: number;
  opacity: number;
}

const CLOUD_LAYERS: CloudLayerSpec[] = [
  { position: [-60, 55, -120], scale: 12, speed: 0.04, opacity: 0.55 },
  { position: [80, 62, -80], scale: 16, speed: 0.03, opacity: 0.45 },
  { position: [-20, 70, 90], scale: 10, speed: 0.05, opacity: 0.4 },
  { position: [140, 58, 40], scale: 14, speed: 0.035, opacity: 0.5 },
  { position: [-160, 65, -40], scale: 18, speed: 0.025, opacity: 0.4 },
];

function DriftingCloud({ spec }: { spec: CloudLayerSpec }) {
  const ref = useRef<Group>(null);

  useFrame((_, delta) => {
    if (!ref.current) return;
    ref.current.position.x += spec.speed * delta * 10;
    if (ref.current.position.x > 400) ref.current.position.x = -400;
  });

  return (
    <group ref={ref} position={spec.position}>
      <Cloud scale={spec.scale} opacity={spec.opacity} speed={0.15} segments={30} color="#ffffff" fade={80} />
    </group>
  );
}

export function Clouds() {
  return (
    <group>
      {CLOUD_LAYERS.map((spec, i) => (
        <DriftingCloud key={i} spec={spec} />
      ))}
    </group>
  );
}
