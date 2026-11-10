import unittest

from game.player.actions import Jump, Parry


class JumpTest(unittest.TestCase):
    def setUp(self):
        self.jump = Jump(duration=0.4, max_height=0.5, frame_count=4)

    def test_crouch_air_land_phases(self):
        heights = []
        for _ in range(40):
            heights.append(self.jump.height)
            self.jump.update(0.01)
        self.assertEqual(max(heights[:10]), 0.0)  # 처음 1/4: 웅크림 (땅)
        self.assertEqual(max(heights[31:]), 0.0)  # 마지막 1/4: 착지 (땅)
        self.assertAlmostEqual(max(heights), 0.5, places=2)  # 가운데에서 최고 높이
        self.assertTrue(self.jump.finished)
        self.assertEqual(self.jump.height, 0.0)

    def test_frames_follow_progress(self):
        frames = []
        for _ in range(40):
            frames.append(self.jump.frame_index)
            self.jump.update(0.01)
        self.assertEqual(frames, sorted(frames))
        self.assertEqual(set(frames), {0, 1, 2, 3})
        self.assertEqual(self.jump.frame_index, 3)  # 끝난 뒤에도 마지막 프레임

    def test_airborne_only_in_middle(self):
        self.assertFalse(self.jump.is_airborne)
        self.jump.update(0.2)
        self.assertTrue(self.jump.is_airborne)

    def test_reset(self):
        self.jump.update(1.0)
        self.jump.reset()
        self.assertFalse(self.jump.finished)
        self.assertEqual(self.jump.frame_index, 0)


class ParryTest(unittest.TestCase):
    def test_window_then_recovery(self):
        parry = Parry(duration=0.4, window=0.15, frame_count=4)
        self.assertTrue(parry.is_active)
        parry.update(0.14)
        self.assertTrue(parry.is_active)
        parry.update(0.02)
        self.assertFalse(parry.is_active)
        self.assertFalse(parry.finished)
        parry.update(0.3)
        self.assertTrue(parry.finished)

    def test_invalid_values(self):
        with self.assertRaises(ValueError):
            Parry(duration=0.4, window=0.5, frame_count=4)
        with self.assertRaises(ValueError):
            Jump(duration=0, max_height=0.5, frame_count=4)


if __name__ == "__main__":
    unittest.main()
