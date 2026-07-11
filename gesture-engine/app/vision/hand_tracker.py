"""
Thin wrapper around MediaPipe's Hands solution.

Responsible ONLY for: running detection on a BGR frame, drawing the 21
landmarks + connections onto a copy of the frame, and returning structured
per-hand results (landmarks in normalized 0..1 coordinates, handedness,
and confidence). Gesture *interpretation* lives entirely in
`app/gestures/`, never here.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from app.config import settings

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

# MediaPipe's 21-landmark topology, indices 0..20.
NUM_LANDMARKS = 21


@dataclass
class HandResult:
    hand_label: str  # "Left" | "Right"
    handedness_confidence: float
    landmarks: list[tuple[float, float, float]]  # (x, y, z) normalized
    landmarks_px: list[tuple[int, int]]  # pixel coords, for motion tracking
    bounding_box: tuple[float, float, float, float]  # x, y, w, h normalized


class HandTracker:
    def __init__(self) -> None:
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=settings.max_num_hands,
            model_complexity=settings.model_complexity,
            min_detection_confidence=settings.min_detection_confidence,
            min_tracking_confidence=settings.min_tracking_confidence,
        )

    def process(self, frame_bgr: np.ndarray) -> tuple[np.ndarray, list[HandResult]]:
        """Runs detection and returns (annotated_frame, hand_results)."""
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._hands.process(rgb)
        rgb.flags.writeable = True

        annotated = frame_bgr.copy()
        hand_results: list[HandResult] = []

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                mp_drawing.draw_landmarks(
                    annotated,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

                pts_norm = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                pts_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

                xs = [p[0] for p in pts_norm]
                ys = [p[1] for p in pts_norm]
                bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

                label = handedness.classification[0].label
                confidence = handedness.classification[0].score

                hand_results.append(
                    HandResult(
                        hand_label=label,
                        handedness_confidence=confidence,
                        landmarks=pts_norm,
                        landmarks_px=pts_px,
                        bounding_box=bbox,
                    )
                )

                self._draw_confidence_label(annotated, pts_px[0], label, confidence)

        return annotated, hand_results

    @staticmethod
    def _draw_confidence_label(frame: np.ndarray, anchor_px: tuple[int, int], label: str, confidence: float) -> None:
        text = f"{label} {confidence * 100:.0f}%"
        x, y = anchor_px
        cv2.putText(
            frame,
            text,
            (max(0, x - 40), max(20, y - 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 217, 255),
            2,
            cv2.LINE_AA,
        )

    def close(self) -> None:
        self._hands.close()
