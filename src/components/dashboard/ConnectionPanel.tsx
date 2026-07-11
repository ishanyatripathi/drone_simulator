import { useDroneStore } from '@/state/droneStore';

export function ConnectionPanel() {
  const quality = useDroneStore((s) => s.telemetry.connectionQuality);
  const armed = useDroneStore((s) => s.telemetry.armed);

  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${armed ? 'bg-aeris-green animate-pulse-slow' : 'bg-aeris-textDim'}`} />
      <div className="flex flex-col leading-tight">
        <span className="hud-label">Link</span>
        <span className="hud-value text-xs">{quality}% · {armed ? 'ARMED' : 'DISARMED'}</span>
      </div>
    </div>
  );
}
