import { useDroneStore } from '@/state/droneStore';

const MOTOR_LABELS = ['FR', 'FL', 'RR', 'RL'];
const MAX_RPM = 6400;

export function MotorRPMPanel() {
  const motorRPM = useDroneStore((s) => s.telemetry.motorRPM);

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-2">
      {motorRPM.map((rpm, i) => (
        <div key={i} className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="hud-label">M{i + 1} {MOTOR_LABELS[i]}</span>
            <span className="hud-value text-[11px]">{Math.round(rpm)}</span>
          </div>
          <div className="h-1 w-full rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full bg-aeris-cyan/80 transition-all duration-150"
              style={{ width: `${Math.min(100, (rpm / MAX_RPM) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
