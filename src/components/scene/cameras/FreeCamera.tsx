import { OrbitControls, PerspectiveCamera } from '@react-three/drei';

export function FreeCamera() {
  return (
    <>
      <PerspectiveCamera makeDefault fov={60} near={0.1} far={3000} position={[40, 25, 55]} />
      <OrbitControls
        enableDamping
        dampingFactor={0.06}
        minDistance={2}
        maxDistance={500}
        target={[0, 5, 0]}
        maxPolarAngle={Math.PI / 2 - 0.01}
      />
    </>
  );
}
