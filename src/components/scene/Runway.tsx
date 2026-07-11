import { useMemo } from 'react';
import * as THREE from 'three';

function buildRunwayTexture(): THREE.CanvasTexture {
  const width = 256;
  const height = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = '#2b2d31';
  ctx.fillRect(0, 0, width, height);

  // subtle asphalt noise
  for (let i = 0; i < 4000; i++) {
    const x = Math.random() * width;
    const y = Math.random() * height;
    const shade = 30 + Math.random() * 25;
    ctx.fillStyle = `rgba(${shade},${shade},${shade + 3},0.5)`;
    ctx.fillRect(x, y, 1.2, 1.2);
  }

  // edge lines
  ctx.fillStyle = '#f2f2f2';
  ctx.fillRect(width * 0.08, 0, width * 0.02, height);
  ctx.fillRect(width * 0.9, 0, width * 0.02, height);

  // dashed centerline
  const dashHeight = 40;
  const gap = 30;
  for (let y = 0; y < height; y += dashHeight + gap) {
    ctx.fillRect(width / 2 - width * 0.015, y, width * 0.03, dashHeight);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1, 6);
  texture.anisotropy = 8;
  return texture;
}

export function Runway() {
  const texture = useMemo(() => buildRunwayTexture(), []);

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, -20]} receiveShadow>
      <planeGeometry args={[14, 120]} />
      <meshStandardMaterial map={texture} roughness={0.85} metalness={0.05} />
    </mesh>
  );
}
