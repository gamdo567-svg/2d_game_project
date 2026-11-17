"""이펙트(SpriteEffect)와 화면 흔들림(ScreenShake) 테스트."""
import unittest

from game import config
from game.effects.effect import ScreenShake, SpriteEffect
from game.enemies.golem import KICK, LASER, SLAM, STOMP, Golem

SPEC = {"path": "x.png", "frame_size": 16, "columns": 4, "frames": 10, "fps": 10}


def open_room(cols=16, rows=10):
    return lambda c, r: not (0 < c < cols - 1 and 0 < r < rows - 1)


class SpriteEffectTest(unittest.TestCase):
    def test_frame_follows_time_and_finishes(self):
        e = SpriteEffect(SPEC, 3.0, 4.0)
        self.assertEqual(e.frame_index, 0)
        self.assertAlmostEqual(e.duration, 1.0)
        e.update(0.25)
        self.assertEqual(e.frame_index, 2)
        e.update(0.7)
        self.assertEqual(e.frame_index, 9)
        self.assertFalse(e.finished)
        e.update(0.2)
        self.assertTrue(e.finished)
        self.assertEqual(e.frame_index, 9)  # 마지막 프레임을 넘지 않는다
        self.assertIsNone(e.shake)

    def test_stomp_effect_sheet_spec(self):
        spec = config.GOLEM_STOMP_EFFECT
        self.assertAlmostEqual(SpriteEffect(spec, 0, 0).duration, 2.5)
        self.assertTrue(spec["path"].exists(), "발 구르기 이펙트 시트가 있어야 한다")
        header = spec["path"].read_bytes()[:24]  # PNG IHDR: 16~24 바이트가 가로·세로 (Pillow 없이 확인)
        w, h = int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
        rows = -(-spec["frames"] // spec["columns"])
        self.assertEqual((w, h), (spec["columns"] * spec["frame_size"], rows * spec["frame_size"]))


class ScreenShakeTest(unittest.TestCase):
    def test_decays_to_zero(self):
        s = ScreenShake()
        self.assertEqual(s.offset, (0, 0))
        s.start(amplitude=8, duration=0.4, frequency=18)
        seen = set()
        for _ in range(20):
            s.update(0.01)
            x, y = s.offset
            self.assertLessEqual(abs(x), 8)
            self.assertLessEqual(abs(y), 8)
            seen.add((x, y))
        self.assertGreater(len(seen), 3)  # 실제로 흔들린다
        s.update(1.0)
        self.assertFalse(s.active)
        self.assertEqual(s.offset, (0, 0))

    def test_weaker_shake_does_not_override(self):
        s = ScreenShake()
        s.start(amplitude=8, duration=1.0, frequency=10)
        s.update(0.1)
        s.start(amplitude=2, duration=1.0, frequency=10)
        self.assertAlmostEqual(s.amplitude, 8)


class GolemStompEffectTest(unittest.TestCase):
    def release(self, pattern):
        golem = Golem(6, 4, open_room())
        golem._windup(pattern, (4, 4))
        golem.update(golem.state_left + 0.001, (4, 4), lambda c, r: True)
        return golem

    def test_stomp_starts_effect_at_feet_tile(self):
        golem = self.release(STOMP)
        self.assertEqual(len(golem.effects), 1)
        effect = golem.effects[0]
        self.assertEqual((effect.x, effect.y), (7.5, 4.5))  # 발 칸 (7, 4) 가운데 (3×3 몸 (6,4)~(8,6) 의 맨 아래 줄 가운데)
        self.assertIsNotNone(effect.shake)
        golem.update(0.01, (4, 4), lambda c, r: True)
        self.assertEqual(golem.effects, [])  # 한 프레임만 전달

    def test_other_patterns_have_no_effect(self):
        for pattern in (KICK, LASER):
            self.assertEqual(self.release(pattern).effects, [], pattern)

    def test_slam_starts_effect_at_front_area_center(self):
        golem = Golem(6, 4, open_room())
        golem._windup(SLAM, (4, 4))
        area = golem.target_tiles
        golem.update(golem.state_left + 0.001, (4, 4), lambda c, r: True)
        self.assertEqual(len(golem.effects), 1)
        effect = golem.effects[0]
        self.assertIs(effect.spec, config.GOLEM_SLAM_EFFECT)
        self.assertAlmostEqual(effect.x, sum(c for c, _ in area) / len(area) + 0.5)
        self.assertAlmostEqual(effect.y, sum(r for _, r in area) / len(area) + 0.5)
        self.assertIsNotNone(effect.shake)

    def test_slam_effect_sheet_spec(self):
        spec = config.GOLEM_SLAM_EFFECT
        header = spec["path"].read_bytes()[:24]
        w, h = int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
        rows = -(-spec["frames"] // spec["columns"])
        self.assertEqual((w, h), (spec["columns"] * spec["frame_size"], rows * spec["frame_size"]))


class SceneEffectTest(unittest.TestCase):
    def test_scene_plays_effect_and_shakes_camera(self):
        from game.scenes.field_scene import FieldScene
        from game.world.grid import Grid
        from game.world.tile_map import TileMap
        from game.input.input_state import InputState
        from tests.test_golem import ROOM

        tile_map = TileMap.from_text(ROOM)
        scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        golem = scene.golems[0]
        golem._windup(STOMP, (scene.player.col, scene.player.row))
        inp = InputState()
        dt = 1 / 120
        offsets = set()
        for _ in range(round((golem.state_left + 0.2) / dt)):
            scene.update(dt, inp)
            offsets.add(scene.shake.offset)
        self.assertEqual(len(scene.effects), 1)
        self.assertGreater(len(offsets), 2)
        effect = scene.effects[0]
        for _ in range(round(0.4 / dt)):
            scene.update(dt, inp)
        self.assertEqual(scene.shake.offset, (0, 0))  # 흔들림은 짧게 끝남
        for _ in range(round(2.0 / dt)):
            scene.update(dt, inp)
        self.assertTrue(effect.finished)
        self.assertNotIn(effect, scene.effects)  # 다 재생하면 사라짐

    def test_stomp_effect_drawn_at_range_size(self):
        # 발 구르기 이펙트는 ③ 범위(7×7칸) 크기로 그린다 (2026-11-17 사용자 요청)
        from game.scenes.field_scene import FieldScene
        from game.world.grid import Grid
        from game.world.tile_map import TileMap
        from game.effects.effect import SpriteEffect
        from tests.test_golem import ROOM

        class Rec:
            def __init__(self):
                self.calls = []

            def draw_sheet_frame(self, *args):
                self.calls.append(args)

        tile_map = TileMap.from_text(ROOM)
        scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        rec = Rec()
        scene._draw_effect(rec, SpriteEffect(config.GOLEM_STOMP_EFFECT, 5.5, 4.5))
        draw_w, draw_h = rec.calls[0][-2:]
        size = config.GOLEM_STOMP["size"] * config.RENDER_TILE_SIZE
        self.assertEqual((draw_w, draw_h), (size, size))


if __name__ == "__main__":
    unittest.main()
