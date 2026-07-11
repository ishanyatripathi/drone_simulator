import { useState } from 'react';
import { motion } from 'framer-motion';
import { CommandType } from '@/types/command.types';
import { useDroneStore } from '@/state/droneStore';

export function EmergencyStopButton() {
  const dispatchCommand = useDroneStore((s) => s.dispatchCommand);
  const armed = useDroneStore((s) => s.telemetry.armed);
  const [pressed, setPressed] = useState(false);

  const handleClick = () => {
    dispatchCommand(CommandType.EMERGENCY_STOP, 'system');
    setPressed(true);
    setTimeout(() => setPressed(false), 600);
  };

  return (
    <motion.button
      whileTap={{ scale: 0.94 }}
      onClick={handleClick}
      disabled={!armed}
      className={`pointer-events-auto flex items-center gap-2 rounded-lg px-4 py-2.5 font-display font-semibold tracking-wide text-sm border transition-colors
        ${armed ? 'bg-aeris-red/15 border-aeris-red/60 text-aeris-red hover:bg-aeris-red/25 shadow-glowRed' : 'bg-white/5 border-white/10 text-aeris-textDim cursor-not-allowed'}
        ${pressed ? 'animate-pulse' : ''}`}
    >
      <span className="w-2 h-2 rounded-full bg-current" />
      EMERGENCY STOP
    </motion.button>
  );
}
