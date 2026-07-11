import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { GestureInputManager } from '@/core/gestureInputManager';
import type { GestureHistoryEntry } from '@/core/gestureInputManager';
import { useDroneStore } from '@/state/droneStore';
import type { GestureConnectionState, GestureFrameMessage } from '@/types/gesture.types';

const MAX_HISTORY = 25;

export interface UseGestureInputResult {
  connectionState: GestureConnectionState;
  connect: (cameraIndex?: number) => void;
  disconnect: () => void;
  latestFrame: GestureFrameMessage | null;
  history: GestureHistoryEntry[];
  current: GestureHistoryEntry | null;
}

/**
 * Mirrors `useKeyboardInput`: mounts the GestureInputManager, forwards
 * confirmed gesture commands into the same `dispatchCommand` the keyboard
 * uses, and exposes connection/frame/history state for the GesturePanel UI.
 * The socket is NOT opened automatically — the operator explicitly
 * connects it from the dashboard, since it requests webcam access on the
 * backend.
 */
export function useGestureInput(wsUrl?: string): UseGestureInputResult {
  const dispatchCommand = useDroneStore((s) => s.dispatchCommand);

  const [connectionState, setConnectionState] = useState<GestureConnectionState>('idle');
  const [latestFrame, setLatestFrame] = useState<GestureFrameMessage | null>(null);
  const [history, setHistory] = useState<GestureHistoryEntry[]>([]);
  const [current, setCurrent] = useState<GestureHistoryEntry | null>(null);

  const managerRef = useRef<GestureInputManager | null>(null);

  const manager = useMemo(() => {
    const instance = new GestureInputManager(
      {
        onDispatch: (type) => dispatchCommand(type, 'gesture'),
        onGestureCommand: (entry) => {
          setCurrent(entry);
          setHistory((prev) => [entry, ...prev].slice(0, MAX_HISTORY));
        },
        onFrame: (frame) => setLatestFrame(frame),
        onConnectionStateChange: (state) => setConnectionState(state),
      },
      wsUrl,
    );
    managerRef.current = instance;
    return instance;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatchCommand, wsUrl]);

  useEffect(() => {
    return () => {
      managerRef.current?.disconnect();
    };
  }, [manager]);

  const connect = useCallback((cameraIndex?: number) => manager.connect(cameraIndex), [manager]);
  const disconnect = useCallback(() => manager.disconnect(), [manager]);

  return { connectionState, connect, disconnect, latestFrame, history, current };
}
