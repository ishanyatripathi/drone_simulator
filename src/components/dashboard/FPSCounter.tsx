import { useDroneStore } from '@/state/droneStore';

export function FPSCounter() {
  const fps = useDroneStore((s) => s.fps);
  const colorClass = fps >= 50 ? 'text-aeris-green' : fps >= 30 ? 'text-aeris-amber' : 'text-aeris-red';

  return (
    <div className="hud-value text-xs flex items-center gap-1.5">
      <span className="hud-label">FPS</span>
      <span className={colorClass}>{fps}</span>
    </div>
  );
}
