import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { KEY_BINDINGS_HELP } from '@/core/keyboardInputManager';

export function ControlsHelp() {
  const [open, setOpen] = useState(false);

  return (
    <div className="pointer-events-auto flex flex-col items-end gap-2">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="glass-panel rounded-lg p-3 w-56"
          >
            <div className="hud-label mb-2">Keyboard Controls</div>
            <div className="flex flex-col gap-1.5">
              {KEY_BINDINGS_HELP.map((b) => (
                <div key={b.key} className="flex items-center justify-between text-xs">
                  <span className="hud-value px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-aeris-cyan">
                    {b.key}
                  </span>
                  <span className="text-aeris-textDim">{b.label}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <button
        onClick={() => setOpen((o) => !o)}
        className="glass-panel rounded-full w-8 h-8 flex items-center justify-center text-aeris-cyan hud-value text-sm"
      >
        ?
      </button>
    </div>
  );
}
