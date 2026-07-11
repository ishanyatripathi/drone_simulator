import { useMemo, useRef, useLayoutEffect } from 'react';
import * as THREE from 'three';

interface TreePlacement {
  position: [number, number, number];
  scale: number;
  rotationY: number;
}

function generatePlacements(count: number): TreePlacement[] {
  const placements: TreePlacement[] = [];
  let attempts = 0;

  while (placements.length < count && attempts < count * 6) {
    attempts++;
    const x = (Math.random() - 0.5) * 380;
    const z = (Math.random() - 0.5) * 380;

    // Keep clear of the runway corridor and the drone's home pad.
    const nearRunway = Math.abs(x) < 12 && z < 45 && z > -95;
    const nearHome = Math.hypot(x, z) < 10;
    if (nearRunway || nearHome) continue;

    placements.push({
      position: [x, 0, z],
      scale: 0.8 + Math.random() * 1.1,
      rotationY: Math.random() * Math.PI * 2,
    });
  }

  return placements;
}

export function Trees({ count = 260 }: { count?: number }) {
  const placements = useMemo(() => generatePlacements(count), [count]);
  const trunkRef = useRef<THREE.InstancedMesh>(null);
  const canopyRef = useRef<THREE.InstancedMesh>(null);

  useLayoutEffect(() => {
    const dummy = new THREE.Object3D();

    placements.forEach((p, i) => {
      dummy.position.set(p.position[0], 0.6 * p.scale, p.position[2]);
      dummy.rotation.set(0, p.rotationY, 0);
      dummy.scale.setScalar(p.scale);
      dummy.updateMatrix();
      trunkRef.current?.setMatrixAt(i, dummy.matrix);

      dummy.position.set(p.position[0], 1.7 * p.scale, p.position[2]);
      dummy.updateMatrix();
      canopyRef.current?.setMatrixAt(i, dummy.matrix);
    });

    if (trunkRef.current) trunkRef.current.instanceMatrix.needsUpdate = true;
    if (canopyRef.current) canopyRef.current.instanceMatrix.needsUpdate = true;
  }, [placements]);

  return (
    <group>
      <instancedMesh ref={trunkRef} args={[undefined, undefined, placements.length]} castShadow receiveShadow>
        <cylinderGeometry args={[0.09, 0.13, 1.2, 6]} />
        <meshStandardMaterial color="#4a3626" roughness={1} />
      </instancedMesh>
      <instancedMesh ref={canopyRef} args={[undefined, undefined, placements.length]} castShadow receiveShadow>
        <coneGeometry args={[0.95, 2.1, 7]} />
        <meshStandardMaterial color="#1f4a2c" roughness={0.9} />
      </instancedMesh>
    </group>
  );
}
