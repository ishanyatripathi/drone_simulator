import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  title?: string;
  accent?: 'cyan' | 'amber' | 'red' | 'none';
  delay?: number;
}

const ACCENT_BORDER: Record<NonNullable<GlassPanelProps['accent']>, string> = {
  cyan: 'border-l-2 border-l-aeris-cyan/60',
  amber: 'border-l-2 border-l-aeris-amber/60',
  red: 'border-l-2 border-l-aeris-red/60',
  none: '',
};

export function GlassPanel({ children, className = '', title, accent = 'none', delay = 0 }: GlassPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
      className={`glass-panel rounded-lg pointer-events-auto ${ACCENT_BORDER[accent]} ${className}`}
    >
      {title && (
        <div className="hud-label px-3 pt-2.5 pb-1 flex items-center gap-1.5">
          <span className="w-1 h-1 rounded-full bg-aeris-cyan/70" />
          {title}
        </div>
      )}
      <div className="px-3 pb-3 pt-1">{children}</div>
    </motion.div>
  );
}
