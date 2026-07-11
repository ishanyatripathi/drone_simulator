import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useGestureInput } from '@/hooks/useGestureInput';

const STATE_COLOR: Record<string, string> = {
  idle: 'bg-aeris-textDim',
  connecting: 'bg-aeris-amber animate-pulse-slow',
  connected: 'bg-aeris-green animate-pulse-slow',
  error: 'bg-aeris-red',
  closed: 'bg-aeris-textDim',
};

/**
 * Phase 2 UI: connects to the Python gesture-engine over WebSocket
 * (see gesture-engine/README.md) and surfaces its live feed + confirmed
 * commands. This never touches the CommandQueue directly — that happens
 * inside `useGestureInput` -> `GestureInputManager`, exactly like the
 * keyboard adapter.
 */
export function GesturePanel() {
  const [open, setOpen] = useState(false);
  const { connectionState, connect, disconnect, latestFrame, history, current } = useGestureInput();

  const connected = connectionState === 'connected';
  const busy = connectionState === 'connecting';

  return (
    <div className="pointer-events-auto flex flex-col items-end gap-2">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="glass-panel rounded-lg p-3 w-72"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="hud-label">Gesture Control · Phase 2</span>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${STATE_COLOR[connectionState]}`} />
                <span className="hud-value text-[10px] text-aeris-textDim uppercase">{connectionState}</span>
              </div>
            </div>

            <div className="relative w-full aspect-[4/3] rounded-md overflow-hidden bg-black/50 border border-white/10 mb-2">
              {latestFrame ? (
                <img
                  src={`data:image/jpeg;base64,${latestFrame.frame_jpeg_b64}`}
                  className="w-full h-full object-cover"
                  alt="Live gesture camera feed with hand landmarks"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-aeris-textDim text-xs text-center px-4">
                  {connected ? 'Waiting for camera frames…' : 'Connect to start the CV pipeline'}
                </div>
              )}
              {latestFrame && (
                <span className="absolute bottom-1 right-1.5 hud-value text-[10px] text-aeris-cyan/90 bg-black/40 px-1 rounded">
                  {latestFrame.fps.toFixed(0)} fps · {latestFrame.hands.length} hand
                  {latestFrame.hands.length === 1 ? '' : 's'}
                </span>
              )}
            </div>

            <button
              onClick={() => (connected ? disconnect() : connect())}
              disabled={busy}
              className={`w-full mb-2 rounded-md px-3 py-1.5 text-xs font-medium tracking-wide border transition-colors
                ${
                  connected
                    ? 'bg-aeris-red/10 border-aeris-red/40 text-aeris-red hover:bg-aeris-red/20'
                    : 'bg-aeris-cyan/10 border-aeris-cyan/40 text-aeris-cyan hover:bg-aeris-cyan/20'
                }`}
            >
              {connected ? 'Disconnect Camera' : busy ? 'Connecting…' : 'Connect Camera'}
            </button>

            {current && (
              <div className="rounded-md bg-white/[0.03] border border-white/10 px-2.5 py-2 mb-2">
                <div className="flex items-center justify-between">
                  <span className="hud-value text-xs text-aeris-cyan">{current.gesture}</span>
                  <span className="hud-value text-[11px]">{(current.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="hud-label mt-1 !text-[9px]">
                  {current.kind} · {current.hand ?? '—'} ·{' '}
                  {current.mappedCommand ? current.command : `${current.command} (no sim action yet)`}
                </div>
              </div>
            )}

            <div className="hud-label mb-1">History</div>
            <div className="flex flex-col gap-1 max-h-28 overflow-y-auto pr-1">
              {history.length === 0 && <span className="text-aeris-textDim text-[11px]">No gestures yet</span>}
              {history.map((h, i) => (
                <div key={`${h.timestamp}-${i}`} className="flex items-center justify-between text-[11px]">
                  <span className="text-aeris-text">{h.gesture}</span>
                  <span className="text-aeris-textDim">{(h.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setOpen((o) => !o)}
        className="glass-panel rounded-full w-8 h-8 flex items-center justify-center text-aeris-cyan hud-value text-sm relative"
        title="Gesture control"
      >
        ✋
        {connected && <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-aeris-green" />}
      </button>
    </div>
  );
}
