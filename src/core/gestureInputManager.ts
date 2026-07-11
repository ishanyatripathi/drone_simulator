import { CommandType } from '@/types/command.types';
import type {
  GestureCommandMessage,
  GestureConnectionState,
  GestureFrameMessage,
  GestureSocketEnvelope,
} from '@/types/gesture.types';
import { resolveGestureCommand } from './gestureCommandMap';

export interface GestureHistoryEntry {
  gesture: string;
  command: string;
  mappedCommand: CommandType | null;
  confidence: number;
  kind: 'static' | 'dynamic';
  hand: string | null;
  timestamp: number;
}

interface GestureInputManagerCallbacks {
  /** Called for every confirmed gesture whose command maps to an existing
   * simulator CommandType — this is the only callback that should ever
   * touch the CommandQueue. */
  onDispatch: (type: CommandType) => void;
  /** Called for every confirmed gesture, mapped or not, for UI/history display. */
  onGestureCommand?: (entry: GestureHistoryEntry) => void;
  /** Called on every annotated video frame + landmark broadcast. */
  onFrame?: (frame: GestureFrameMessage) => void;
  onConnectionStateChange?: (state: GestureConnectionState) => void;
}

// Overridable via VITE_GESTURE_WS_URL (see .env.example) for cases where
// the gesture engine runs on a different host/port than the default local
// dev setup. In production, the browser will try the same host by default
// so the gesture backend can be deployed behind the same origin or a proxy.
function resolveGestureSocketUrl(explicitUrl?: string): string {
  if (explicitUrl) {
    return explicitUrl;
  }

  if (import.meta.env.VITE_GESTURE_WS_URL) {
    return import.meta.env.VITE_GESTURE_WS_URL;
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    const isLocalHost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';

    if (isLocalHost) {
      return `${protocol === 'https:' ? 'wss' : 'ws'}://localhost:8000/ws/gestures`;
    }

    const wsProtocol = protocol === 'https:' ? 'wss' : 'ws';
    return `${wsProtocol}://${window.location.host}/ws/gestures`;
  }

  return 'ws://localhost:8000/ws/gestures';
}

const DEFAULT_URL = resolveGestureSocketUrl();

/**
 * GestureInputManager
 * ---------------------
 * The Phase 2 counterpart to `KeyboardInputManager`. It knows nothing
 * about physics or rendering — its sole job is turning confirmed gesture
 * events (already debounced server-side per the safety spec) into
 * `CommandType` values, exactly like the keyboard adapter. Both adapters
 * can run side by side, since they both just enqueue onto the same
 * CommandQueue via the store's `dispatchCommand`.
 */
export class GestureInputManager {
  private socket: WebSocket | null = null;
  private readonly url: string;
  private readonly callbacks: GestureInputManagerCallbacks;
  private _state: GestureConnectionState = 'idle';

  constructor(callbacks: GestureInputManagerCallbacks, url: string = DEFAULT_URL) {
    this.callbacks = callbacks;
    this.url = url;
  }

  connect(cameraIndex?: number): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const target = cameraIndex !== undefined ? `${this.url}?camera=${cameraIndex}` : this.url;
    this.setState('connecting');

    const ws = new WebSocket(target);
    this.socket = ws;

    ws.onopen = () => this.setState('connected');
    ws.onclose = () => this.setState('closed');
    ws.onerror = () => this.setState('error');
    ws.onmessage = (event) => this.handleMessage(event.data);
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = null;
    this.setState('idle');
  }

  get state(): GestureConnectionState {
    return this._state;
  }

  private setState(state: GestureConnectionState): void {
    this._state = state;
    this.callbacks.onConnectionStateChange?.(state);
  }

  private handleMessage(raw: string): void {
    let envelope: GestureSocketEnvelope;
    try {
      envelope = JSON.parse(raw);
    } catch {
      return;
    }

    switch (envelope.type) {
      case 'frame':
        this.callbacks.onFrame?.(envelope.payload);
        break;
      case 'command':
        this.handleCommand(envelope.payload);
        break;
      case 'status':
        break;
      case 'error':
        this.setState('error');
        break;
    }
  }

  private handleCommand(payload: GestureCommandMessage): void {
    const mapped = resolveGestureCommand(payload.command);

    this.callbacks.onGestureCommand?.({
      gesture: payload.gesture,
      command: payload.command,
      mappedCommand: mapped,
      confidence: payload.confidence,
      kind: payload.kind,
      hand: payload.hand,
      timestamp: payload.timestamp,
    });

    if (mapped !== null) {
      this.callbacks.onDispatch(mapped);
    }
  }
}
