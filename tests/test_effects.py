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
        self.assertEqual((effect.x, effect.y), (6.5, 4.5))  # 발 칸 (6, 4) 가운데 (몸 1×2 의 아래 칸)
        self.assertIsNotNone(effect.shake)
        golem.update(0.01, (4, 4), lambda c, r: True)
        self.assertEqual(golem.effects, [])  # 한 프레임만 전달

    def test_other_patterns_have_no_effect(self):
        self.assertEqual(self.release(KICK).effects, [])

    def test_laser_blast_at_aim(self):
        # ④ 레이저 (2026-11-18): 조준점에서 폭발 이펙트 (인물 위, 화면 흔들림)
        golem = self.release(LASER)
        (effect,) = golem.effects
        self.assertIs(effect.spec, config.GOLEM_LASER_BLAST_EFFECT)
        self.assertEqual((effect.x, effect.y), golem.aim)
        self.assertTrue(effect.spec["on_top"])
        self.assertIsNotNone(effect.shake)

    def test_laser_charge_motes_run_by_time_orb_by_progress(self):
        # 빛 알갱이는 실제 시간으로 돌고(1/fps 마다 다음 장), 구는 충전 진행도로 커진다
        golem = Golem(6, 4, open_room())
        golem._windup(LASER, (2, 4))
        spec = config.GOLEM_LASER_CHARGE
        self.assertEqual(golem.laser_charge_frames, (0, 0))
        golem.update(1.0 / spec["motes_fps"] + 0.001, (2, 4), lambda c, r: True)
        self.assertEqual(golem.laser_charge_frames[0], 1)
        golem.update(config.GOLEM_LASER["windup"] - 0.1, (2, 4), lambda c, r: True)
        self.assertEqual(golem.laser_charge_frames[1], spec["orb_frames"] - 1)

    def test_laser_effect_sheets_match_spec(self):
        from PIL import Image
        charge = config.GOLEM_LASER_CHARGE
        with Image.open(charge["motes_path"]) as im:
            self.assertEqual(im.size, (charge["motes_size"] * charge["motes_frames"], charge["motes_size"]))
        with Image.open(charge["orb_path"]) as im:
            self.assertEqual(im.size, (charge["orb_size"] * charge["orb_frames"], charge["orb_size"]))
        blast = config.GOLEM_LASER_BLAST_EFFECT
        with Image.open(blast["path"]) as im:
            self.assertEqual(im.size, (blast["frame_size"] * blast["frames"], blast["frame_size"]))
        self.assertTrue(config.GOLEM_LASER_BEAM["path"].exists())

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

    def test_parry_success_starts_spark_on_top(self):
        # 패링에 성공하면 칼이 막은 자리(바라보는 쪽 앞)에서 노란 불꽃 이펙트가 인물 위에 그려진다 (2026-11-17)
        from game.scenes.field_scene import FieldScene
        from game.world.grid import Grid
        from game.world.tile_map import TileMap
        from game.input.input_state import Action, InputState
        from game.combat.enemy_attack import EnemyAttack
        from game.player.player import parry_spark_point
        from tests.test_golem import ROOM

        tile_map = TileMap.from_text(ROOM)
        scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        player, golem = scene.player, scene.golems[0]
        inp = InputState()
        inp.press(Action.PARRY)
        scene.update(1 / 60, inp)
        inp.begin_frame()
        inp.release(Action.PARRY)
        hit = EnemyAttack(frozenset({(player.col, player.row)}), 10, parryable=True)

        def fake_update(dt, player_tile, can_place):
            golem.attacks = [hit]
            golem.effects = []

        golem.update = fake_update
        scene.update(1 / 60, inp)
        sparks = [e for e in scene.effects if e.spec is config.PARRY_SPARK_EFFECT]
        self.assertEqual(len(sparks), 1)
        self.assertEqual((sparks[0].x, sparks[0].y), parry_spark_point(player.col, player.row, player.facing))
        self.assertEqual(player.hp, player.max_hp)  # 막았으니 피해 없음

        class Rec:
            def __init__(self):
                self.calls = []

            def __getattr__(self, name):
                return lambda *a, **k: self.calls.append(name)

            def draw_sheet_frame(self, path, *args):
                self.calls.append(("effect", path))

            def draw_sprite_frame(self, path, *args, **kwargs):
                self.calls.append(("sprite", path))

        rec = Rec()
        scene.draw(rec)
        order = [c for c in rec.calls if isinstance(c, tuple)]
        spark_at = order.index(("effect", str(config.PARRY_SPARK_EFFECT["path"])))
        self.assertTrue(all(kind == "effect" or i < spark_at for i, (kind, _) in enumerate(order)
                            if kind == "sprite"))  # 인물 그림보다 나중에

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


class StunStarsTest(unittest.TestCase):
    """기절 공용 이펙트 (2026-11-18): 반복 재생, 기절한 골렘 머리 위에 그림."""

    def test_loop_frame_wraps(self):
        from game.effects.effect import loop_frame
        spec = config.STUN_STARS_EFFECT
        self.assertEqual(loop_frame(spec, 0.0), 0)
        self.assertEqual(loop_frame(spec, spec["frames"] / spec["fps"]), 0)  # 한 바퀴 돌면 처음으로
        self.assertEqual(loop_frame(spec, 1.5 / spec["fps"]), 1)

    def test_sheet_matches_spec(self):
        from PIL import Image
        spec = config.STUN_STARS_EFFECT
        w, h = spec["frame_size"]
        with Image.open(spec["path"]) as im:
            self.assertEqual(im.size, (w * spec["frames"], h))

    def test_stunned_golem_draws_stars(self):
        from game.world.grid import Grid

        class Rec:
            def __init__(self):
                self.paths = []

            def draw_sheet_frame(self, path, *args):
                self.paths.append(path)
                return True

            def draw_sprite_frame(self, *args, **kwargs):
                return True

            def __getattr__(self, name):
                return lambda *a, **k: None

        golem = Golem(6, 4, open_room())
        for _ in range(4):
            golem.on_parried()
        golem.update(0.3, (1, 1), lambda c, r: True)
        rec = Rec()
        golem.draw(rec, Grid(16, 10, 64))
        self.assertIn(str(config.STUN_STARS_EFFECT["path"]), rec.paths)
        golem.update(config.POSTURE_STUN_TIME, (1, 1), lambda c, r: True)  # 기절이 풀리면 별 없음
        rec = Rec()
        golem.draw(rec, Grid(16, 10, 64))
        self.assertNotIn(str(config.STUN_STARS_EFFECT["path"]), rec.paths)


class GolemStunAnimTest(unittest.TestCase):
    """골렘 기절 동작 그림 (2026-11-18): 휘청 → 무릎 → 무릎 유지 → 풀리기 직전 일어섬."""

    def stunned(self):
        golem = Golem(6, 4, open_room())
        for _ in range(4):
            golem.on_parried()
        return golem

    def test_frames_follow_enter_kneel_exit(self):
        anim = config.GOLEM_STUN_ANIM
        golem = self.stunned()
        step = lambda t: golem.update(t, (1, 1), lambda c, r: True)
        self.assertEqual(golem.stun_frame, anim["enter_frames"][0])
        step(anim["enter_time"] * 0.5)
        self.assertIn(golem.stun_frame, anim["enter_frames"][1:-1])
        step(anim["enter_time"])  # 들어가기 끝 → 무릎 유지
        self.assertEqual(golem.stun_frame, anim["kneel_frame"])
        step(golem.posture.stun_left - anim["exit_time"] - 0.05)
        self.assertEqual(golem.stun_frame, anim["kneel_frame"])  # 풀리기 exit_time 전까지 무릎
        step(golem.posture.stun_left - anim["exit_time"] * 0.1)  # 풀리기 직전: 일어섬
        self.assertIn(golem.stun_frame, anim["exit_frames"][1:])
        step(anim["exit_time"])
        self.assertIsNone(golem.stun_frame)  # 풀리면 서 있는 그림

    def test_draws_stun_sheet(self):
        from game.world.grid import Grid

        class Rec:
            def __init__(self):
                self.paths = []

            def draw_sprite_frame(self, path, *args, **kwargs):
                self.paths.append(path)
                return True

            def __getattr__(self, name):
                return lambda *a, **k: None

        golem = self.stunned()
        golem.update(1.0, (1, 1), lambda c, r: True)
        rec = Rec()
        golem.draw(rec, Grid(16, 10, 64))
        self.assertEqual(rec.paths[0], golem.attack_sprite_path("stun"))

    def test_sheets_match_spec(self):
        from PIL import Image
        anim = config.GOLEM_STUN_ANIM
        w, h = anim["frame_size"]
        count = len(anim["head_drop"])
        self.assertEqual(count, max(anim["exit_frames"]) + 1)
        for view in ("south", "east", "north", "west"):
            with Image.open(config.GOLEM_IMAGE_DIR / f"stun_{view}.png") as im:
                self.assertEqual(im.size, (w * count, h), view)
