import { motion } from 'framer-motion';

export function BrandHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-panel rounded-lg px-4 py-2 flex items-center gap-3 pointer-events-auto"
    >
      <div className="w-7 h-7 rounded-md bg-aeris-cyan/10 border border-aeris-cyan/40 flex items-center justify-center">
        <div className="w-2.5 h-2.5 rounded-sm bg-aeris-cyan shadow-glow" />
      </div>
      <div className="leading-tight">
        <div className="font-display font-semibold tracking-[0.18em] text-sm text-aeris-text">AERIS</div>
        <div className="hud-label !text-[9px] !tracking-[0.14em]">Ground Control · Simulator</div>
      </div>
    </motion.div>
  );
}
