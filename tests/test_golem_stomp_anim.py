"""골렘 ③ 발 구르기 동작 그림: 예고·자세 되돌림 진행도에 따라 고르는 그림 번호와 그림 파일 규격."""
import unittest

from game import config
from game.enemies.golem import KICK, RECOVER, SLAM, STOMP, WINDUP, Golem

ANIM = config.GOLEM_STOMP_ANIM


def open_room(cols=16, rows=10):
    return lambda c, r: not (0 < c < cols - 1 and 0 < r < rows - 1)


def png_size(path):
    header = path.read_bytes()[:24]
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


class StompFrameTest(unittest.TestCase):
    def setUp(self):
        self.golem = Golem(6, 4, open_room())
        self.player = (4, 4)

    def step(self, seconds):
        self.golem.update(seconds, self.player, lambda c, r: True)

    def test_windup_lifts_then_falls_at_the_end(self):
        g = self.golem
        g._windup(STOMP, self.player)
        self.assertEqual(g.stomp_frame, 0)
        total = config.GOLEM_STOMP["windup"]
        self.step(total * 0.7)  # 무릎을 다 든 뒤 위에서 멈춤
        self.assertEqual(g.stomp_frame, 7)
        self.step(total * 0.25)  # 터지기 직전: 떨어지는 한 장
        self.assertEqual(g.state, WINDUP)
        self.assertEqual(g.stomp_frame, 8)

    def test_release_shows_impact_squash_then_rises(self):
        g = self.golem
        g._windup(STOMP, self.player)
        self.step(config.GOLEM_STOMP["windup"] + 0.001)
        self.assertEqual(g.state, RECOVER)
        self.assertEqual(g.stomp_frame, 9)  # 착지
        self.assertGreater(g.stomp_squash, 0.0)
        self.step(config.GOLEM_RECOVER_TIME * 0.5)
        self.assertEqual(g.stomp_squash, 0.0)
        self.assertIn(g.stomp_frame, ANIM["recover_frames"][3:7])
        self.step(config.GOLEM_RECOVER_TIME * 0.45)
        self.assertEqual(g.stomp_frame, 18)  # 다 일어섬
        self.step(config.GOLEM_RECOVER_TIME)
        self.assertIsNone(g.stomp_frame)  # 쉬는 동안은 서 있는 그림

    def test_other_patterns_use_standing_sprite(self):
        for pattern in (SLAM, KICK):
            g = Golem(6, 4, open_room())
            g._windup(pattern, self.player)
            self.assertIsNone(g.stomp_frame, pattern)
            self.assertEqual(g.stomp_squash, 0.0)

    def test_frame_tables_are_consistent(self):
        for frames, ends in ((ANIM["windup_frames"], ANIM["windup_ends"]),
                             (ANIM["recover_frames"], ANIM["recover_ends"])):
            self.assertEqual(len(frames), len(ends))
            self.assertEqual(list(ends), sorted(ends))
            self.assertEqual(ends[-1], 1.0)


class StompSpriteFileTest(unittest.TestCase):
    def test_sheets_exist_for_four_directions(self):
        w, h = ANIM["frame_size"]
        count = max(ANIM["windup_frames"] + ANIM["recover_frames"]) + 1
        for view in ("south", "north", "east", "west"):
            path = config.GOLEM_IMAGE_DIR / f"stomp_{view}.png"
            self.assertTrue(path.exists(), view)
            sw, sh = png_size(path)
            self.assertEqual(sh, h, view)
            self.assertEqual(sw % w, 0, view)
            self.assertGreaterEqual(sw // w, count, view)


if __name__ == "__main__":
    unittest.main()
