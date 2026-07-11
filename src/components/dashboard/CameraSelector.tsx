import { useDroneStore } from '@/state/droneStore';
import type { CameraMode } from '@/types/drone.types';

const OPTIONS: { mode: CameraMode; label: string }[] = [
  { mode: 'FOLLOW', label: 'Follow' },
  { mode: 'FPV', label: 'FPV' },
  { mode: 'TOP', label: 'Top' },
  { mode: 'ORBIT', label: 'Orbit' },
  { mode: 'FREE', label: 'Free' },
];

export function CameraSelector() {
  const cameraMode = useDroneStore((s) => s.cameraMode);
  const setCameraMode = useDroneStore((s) => s.setCameraMode);

  return (
    <div className="flex gap-1 pointer-events-auto">
      {OPTIONS.map((opt) => (
        <button
          key={opt.mode}
          onClick={() => setCameraMode(opt.mode)}
          className={`px-2.5 py-1.5 rounded-md text-[11px] font-medium tracking-wide transition-colors border
            ${
              cameraMode === opt.mode
                ? 'bg-aeris-cyan/15 border-aeris-cyan/50 text-aeris-cyan'
                : 'bg-white/[0.03] border-white/10 text-aeris-textDim hover:text-aeris-text hover:border-white/20'
            }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
