import { useDroneStore } from '@/state/droneStore';
import type { FlightMode } from '@/types/drone.types';

const MODE_STYLES: Record<FlightMode, string> = {
  DISARMED: 'text-aeris-textDim border-aeris-textDim/30',
  IDLE: 'text-aeris-textDim border-aeris-textDim/30',
  LANDED: 'text-aeris-textDim border-aeris-textDim/30',
  TAKING_OFF: 'text-aeris-amber border-aeris-amber/40',
  LANDING: 'text-aeris-amber border-aeris-amber/40',
  HOVER: 'text-aeris-cyan border-aeris-cyan/40',
  FLYING: 'text-aeris-green border-aeris-green/40',
  EMERGENCY: 'text-aeris-red border-aeris-red/50',
};

const COMMAND_LABELS: Record<string, string> = {
  NONE: 'IDLE',
  MOVE_FORWARD: 'PITCH FORWARD',
  MOVE_BACKWARD: 'PITCH BACKWARD',
  MOVE_LEFT: 'ROLL LEFT',
  MOVE_RIGHT: 'ROLL RIGHT',
  YAW_LEFT: 'YAW LEFT',
  YAW_RIGHT: 'YAW RIGHT',
  ASCEND: 'ASCEND',
  DESCEND: 'DESCEND',
  HOVER: 'HOVER',
  TAKEOFF: 'TAKEOFF',
  LAND: 'LAND',
  RESET: 'RESET',
  EMERGENCY_STOP: 'EMERGENCY STOP',
};

export function FlightStatusPanel() {
  const flightMode = useDroneStore((s) => s.telemetry.flightMode);
  const lastCommand = useDroneStore((s) => s.telemetry.lastCommand);

  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex flex-col gap-1">
        <span className="hud-label">Flight Mode</span>
        <span className={`inline-block w-fit px-2 py-0.5 rounded border text-xs font-semibold tracking-wide ${MODE_STYLES[flightMode]}`}>
          {flightMode.replace('_', ' ')}
        </span>
      </div>
      <div className="flex flex-col gap-1 items-end">
        <span className="hud-label">Command</span>
        <span className="hud-value text-xs text-aeris-cyan">
          {COMMAND_LABELS[lastCommand] ?? lastCommand}
        </span>
      </div>
    </div>
  );
}
