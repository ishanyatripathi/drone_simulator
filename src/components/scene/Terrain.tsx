import { useMemo } from 'react';
import * as THREE from 'three';

function buildGrassTexture(): THREE.CanvasTexture {
  const size = 512;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = '#2c4a2e';
  ctx.fillRect(0, 0, size, size);

  for (let i = 0; i < 9000; i++) {
    const x = Math.random() * size;
    const y = Math.random() * size;
    const shade = 0.7 + Math.random() * 0.5;
    const g = Math.floor(70 * shade + 40);
    ctx.fillStyle = `rgba(${Math.floor(30 * shade)}, ${g}, ${Math.floor(35 * shade)}, 0.55)`;
    ctx.fillRect(x, y, 1.4, 1.4);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(80, 80);
  texture.anisotropy = 8;
  return texture;
}

export function Terrain() {
  const grassTexture = useMemo(() => buildGrassTexture(), []);

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
      <planeGeometry args={[2000, 2000, 1, 1]} />
      <meshStandardMaterial map={grassTexture} roughness={0.95} metalness={0} />
    </mesh>
  );
}
