import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.gestures.stability_filter import StabilityFilter


class StabilityFilterTests(unittest.TestCase):
    def test_continuous_emission_for_same_gesture(self) -> None:
        fake_settings = SimpleNamespace(
            min_gesture_confidence=0.5,
            confirmation_window_ms=100,
            cooldown_ms=0,
            max_dropped_frames=3,
            repeat_interval_ms=50,
        )

        with patch("app.gestures.stability_filter.settings", fake_settings):
            filter_ = StabilityFilter()

            first = filter_.update("GESTURE_A", 0.6, now=0.0)
            self.assertIsNone(first)

            second = filter_.update("GESTURE_A", 0.6, now=0.11)
            self.assertEqual(second, ("GESTURE_A", 0.6))

            third = filter_.update("GESTURE_A", 0.6, now=0.16)
            self.assertEqual(third, ("GESTURE_A", 0.6))

            low_conf = filter_.update("GESTURE_A", 0.4, now=0.17)
            self.assertIsNone(low_conf)

            fourth = filter_.update("GESTURE_A", 0.6, now=0.22)
            self.assertEqual(fourth, ("GESTURE_A", 0.6))


if __name__ == "__main__":
    unittest.main()
