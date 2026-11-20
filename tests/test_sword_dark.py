"""계산해 만드는 검 어둠(블랙홀) 테스트 (2026-11-20 사용자, pico2d 없이)."""
import random
import unittest

from game.player.sword_dark import DarkField
from game.player.sword_lightning import SWORD_SHAPE


class DarkFieldTest(unittest.TestCase):
    def test_everything_is_pulled_into_the_blade(self):
        f = DarkField(random.Random(1))
        f.update(1 / 60)
        start = {id(m): abs(m.off) for m in f.motes}
        for _ in range(10):
            f.update(1 / 60)
        moved = [abs(m.off) < start[id(m)] for m in f.motes if id(m) in start]
        self.assertTrue(moved)
        self.assertTrue(all(moved))  # 모두 칼날 쪽으로 끌려옴

    def test_absorbed_at_blade_and_pulses_irregularly(self):
        f = DarkField(random.Random(2))
        pulses, was = 0, False
        for _ in range(600):
            f.update(1 / 60)
            for m in f.motes:
                self.assertGreater(abs(m.off), 0.5)  # 칼날에 닿은 것은 사라짐
            if f.pulse > 0 and not was:
                pulses += 1
            was = f.pulse > 0
        self.assertGreater(pulses, 4)  # 10초에 여러 번 맥동

    def test_reach_limits_while_enchanting(self):
        f = DarkField(random.Random(3))
        f.update(1 / 60, reach=0.0)
        self.assertEqual(f.motes, [])  # 아직 안 번졌으면 아무것도 없음
        pix = f.pixels((0.0, 0.0), (1.0, 0.0), SWORD_SHAPE, reach=0.0)
        self.assertTrue(all(x <= SWORD_SHAPE.start + 1 for x, _, _ in pix))


if __name__ == "__main__":
    unittest.main()
