import unittest

from game.player.animation import LoopAnimation


def run(anim, seconds, fps):
    dt = 1.0 / fps
    for _ in range(round(seconds * fps)):
        anim.update(dt)


class LoopAnimationTest(unittest.TestCase):
    def test_starts_at_first_frame(self):
        self.assertEqual(LoopAnimation(5, 0.1).frame_index, 0)

    def test_advances_by_time(self):
        anim = LoopAnimation(5, 0.1)
        anim.update(0.25)
        self.assertEqual(anim.frame_index, 2)

    def test_loops(self):
        anim = LoopAnimation(5, 0.1)
        anim.update(0.55)  # 한 바퀴(0.5초) + 0.05초
        self.assertEqual(anim.frame_index, 0)
        anim.update(0.1)
        self.assertEqual(anim.frame_index, 1)

    def test_fps_independent(self):
        slow, fast = LoopAnimation(5, 0.1), LoopAnimation(5, 0.1)
        run(slow, 0.35, fps=20)
        run(fast, 0.35, fps=200)
        self.assertEqual(slow.frame_index, fast.frame_index)

    def test_reset(self):
        anim = LoopAnimation(5, 0.1)
        anim.update(0.33)
        anim.reset()
        self.assertEqual(anim.frame_index, 0)

    def test_invalid_args(self):
        with self.assertRaises(ValueError):
            LoopAnimation(0, 0.1)
        with self.assertRaises(ValueError):
            LoopAnimation(5, 0)


if __name__ == "__main__":
    unittest.main()
