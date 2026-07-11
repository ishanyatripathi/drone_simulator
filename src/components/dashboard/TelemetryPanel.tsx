import { useDroneStore } from '@/state/droneStore';

function Metric({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="hud-label">{label}</span>
      <span className="hud-value text-sm">
        {value}
        {unit && <span className="text-aeris-textDim text-[11px] ml-0.5">{unit}</span>}
      </span>
    </div>
  );
}

export function TelemetryPanel() {
  const telemetry = useDroneStore((s) => s.telemetry);

  return (
    <div className="grid grid-cols-2 gap-x-5 gap-y-2.5">
      <Metric label="Altitude" value={telemetry.altitude.toFixed(1)} unit="m" />
      <Metric label="Ground Speed" value={telemetry.speed.toFixed(1)} unit="m/s" />
      <Metric label="Vertical Speed" value={telemetry.verticalSpeed.toFixed(1)} unit="m/s" />
      <Metric label="Distance / Home" value={telemetry.distanceFromHome.toFixed(0)} unit="m" />
      <Metric label="Flight Time" value={formatTime(telemetry.flightTimeSeconds)} />
      <Metric label="GPS Sats" value={`${telemetry.gps.satellites}`} />
      <div className="col-span-2">
        <span className="hud-label">GPS Coordinates</span>
        <div className="hud-value text-xs mt-0.5">
          {telemetry.gps.lat.toFixed(5)}, {telemetry.gps.lon.toFixed(5)}
        </div>
      </div>
    </div>
  );
}

function formatTime(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
