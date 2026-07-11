"""Pure geometry helpers operating on normalized MediaPipe landmarks.

Landmark index reference (MediaPipe Hands, 21 points):
  0 WRIST
  1-4  THUMB   (CMC, MCP, IP, TIP)
  5-8  INDEX   (MCP, PIP, DIP, TIP)
  9-12 MIDDLE  (MCP, PIP, DIP, TIP)
  13-16 RING   (MCP, PIP, DIP, TIP)
  17-20 PINKY  (MCP, PIP, DIP, TIP)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float, float]

WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

FINGER_TIPS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
FINGER_PIPS = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
FINGER_MCPS = [THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]
FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]


def dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dist3(a: Point, b: Point) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


@dataclass
class FingerState:
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool

    def count(self) -> int:
        return sum([self.thumb, self.index, self.middle, self.ring, self.pinky])

    def as_list(self) -> list[bool]:
        return [self.thumb, self.index, self.middle, self.ring, self.pinky]


def palm_center(lm: list[Point]) -> Point:
    xs = [lm[i][0] for i in (WRIST, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)]
    ys = [lm[i][1] for i in (WRIST, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP)]
    return (sum(xs) / len(xs), sum(ys) / len(ys), 0.0)


def hand_scale(lm: list[Point]) -> float:
    """A rotation/translation-invariant size reference (wrist -> middle MCP)."""
    return max(dist(lm[WRIST], lm[MIDDLE_MCP]), 1e-6)


def fingers_extended(lm: list[Point], handedness: str) -> FingerState:
    """Determines which fingers are extended, invariant to in-plane hand
    rotation, by comparing each fingertip's distance from the wrist against
    its corresponding PIP joint's distance from the wrist. The thumb uses a
    lateral (x-axis, handedness-aware) test instead, since it flexes
    sideways rather than curling toward the palm.
    """
    scale = hand_scale(lm)

    def extended(tip_idx: int, pip_idx: int, mcp_idx: int) -> bool:
        tip_from_wrist = dist(lm[tip_idx], lm[WRIST])
        pip_from_wrist = dist(lm[pip_idx], lm[WRIST])
        mcp_from_wrist = dist(lm[mcp_idx], lm[WRIST])
        return (tip_from_wrist - pip_from_wrist) > 0.02 * scale and tip_from_wrist > mcp_from_wrist

    index = extended(INDEX_TIP, INDEX_PIP, INDEX_MCP)
    middle = extended(MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP)
    ring = extended(RING_TIP, RING_PIP, RING_MCP)
    pinky = extended(PINKY_TIP, PINKY_PIP, PINKY_MCP)

    # Thumb: compare tip-to-pinky-MCP distance vs thumb-MCP-to-pinky-MCP
    # distance — a mirrored, handedness-agnostic lateral extension test.
    thumb_tip_spread = dist(lm[THUMB_TIP], lm[PINKY_MCP])
    thumb_base_spread = dist(lm[THUMB_MCP], lm[PINKY_MCP])
    thumb = thumb_tip_spread > thumb_base_spread * 1.15

    return FingerState(thumb=thumb, index=index, middle=middle, ring=ring, pinky=pinky)


def average_fingertip_spread(lm: list[Point]) -> float:
    """Average pairwise distance between adjacent fingertips, normalized by
    hand scale. Large values => splayed/spread fingers (e.g. 🖐);
    small values => fingers held together (e.g. ✋).
    """
    scale = hand_scale(lm)
    tips = [lm[INDEX_TIP], lm[MIDDLE_TIP], lm[RING_TIP], lm[PINKY_TIP]]
    pairs = list(zip(tips, tips[1:]))
    return sum(dist(a, b) for a, b in pairs) / (len(pairs) * scale)


def pointing_direction_deg(lm: list[Point]) -> float:
    """Angle (degrees, image-space, 0 = pointing right, 90 = pointing down
    since y grows downward in image coordinates) of the index finger's
    MCP->TIP vector."""
    dx = lm[INDEX_TIP][0] - lm[INDEX_MCP][0]
    dy = lm[INDEX_TIP][1] - lm[INDEX_MCP][1]
    return math.degrees(math.atan2(dy, dx))


def hand_roll_deg(lm: list[Point]) -> float:
    """Approximate in-plane hand rotation using the wrist -> middle-MCP axis."""
    dx = lm[MIDDLE_MCP][0] - lm[WRIST][0]
    dy = lm[MIDDLE_MCP][1] - lm[WRIST][1]
    return math.degrees(math.atan2(dy, dx))


def thumb_direction_deg(lm: list[Point]) -> float:
    """Angle (degrees, image-space, 0 = right, 90 = down, -90 = up, ±180 =
    left) of the thumb's MCP->TIP vector. Used to distinguish a vertical
    thumbs-up/down pose from a horizontal thumb-pointing-left/right pose,
    which map to different gestures despite an identical finger-extension
    pattern (thumb-only extended).
    """
    dx = lm[THUMB_TIP][0] - lm[THUMB_MCP][0]
    dy = lm[THUMB_TIP][1] - lm[THUMB_MCP][1]
    return math.degrees(math.atan2(dy, dx))

