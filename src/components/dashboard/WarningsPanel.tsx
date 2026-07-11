import { AnimatePresence, motion } from 'framer-motion';
import { useDroneStore } from '@/state/droneStore';

export function WarningsPanel() {
  const warnings = useDroneStore((s) => s.telemetry.warnings);

  if (warnings.length === 0) return null;

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 flex flex-col gap-2 items-center pointer-events-none z-20">
      <AnimatePresence>
        {warnings.map((w) => (
          <motion.div
            key={w}
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="glass-panel border-l-2 border-l-aeris-red/70 rounded-md px-4 py-1.5 shadow-glowRed"
          >
            <span className="hud-value text-xs text-aeris-red tracking-wide font-semibold">⚠ {w}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
