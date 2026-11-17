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

    def test_kick_pulls_back_then_kicks_without_squash(self):
        g = Golem(6, 4, open_room())
        g._windup(KICK, self.player)
        self.assertEqual(g.attack_anim[0], "kick")
        self.assertIsNone(g.stomp_frame)
        self.assertEqual(g.attack_frame, 0)
        g.update(config.GOLEM_KICK["windup"] * 0.6, self.player, lambda c, r: True)
        self.assertEqual(g.attack_frame, 3)  # 다리를 뒤로 당긴 채 멈춤
        g.update(config.GOLEM_KICK["windup"] * 0.4 + 0.001, self.player, lambda c, r: True)
        self.assertEqual(g.state, RECOVER)
        self.assertEqual(g.attack_frame, 4)  # 차올림
        self.assertEqual(g.attack_squash, 0.0)  # 눌림 없음
        self.assertEqual(g.effects, [])  # 이펙트·화면 흔들림 없음 (사용자 요청)
        g.update(config.GOLEM_RECOVER_TIME * 0.95, self.player, lambda c, r: True)
        self.assertEqual(g.attack_frame, 10)

    def test_kick_range_three_wide_four_ahead(self):
        self.assertEqual((config.GOLEM_KICK["width"], config.GOLEM_KICK["depth"]), (3, 4))
        g = Golem(6, 4, open_room())
        g._windup(KICK, (2, 4))  # 왼쪽을 봄
        self.assertEqual(len(g.target_tiles), 3 * 4)

    def test_slam_lifts_then_impact_then_rises(self):
        g = Golem(6, 4, open_room())
        g._windup(SLAM, self.player)
        self.assertEqual(g.attack_anim[0], "slam")
        self.assertIsNone(g.stomp_frame)  # ③ 전용 이름은 None
        self.assertEqual(g.attack_frame, 0)
        g.update(config.GOLEM_SLAM["windup"] * 0.8, self.player, lambda c, r: True)
        self.assertEqual(g.attack_frame, 6)  # 위에서 멈춤
        g.update(config.GOLEM_SLAM["windup"] * 0.2 + 0.001, self.player, lambda c, r: True)
        self.assertEqual(g.state, RECOVER)
        self.assertEqual(g.attack_frame, 7)  # 착지
        self.assertGreater(g.attack_squash, 0.0)
        g.update(config.GOLEM_RECOVER_TIME * 0.95, self.player, lambda c, r: True)
        self.assertEqual(g.attack_frame, 13)

    def test_frame_tables_are_consistent(self):
        for frames, ends in ((ANIM["windup_frames"], ANIM["windup_ends"]),
                             (ANIM["recover_frames"], ANIM["recover_ends"])):
            self.assertEqual(len(frames), len(ends))
            self.assertEqual(list(ends), sorted(ends))
            self.assertEqual(ends[-1], 1.0)


class WalkFrameTest(unittest.TestCase):
    def test_walk_frames_follow_distance(self):
        g = Golem(6, 4, open_room())
        self.assertIsNone(g.walk_frame)  # 서 있음
        anim = config.GOLEM_WALK_ANIM
        seen = []
        player = (12, 4)  # 멀리 오른쪽
        can = lambda c, r: True  # noqa: E731
        self.assertTrue(g._step_toward(player, can))  # 한 칸 걷기 시작 (패턴 고르기의 난수와 무관하게)
        for _ in range(round(60 / config.GOLEM_MOVE_SPEED)):
            if g.walk_frame is not None:
                seen.append(g.walk_frame)
            g.update(1 / 60, player, can)
        self.assertTrue(seen, "걸어가는 동안 걷기 그림을 써야 한다")
        self.assertTrue(set(seen) <= set(range(anim["frames"])))
        # 한 칸 걸을 때 주기의 절반(4장)쯤 넘어간다
        self.assertGreaterEqual(len(set(seen)), anim["frames"] // 2)

    def test_dead_golem_has_no_walk_frame(self):
        g = Golem(6, 4, open_room())
        g._move_t = 0.5
        g.take_hit(10_000, (1, 0))
        self.assertIsNone(g.walk_frame)


class StompSpriteFileTest(unittest.TestCase):
    def test_kick_sheets_exist_for_four_directions(self):
        anim = config.GOLEM_KICK_ANIM
        w, h = anim["frame_size"]
        count = max(anim["windup_frames"] + anim["recover_frames"]) + 1
        for view in ("south", "north", "east", "west"):
            path = config.GOLEM_IMAGE_DIR / f"kick_{view}.png"
            self.assertTrue(path.exists(), view)
            self.assertEqual(png_size(path), (w * count, h), view)

    def test_slam_sheets_exist_for_four_directions(self):
        anim = config.GOLEM_SLAM_ANIM
        w, h = anim["frame_size"]
        count = max(anim["windup_frames"] + anim["recover_frames"]) + 1
        for view in ("south", "north", "east", "west"):
            path = config.GOLEM_IMAGE_DIR / f"slam_{view}.png"
            self.assertTrue(path.exists(), view)
            self.assertEqual(png_size(path), (w * count, h), view)

    def test_walk_sheets_exist_for_four_directions(self):
        anim = config.GOLEM_WALK_ANIM
        w, h = anim["frame_size"]
        for view in ("south", "north", "east", "west"):
            path = config.GOLEM_IMAGE_DIR / f"walk_{view}.png"
            self.assertTrue(path.exists(), view)
            self.assertEqual(png_size(path), (w * anim["frames"], h), view)

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
