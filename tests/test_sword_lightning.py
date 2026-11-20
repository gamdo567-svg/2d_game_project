"""계산해 만드는 검 전기 테스트 (2026-11-20 사용자: 미리 그린 번개는 일정해 보임, pico2d 없이)."""
import random
import unittest

from game.player.sword_lightning import MAX_ARCS, SWORD_SHAPE, WHITE, LightningField


class LightningFieldTest(unittest.TestCase):
    def test_bolts_are_short_lived_and_keep_changing(self):
        f = LightningField(random.Random(1))
        shapes = set()
        for _ in range(120):
            f.update(1 / 60)
            self.assertLessEqual(sum(1 for b in f.bolts if b.core == WHITE), MAX_ARCS + 1)
            for b in f.bolts:
                self.assertLess(b.age, b.life)
                shapes.add(tuple(round(a, 2) for a, _ in b.points[:2]))
        self.assertGreater(len(shapes), 20)  # 2초 동안 서로 다른 번개가 많이 (반복되지 않음)

    def test_discharges_at_irregular_intervals(self):
        f = LightningField(random.Random(2))
        times, t, was = [], 0.0, False
        for _ in range(600):
            f.update(1 / 60)
            t += 1 / 60
            if f.flash > 0 and not was:
                times.append(t)
            was = f.flash > 0
        gaps = [b - a for a, b in zip(times, times[1:])]
        self.assertGreater(len(gaps), 5)
        self.assertGreater(max(gaps) - min(gaps), 0.2)  # 일정하지 않음

    def test_reach_limits_arcs_while_enchanting(self):
        f = LightningField(random.Random(3))
        for _ in range(60):
            f.update(1 / 60, reach=0.4)
            for b in f.bolts:
                if b.core == WHITE:
                    self.assertLessEqual(min(a for a, _ in b.points), 0.45)

    def test_pixels_stay_near_the_blade(self):
        f = LightningField(random.Random(4))
        for _ in range(30):
            f.update(1 / 60)
        for x, y, _ in f.pixels((0.0, 0.0), (1.0, 0.0), SWORD_SHAPE):
            self.assertTrue(-1 <= x <= SWORD_SHAPE.end + 25, x)  # 스파크·방전이 멀리 가도 칼 둘레


if __name__ == "__main__":
    unittest.main()
