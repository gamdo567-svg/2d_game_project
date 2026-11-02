import unittest

from game.core.clock import FrameClock


class FrameClockTest(unittest.TestCase):
    def test_first_tick_returns_zero(self):
        clock = FrameClock(max_dt=0.1)
        self.assertEqual(clock.tick(10.0), 0.0)

    def test_returns_elapsed_time(self):
        clock = FrameClock(max_dt=0.1)
        clock.tick(10.0)
        self.assertAlmostEqual(clock.tick(10.016), 0.016)
        self.assertAlmostEqual(clock.tick(10.050), 0.034)

    def test_dt_is_clamped_to_max(self):
        clock = FrameClock(max_dt=0.1)
        clock.tick(0.0)
        self.assertEqual(clock.tick(5.0), 0.1)

    def test_time_going_backwards_returns_zero(self):
        clock = FrameClock(max_dt=0.1)
        clock.tick(10.0)
        self.assertEqual(clock.tick(9.0), 0.0)

    def test_total_time_accumulates_clamped_dt(self):
        clock = FrameClock(max_dt=0.1)
        clock.tick(0.0)
        clock.tick(0.05)
        clock.tick(3.0)  # 0.1 로 제한
        self.assertAlmostEqual(clock.total_time, 0.15)

    def test_invalid_max_dt(self):
        with self.assertRaises(ValueError):
            FrameClock(max_dt=0)


if __name__ == "__main__":
    unittest.main()
