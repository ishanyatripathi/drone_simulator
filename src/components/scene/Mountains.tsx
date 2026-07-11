import { useMemo } from 'react';

interface PeakSpec {
  position: [number, number, number];
  radius: number;
  height: number;
  color: string;
}

function generatePeaks(): PeakSpec[] {
  const peaks: PeakSpec[] = [];
  const ringRadius = 520;
  const count = 18;

  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2 + Math.random() * 0.2;
    const dist = ringRadius + Math.random() * 140;
    const height = 90 + Math.random() * 160;
    const shade = 0.35 + Math.random() * 0.25;
    peaks.push({
      position: [Math.cos(angle) * dist, height / 2 - 4, Math.sin(angle) * dist],
      radius: 90 + Math.random() * 90,
      height,
      color: `rgb(${Math.floor(70 * shade)}, ${Math.floor(90 * shade)}, ${Math.floor(110 * shade)})`,
    });
  }
  return peaks;
}

export function Mountains() {
  const peaks = useMemo(() => generatePeaks(), []);

  return (
    <group>
      {peaks.map((p, i) => (
        <mesh key={i} position={p.position}>
          <coneGeometry args={[p.radius, p.height, 5]} />
          <meshStandardMaterial color={p.color} roughness={1} fog />
        </mesh>
      ))}
    </group>
  );
}
