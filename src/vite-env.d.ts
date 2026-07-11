/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional override for the gesture engine's WebSocket URL.
   * Defaults to ws://localhost:8000/ws/gestures when unset. See .env.example. */
  readonly VITE_GESTURE_WS_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

