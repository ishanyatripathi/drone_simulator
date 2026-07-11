import { create } from 'zustand';
import { CommandQueue } from '@/core/commandQueue';
import { DroneController } from '@/core/droneController';
import { PhysicsEngine } from '@/core/physicsEngine';
import type { CommandSource, CommandType } from '@/types/command.types';
import type { CameraMode, DroneTelemetry } from '@/types/drone.types';
import { createInitialTelemetry } from '@/types/drone.types';

const commandQueue = new CommandQueue();
const controller = new DroneController();
const engine = new PhysicsEngine();

interface DroneStore {
  telemetry: DroneTelemetry;
  cameraMode: CameraMode;
  fps: number;
  simulationTime: number;

  /** Called by input hooks (keyboard now, gesture in Phase 2). */
  dispatchCommand: (type: CommandType, source?: CommandSource) => void;
  /** Called once per animation frame from the R3F render loop. */
  tick: (dt: number) => void;
  setCameraMode: (mode: CameraMode) => void;
  setFps: (fps: number) => void;
}

export const useDroneStore = create<DroneStore>((set, get) => ({
  telemetry: createInitialTelemetry(),
  cameraMode: 'FOLLOW',
  fps: 0,
  simulationTime: 0,

  dispatchCommand: (type, source = 'keyboard') => {
    commandQueue.enqueue(type, source);
  },

  tick: (dt) => {
    const input = controller.resolve(commandQueue);
    const next = engine.step(input, get().telemetry, dt, controller.lastCommand);
    set((state) => ({ telemetry: next, simulationTime: state.simulationTime + dt }));
  },

  setCameraMode: (mode) => set({ cameraMode: mode }),
  setFps: (fps) => set({ fps }),
}));

/** Exposed for advanced/debug use only — normal code should go through the store. */
export const __simulationInternals = { commandQueue, controller, engine };
