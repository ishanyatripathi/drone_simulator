/**
 * Mirrors gesture-engine/app/models/command.py and landmarks.py.
 * Kept in sync by hand since the two projects don't share a build step.
 */

export interface GestureCommandMessage {
  command: string; // abstract command name, e.g. "TAKEOFF" | "CIRCLE" | "RETURN_HOME"
  gesture: string; // human-readable label, e.g. "Thumbs Up"
  confidence: number; // 0..1
  timestamp: number; // ms epoch (set server-side)
  kind: 'static' | 'dynamic';
  hand: 'Left' | 'Right' | null;
  session_id: string | null;
}

export interface GestureLandmark {
  x: number;
  y: number;
  z: number;
}

export interface GestureHandDetection {
  hand: 'Left' | 'Right';
  handedness_confidence: number;
  landmarks: GestureLandmark[]; // 21 points, MediaPipe order
  bounding_box: [number, number, number, number];
}

export interface GestureFrameMessage {
  frame_jpeg_b64: string;
  hands: GestureHandDetection[];
  fps: number;
  frame_index: number;
}

export interface GestureStatusMessage {
  state: 'connected' | 'disconnected' | 'error';
  session_id?: string;
  detail?: string;
}

export type GestureSocketEnvelope =
  | { type: 'frame'; payload: GestureFrameMessage }
  | { type: 'command'; payload: GestureCommandMessage }
  | { type: 'status'; payload: GestureStatusMessage }
  | { type: 'error'; payload: { detail: string } };

export type GestureConnectionState = 'idle' | 'connecting' | 'connected' | 'error' | 'closed';
