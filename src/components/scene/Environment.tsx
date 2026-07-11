import { Sky, Environment as DreiEnvironment } from '@react-three/drei';
import { Terrain } from './Terrain';
import { Runway } from './Runway';
import { Trees } from './Trees';
import { Mountains } from './Mountains';
import { Clouds } from './Clouds';

const SUN_POSITION: [number, number, number] = [180, 140, -90];

export function Environment() {
  return (
    <>
      <fog attach="fog" args={['#a9c4d6', 90, 620]} />

      <Sky
        distance={4500}
        sunPosition={SUN_POSITION}
        turbidity={4}
        rayleigh={1.4}
        mieCoefficient={0.006}
        mieDirectionalG={0.8}
      />

      {/* HDR-style image-based lighting for realistic metallic reflections */}
      <DreiEnvironment preset="sunset" environmentIntensity={0.6} />

      <ambientLight intensity={0.35} />
      <hemisphereLight args={['#bcd8ea', '#3a4a3c', 0.5]} />
      <directionalLight
        position={SUN_POSITION}
        intensity={2.2}
        color="#fff4dd"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-120}
        shadow-camera-right={120}
        shadow-camera-top={120}
        shadow-camera-bottom={-120}
        shadow-camera-near={10}
        shadow-camera-far={600}
        shadow-bias={-0.0003}
      />

      <Terrain />
      <Runway />
      <Trees />
      <Mountains />
      <Clouds />
    </>
  );
}
