import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Loader } from '@react-three/drei';
import { ACESFilmicToneMapping, PCFSoftShadowMap } from 'three';
import { Scene } from '@/components/scene/Scene';
import { Dashboard } from '@/components/dashboard/Dashboard';
import { useKeyboardInput } from '@/hooks/useKeyboardInput';

export default function App() {
  const keyboard = useKeyboardInput();

  return (
    <div className="relative w-screen h-screen bg-aeris-bg overflow-hidden">
      <Canvas
        shadows={{ type: PCFSoftShadowMap }}
        dpr={[1, 1.75]}
        gl={{
          antialias: true,
          toneMapping: ACESFilmicToneMapping,
          toneMappingExposure: 1.05,
        }}
        camera={{ position: [0, 4, 10], fov: 55, near: 0.1, far: 2000 }}
      >
        <Suspense fallback={null}>
          <Scene keyboard={keyboard} />
        </Suspense>
      </Canvas>

      <Loader
        containerStyles={{ background: '#05070c' }}
        innerStyles={{ background: '#0b1018', width: '240px' }}
        barStyles={{ background: '#00d9ff' }}
        dataStyles={{ color: '#6b8299', fontFamily: 'JetBrains Mono, monospace', fontSize: '11px' }}
      />
      <Dashboard />
    </div>
  );
}
