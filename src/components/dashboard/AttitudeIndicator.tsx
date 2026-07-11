import { useDroneStore } from '@/state/droneStore';
import { RAD2DEG } from '@/utils/math';

const SIZE = 132;
const CENTER = SIZE / 2;

export function AttitudeIndicator() {
  const rotation = useDroneStore((s) => s.telemetry.rotation);
  const heading = useDroneStore((s) => s.telemetry.heading);

  const pitchDeg = rotation.x * RAD2DEG;
  const rollDeg = rotation.z * RAD2DEG;
  const pitchOffsetPx = Math.max(-30, Math.min(30, pitchDeg * 1.1));

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className="relative rounded-full overflow-hidden border border-aeris-cyan/25 shadow-glow"
        style={{ width: SIZE, height: SIZE }}
      >
        {/* Rotating horizon (roll) */}
        <div
          className="absolute inset-[-40%]"
          style={{ transform: `rotate(${-rollDeg}deg)` }}
        >
          <div
            className="absolute left-0 right-0"
            style={{
              top: `calc(50% + ${pitchOffsetPx}px)`,
              height: '200%',
              background: 'linear-gradient(180deg, #0a2a3d 0%, #062033 100%)',
            }}
          />
          <div
            className="absolute left-0 right-0"
            style={{
              bottom: `calc(50% - ${pitchOffsetPx}px)`,
              height: '200%',
              background: 'linear-gradient(180deg, #3a2b12 0%, #1c1608 100%)',
            }}
          />
          <div
            className="absolute left-0 right-0 h-[1.5px] bg-aeris-cyan/80"
            style={{ top: `calc(50% + ${pitchOffsetPx}px)` }}
          />
        </div>

        {/* Fixed aircraft reference symbol */}
        <svg
          className="absolute inset-0"
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
        >
          <line x1={CENTER - 22} y1={CENTER} x2={CENTER - 8} y2={CENTER} stroke="#ffb020" strokeWidth={2.5} />
          <line x1={CENTER + 8} y1={CENTER} x2={CENTER + 22} y2={CENTER} stroke="#ffb020" strokeWidth={2.5} />
          <circle cx={CENTER} cy={CENTER} r={2.5} fill="#ffb020" />
        </svg>

        {/* Bezel ring */}
        <div className="absolute inset-0 rounded-full ring-1 ring-inset ring-white/10 pointer-events-none" />
      </div>

      <div className="flex gap-3 hud-value text-[11px]">
        <span>
          <span className="text-aeris-textDim">PITCH </span>
          {pitchDeg.toFixed(1)}°
        </span>
        <span>
          <span className="text-aeris-textDim">ROLL </span>
          {rollDeg.toFixed(1)}°
        </span>
        <span>
          <span className="text-aeris-textDim">HDG </span>
          {heading.toFixed(0)}°
        </span>
      </div>
    </div>
  );
}
