import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Group, Mesh, MeshStandardMaterial, PointLight } from 'three';
import { Propeller } from './Propeller';
import { useDroneStore } from '@/state/droneStore';

const ARM_OFFSET = 0.34;

interface MotorArmProps {
  position: [number, number, number];
  rpmRef: React.MutableRefObject<number>;
  spinDirection: 1 | -1;
}

function MotorArm({ position, rpmRef, spinDirection }: MotorArmProps) {
  return (
    <group position={position}>
      {/* Carbon fiber arm */}
      <mesh castShadow receiveShadow rotation={[0, Math.atan2(position[0], position[2]), 0]} position={[-position[0] / 2, -position[1] / 2, -position[2] / 2]}>
        <boxGeometry args={[0.05, 0.028, Math.hypot(position[0], position[2])]} />
        <meshStandardMaterial color="#14161b" roughness={0.35} metalness={0.55} />
      </mesh>
      {/* Motor bell */}
      <mesh castShadow position={[0, 0.02, 0]}>
        <cylinderGeometry args={[0.075, 0.08, 0.075, 20]} />
        <meshStandardMaterial color="#c9cdd3" metalness={0.9} roughness={0.22} />
      </mesh>
      <mesh position={[0, 0.06, 0]}>
        <cylinderGeometry args={[0.018, 0.018, 0.05, 10]} />
        <meshStandardMaterial color="#22252b" metalness={0.8} roughness={0.3} />
      </mesh>
      <group position={[0, 0.085, 0]}>
        <Propeller rpmRef={rpmRef} spinDirection={spinDirection} />
      </group>
    </group>
  );
}

/** Front/rear/side status LEDs that pulse based on flight mode. */
function StatusLED({
  position,
  color,
}: {
  position: [number, number, number];
  color: string;
}) {
  const lightRef = useRef<PointLight>(null);
  const meshRef = useRef<Mesh>(null);

  useFrame((state) => {
    const { telemetry } = useDroneStore.getState();
    const material = meshRef.current?.material as MeshStandardMaterial | undefined;
    if (!material) return;
    if (telemetry.flightMode === 'EMERGENCY') {
      material.emissiveIntensity = 1.5 + Math.max(0, Math.sin(state.clock.elapsedTime * 18)) * 3;
    } else {
      material.emissiveIntensity = 2.5;
    }
  });

  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <sphereGeometry args={[0.018, 8, 8]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2.5} toneMapped={false} />
      </mesh>
      <pointLight ref={lightRef} color={color} intensity={0.6} distance={1.2} />
    </group>
  );
}

export function Drone() {
  const groupRef = useRef<Group>(null);
  const gimbalRef = useRef<Group>(null);
  const rpm0 = useRef(0);
  const rpm1 = useRef(0);
  const rpm2 = useRef(0);
  const rpm3 = useRef(0);

  const armPositions = useMemo<[number, number, number][]>(
    () => [
      [ARM_OFFSET, 0.02, ARM_OFFSET],
      [-ARM_OFFSET, 0.02, ARM_OFFSET],
      [ARM_OFFSET, 0.02, -ARM_OFFSET],
      [-ARM_OFFSET, 0.02, -ARM_OFFSET],
    ],
    [],
  );

  useFrame(() => {
    const { telemetry } = useDroneStore.getState();
    const g = groupRef.current;
    if (g) {
      g.position.set(telemetry.position.x, telemetry.position.y + 0.12, telemetry.position.z);
      g.rotation.set(telemetry.rotation.x, telemetry.rotation.y, telemetry.rotation.z);
    }

    rpm0.current = telemetry.motorRPM[0];
    rpm1.current = telemetry.motorRPM[1];
    rpm2.current = telemetry.motorRPM[2];
    rpm3.current = telemetry.motorRPM[3];

    if (gimbalRef.current) {
      // Gimbal counter-rotates to stay level relative to world, like a real
      // stabilized camera mount.
      gimbalRef.current.rotation.x = -telemetry.rotation.x * 0.85;
      gimbalRef.current.rotation.z = -telemetry.rotation.z * 0.85;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Central carbon-fiber body */}
      <mesh castShadow receiveShadow>
        <boxGeometry args={[0.36, 0.09, 0.36]} />
        <meshStandardMaterial color="#0d0e11" roughness={0.28} metalness={0.65} />
      </mesh>
      <mesh castShadow position={[0, 0.055, 0]}>
        <boxGeometry args={[0.24, 0.03, 0.24]} />
        <meshStandardMaterial color="#181b21" roughness={0.2} metalness={0.8} />
      </mesh>
      {/* Top plate accent ring */}
      <mesh position={[0, 0.072, 0]}>
        <torusGeometry args={[0.1, 0.006, 8, 24]} />
        <meshStandardMaterial color="#00d9ff" emissive="#00d9ff" emissiveIntensity={0.8} roughness={0.4} />
      </mesh>

      {/* Four motor arms + rotating propellers */}
      <MotorArm position={armPositions[0]} rpmRef={rpm0} spinDirection={1} />
      <MotorArm position={armPositions[1]} rpmRef={rpm1} spinDirection={-1} />
      <MotorArm position={armPositions[2]} rpmRef={rpm2} spinDirection={-1} />
      <MotorArm position={armPositions[3]} rpmRef={rpm3} spinDirection={1} />

      {/* Camera gimbal, front-mounted, counter-stabilized */}
      <group ref={gimbalRef} position={[0, -0.06, 0.2]}>
        <mesh castShadow>
          <boxGeometry args={[0.06, 0.06, 0.06]} />
          <meshStandardMaterial color="#22252b" metalness={0.7} roughness={0.3} />
        </mesh>
        <mesh castShadow position={[0, -0.01, 0.045]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.028, 0.028, 0.05, 16]} />
          <meshStandardMaterial color="#0a0a0c" metalness={0.9} roughness={0.1} />
        </mesh>
        <mesh position={[0, -0.01, 0.075]}>
          <circleGeometry args={[0.02, 16]} />
          <meshStandardMaterial color="#00d9ff" emissive="#00d9ff" emissiveIntensity={1.2} roughness={0.1} />
        </mesh>
      </group>

      {/* Landing gear */}
      {[
        [0.13, -0.09, 0.13],
        [-0.13, -0.09, 0.13],
        [0.13, -0.09, -0.13],
        [-0.13, -0.09, -0.13],
      ].map((pos, i) => (
        <group key={i} position={pos as [number, number, number]}>
          <mesh castShadow>
            <cylinderGeometry args={[0.007, 0.007, 0.14, 8]} />
            <meshStandardMaterial color="#26292f" metalness={0.6} roughness={0.4} />
          </mesh>
          <mesh position={[0, -0.075, 0]} castShadow>
            <boxGeometry args={[0.09, 0.012, 0.02]} />
            <meshStandardMaterial color="#1a1c21" metalness={0.5} roughness={0.5} />
          </mesh>
        </group>
      ))}

      {/* Front LEDs (white, forward-facing) */}
      <StatusLED position={[0.06, 0, 0.19]} color="#ffffff" />
      <StatusLED position={[-0.06, 0, 0.19]} color="#ffffff" />
      {/* Rear LEDs (red, aviation convention) */}
      <StatusLED position={[0.06, 0, -0.19]} color="#ff2e2e" />
      <StatusLED position={[-0.06, 0, -0.19]} color="#ff2e2e" />
    </group>
  );
}
