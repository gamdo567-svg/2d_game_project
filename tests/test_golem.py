"""골렘 테스트 (pico2d 없이): 패턴 범위, 예고 → 터짐, 패링·회피 무적·점프, 패링 게이지·기절, 맞기·죽음·다시 나타나기."""
import unittest

from game import config
from game.combat.enemy_attack import AVOIDED, HIT, MISSED, PARRIED
from game.combat.posture import PostureGauge
from game.enemies.golem import DEAD, KICK, LASER, RECOVER, SLAM, STOMP, STUNNED, WALK, WINDUP, Golem
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.state_machine import ATTACK, HURT, JUMP, PARRY
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid
from game.world.tile_map import TileMap

DT = 1 / 120


class FixedRng:
    """패턴 고르기를 정해 두는 가짜 난수."""

    def __init__(self, pick=None, roll=0.0):
        self.pick = pick
        self.roll = roll

    def choice(self, items):
        return self.pick if self.pick in items else items[0]

    def random(self):
        return self.roll


def open_room(cols=16, rows=10):
    return lambda c, r: not (0 < c < cols - 1 and 0 < r < rows - 1)


class PostureGaugeTest(unittest.TestCase):
    def test_fills_stuns_and_decays(self):
        g = PostureGauge()
        for _ in range(3):
            self.assertFalse(g.add_parried())
        self.assertAlmostEqual(g.value, 0.75)
        g.relieve_by_parry()
        self.assertAlmostEqual(g.value, 0.25)
        g.update(1.0)
        self.assertAlmostEqual(g.value, 0.25 - config.POSTURE_DECAY_PER_SECOND)
        g.value = 0.75
        self.assertTrue(g.add_parried())
        self.assertTrue(g.is_stunned)
        g.update(config.POSTURE_STUN_TIME + 0.01)
        self.assertFalse(g.is_stunned)
        self.assertEqual(g.value, 0.0)


    def test_monster_type_gauge_does_not_decay(self):
        g = PostureGauge(decays=False)
        g.add_parried()
        g.update(30.0)
        self.assertAlmostEqual(g.value, config.POSTURE_PARRIED_GAIN)
        self.assertFalse(Golem(6, 4, open_room()).posture.decays)


class GolemAreaTest(unittest.TestCase):
    def setUp(self):
        self.golem = Golem(6, 4, open_room())

    def test_occupies_one_by_two(self):
        # 몸 1×2: 발 칸과 그 위 한 칸 (2026-11-17 사용자 요청: 3×3 은 너무 큼)
        self.assertEqual(self.golem.tiles, {(6, 4), (6, 5)})
        self.assertEqual(self.golem.distance_to((5, 4)), 1)
        self.assertEqual(self.golem.distance_to((2, 5)), 4)

    def test_front_area_toward_player(self):
        self.golem.facing = (-1, 0)
        # 기준은 발 칸 (몸 1×2 의 아래 칸 = (6, 4)), 그 칸 바로 앞부터 (2026-11-17 사용자 결정)
        self.assertEqual(self.golem.feet_tile, (6, 4))
        # 가로 3 은 발 칸을 가운데로 대칭 (주인공 위치와 상관없음)
        for player in ((5, 3), (5, 5), (5, 8)):
            self.assertEqual(self.golem.front_area(3, 3, player), {(c, r) for c in (3, 4, 5) for r in (3, 4, 5)})
        self.golem.facing = (0, 1)
        area = self.golem.front_area(3, 5, (8, 8))
        self.assertEqual(area, {(c, r) for c in (5, 6, 7) for r in range(5, 9)})  # 위쪽 벽(9)에서 멈춤
        self.golem.facing = (0, -1)
        self.assertEqual(self.golem.front_area(3, 3, (6, 1)), {(c, r) for c in (5, 6, 7) for r in (1, 2, 3)})
        # 가로 4: 남는 한 줄은 아래, 주인공이 발 칸보다 위에 있을 때만 위
        self.golem.facing = (-1, 0)
        self.assertEqual(self.golem.front_area(4, 5, (2, 3)), {(c, r) for c in range(1, 6) for r in range(2, 6)})
        self.assertEqual(self.golem.front_area(4, 5, (2, 8)), {(c, r) for c in range(1, 6) for r in range(3, 7)})

    def test_stomp_area_seven_by_seven(self):
        # 7×7: 발 칸 (6, 4) 둘레로 3칸씩, 주인공 위치와 상관없이 대칭 (2026-11-17 사용자 요청)
        area = {(c, r) for c in range(3, 10) for r in range(1, 8)}
        self.assertEqual(self.golem.stomp_area((1, 1)), area)
        self.assertEqual(self.golem.stomp_area((12, 8)), area)

    def test_laser_explodes_four_by_four_at_aim(self):
        self.golem.aim = (3.0, 5.0)  # 조준점을 가운데로 한 4×4
        self.assertEqual(self.golem.laser_tiles(), {(c, r) for c in range(1, 5) for r in range(3, 7)})

    def test_laser_excludes_wall_tiles(self):
        self.golem.aim = (1.0, 5.0)  # 왼쪽 벽(0열)에 걸침 → 벽 칸 빼고 터짐
        self.assertEqual(self.golem.laser_tiles(), {(c, r) for c in range(1, 3) for r in range(3, 7)})


class WarningColorTest(unittest.TestCase):
    def test_color_by_attack_kind(self):
        from game.enemies.golem import warning_kind
        self.assertEqual(warning_kind(SLAM), "parryable")  # 빨강
        self.assertEqual(warning_kind(KICK), "unparryable")  # 노랑
        self.assertEqual(warning_kind(LASER), "unparryable")
        self.assertEqual(warning_kind(STOMP), "jump_only")  # 하늘색

    def test_warning_tiles_drawn_in_kind_color_getting_stronger(self):
        golem = Golem(6, 4, open_room(), FixedRng(STOMP))
        golem._windup(STOMP, (5, 4))
        calls = []

        class Rec:
            def fill_tile(self, grid, col, row, color, inset=0):
                calls.append(color)

        golem.draw_warning(Rec(), Grid(16, 10, 64))
        faint, strong = config.COLOR_WARN["jump_only"]
        self.assertEqual(set(calls), {faint})
        golem.state_left = 0.0001  # 터지기 직전
        calls.clear()
        golem.draw_warning(Rec(), Grid(16, 10, 64))
        self.assertEqual(set(calls), {strong})


class GolemBehaviorTest(unittest.TestCase):
    def enable_laser(self):
        # 레이저는 지금 빠져 있어(GOLEM_LASER_ENABLED) 레이저 시험에서만 켠다
        original = config.GOLEM_LASER_ENABLED
        config.GOLEM_LASER_ENABLED = True
        self.addCleanup(setattr, config, "GOLEM_LASER_ENABLED", original)

    def make(self, pick, roll=0.0):
        self.golem = Golem(6, 4, open_room(), FixedRng(pick, roll))
        self.golem.state_left = 0.0  # 쉬지 않고 바로 판단

    def advance(self, seconds, player_tile, can_place=lambda c, r: True):
        attacks = []
        for _ in range(round(seconds / DT)):
            self.golem.update(DT, player_tile, can_place)
            attacks += self.golem.attacks
        return attacks

    def test_near_slam_windup_then_release(self):
        self.make(SLAM)
        self.advance(DT, (5, 4))
        self.assertEqual((self.golem.state, self.golem.pattern), (WINDUP, SLAM))
        self.assertIn((5, 4), self.golem.target_tiles)
        attacks = self.advance(config.GOLEM_SLAM["windup"] + DT, (5, 4))
        self.assertEqual(len(attacks), 1)
        self.assertTrue(attacks[0].parryable)
        self.assertEqual(attacks[0].damage, config.GOLEM_SLAM["damage"])
        self.assertEqual(self.golem.state, RECOVER)

    def test_near_uses_all_three_close_patterns(self):
        seen = set()
        for pick in (SLAM, KICK, STOMP):
            self.make(pick)
            self.advance(DT, (5, 4))
            seen.add(self.golem.pattern)
        self.assertEqual(seen, {SLAM, KICK, STOMP})

    def test_laser_disabled_for_now(self):
        # 2026-11-17 사용자 요청: 시험을 위해 레이저를 잠시 뺌. 멀어도 레이저 대신 다가간다
        self.assertFalse(config.GOLEM_LASER_ENABLED)
        self.make(None, roll=0.0)
        self.advance(DT, (14, 8))
        self.assertNotEqual(self.golem.pattern, LASER)
        self.assertEqual(self.golem.state, WALK)

    def test_mid_kick_and_far_laser(self):
        self.enable_laser()
        self.make(None, roll=0.0)
        self.advance(DT, (2, 4))  # 거리 4: 차기
        self.assertEqual(self.golem.pattern, KICK)
        self.make(None, roll=0.0)
        self.advance(DT, (14, 8))  # 멀다: 레이저
        self.assertEqual(self.golem.pattern, LASER)

    def test_approaches_until_near(self):
        # 주인공이 멀리 있으면 레이저를 한 번 쏜 뒤에는 쿨타임 동안 걸어서 다가와 가까운 패턴을 쓴다
        self.enable_laser()
        self.make(SLAM, roll=0.0)
        self.advance(DT, (14, 4))
        self.assertEqual(self.golem.pattern, LASER)
        self.advance(config.GOLEM_LASER["windup"] + config.GOLEM_RECOVER_TIME + config.GOLEM_REST_TIME + 0.05, (14, 4))
        self.assertNotEqual(self.golem.pattern, LASER)  # 쿨타임: 다시 레이저를 쏘지 않고 걷는다
        self.advance(6.0, (14, 4))
        self.assertLessEqual(self.golem.distance_to((14, 4)), config.GOLEM_MID)

    def test_far_walks_toward_player(self):
        self.make(None, roll=0.9)
        self.advance(DT, (14, 4))  # 거리 7: 멀다, 레이저 대신 다가감
        self.assertEqual(self.golem.state, WALK)
        self.assertEqual((self.golem.col, self.golem.row), (7, 4))

    def test_laser_aim_follows_player_until_fire(self):
        self.enable_laser()
        self.make(None, roll=0.0)
        self.advance(DT, (14, 8))
        self.advance(0.5, (14, 1))
        self.assertEqual(self.golem.aim, (14.5, 1.5))  # 주인공 칸 가운데를 그대로 따라옴
        attacks = self.advance(config.GOLEM_LASER["windup"], (14, 1))
        self.assertEqual(len(attacks), 1)
        self.assertTrue(attacks[0].tiles)
        self.assertTrue(attacks[0].dodgeable and not attacks[0].parryable)

    def test_monster_type_no_stagger_but_stuns_when_gauge_full(self):
        self.make(SLAM)
        self.advance(DT, (5, 4))
        self.golem.take_hit(10, (1, 0))
        self.assertEqual(self.golem.state, WINDUP)  # 맞아도 경직 없음
        for _ in range(3):
            self.golem.on_parried()
        self.assertEqual(self.golem.state, WINDUP)  # 패링당해도 경직 없음
        self.golem.on_parried()  # 100%
        self.assertEqual(self.golem.state, STUNNED)
        self.assertEqual(self.advance(config.POSTURE_STUN_TIME - 0.1, (5, 4)), [])
        self.advance(0.2, (5, 4))
        self.assertNotEqual(self.golem.state, STUNNED)

    def test_dies_and_respawns(self):
        self.make(SLAM)
        self.golem.take_hit(config.GOLEM_MAX_HP, (1, 0))
        self.assertEqual(self.golem.state, DEAD)
        self.assertEqual(self.golem.tiles, frozenset())
        self.advance(config.GOLEM_RESPAWN_TIME + 0.05, (1, 1))
        self.assertTrue(self.golem.alive)
        self.assertEqual(self.golem.hp, config.GOLEM_MAX_HP)


ROOM = """
################
#..............#
#..............#
#..............#
#..............#
#....P.G.......#
#..............#
#..............#
################
"""


class GolemVsPlayerTest(unittest.TestCase):
    """장면에서: 주인공 (5,3), 골렘 (7,3)~(8,4). 주인공은 골렘 바로 왼쪽 옆 칸 (거리 2)."""

    def setUp(self):
        tile_map = TileMap.from_text(ROOM)
        self.scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        self.player = self.scene.player
        self.golem = self.scene.golems[0]
        self.input = InputState()

    def step(self):
        self.scene.update(DT, self.input)
        self.input.begin_frame()

    def run_for(self, seconds):
        for _ in range(round(seconds / DT)):
            self.step()

    def tap(self, action):
        self.input.press(action)
        self.step()
        self.input.release(action)

    def start_pattern(self, pattern):
        """골렘이 지금 바로 이 패턴의 예고를 시작하게 한다 (거리로 고르는 것은 GolemBehaviorTest 에서 확인)."""
        self.golem._windup(pattern, (self.player.col, self.player.row))
        self.assertEqual(self.golem.pattern, pattern)

    def run_until_release(self, before=0.0):
        """터지기 before 초 전까지 진행."""
        self.run_for(self.golem.state_left - before - DT)

    def test_golem_blocks_player(self):
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(1.0)
        self.assertEqual((self.player.col, self.player.row), (6, 3))

    def test_slam_hits_and_staggers(self):
        self.start_pattern(SLAM)
        self.run_until_release(0.0)
        self.run_for(0.05)
        self.assertEqual(self.player.hp, config.PLAYER_MAX_HP - config.GOLEM_SLAM["damage"])
        self.assertEqual(self.player.state, HURT)
        self.run_for(config.PLAYER_HURT_TIME + 0.05)
        self.assertNotEqual(self.player.state, HURT)

    def test_parry_slam_then_priority_attack(self):
        self.start_pattern(SLAM)
        self.run_until_release(0.05)
        self.tap(Action.PARRY)
        self.run_for(0.06)
        self.assertEqual(self.player.hp, config.PLAYER_MAX_HP)  # 피해 무효
        self.assertAlmostEqual(self.golem.posture.value, config.POSTURE_PARRIED_GAIN, places=2)
        self.assertEqual(self.player.state, PARRY)
        self.assertTrue(self.player.parry_succeeded)
        self.tap(Action.ATTACK)  # 우선권: 패링 동작 중에도 바로 공격
        self.assertEqual(self.player.state, ATTACK)

    def test_kick_cannot_be_parried_but_dodge_avoids(self):
        self.start_pattern(KICK)
        self.run_until_release(0.05)
        self.tap(Action.PARRY)
        self.run_for(0.06)
        self.assertLess(self.player.hp, config.PLAYER_MAX_HP)  # 패링 불가
        self.run_for(config.PLAYER_HURT_TIME + 0.05)
        hp = self.player.hp
        self.player.facing = Facing.LEFT
        self.start_pattern(KICK)
        self.run_until_release(0.02)
        self.player.dodge_cooldown_left = 0.0
        self.tap(Action.DODGE)  # 왼쪽으로 3칸 (2,3): 아직 차기 범위 안이지만 회피 중 무적이라 피함
        self.assertIn((self.player.col, self.player.row), self.golem.target_tiles)
        self.run_for(0.05)
        self.assertEqual(self.player.hp, hp)

    def test_stomp_only_avoided_by_jump(self):
        self.start_pattern(STOMP)
        self.run_until_release(config.PLAYER_JUMP_DURATION / 2)
        self.tap(Action.JUMP)
        self.assertEqual(self.player.state, JUMP)
        self.run_for(config.PLAYER_JUMP_DURATION / 2)
        self.assertEqual(self.player.hp, config.PLAYER_MAX_HP)  # 공중이라 피함

    def test_laser_follows_walking_player_but_dodge_avoids(self):
        self.start_pattern(LASER)
        self.input.press(Action.MOVE_UP)  # 걸어서 도망쳐도 조준선이 따라옴
        self.run_until_release(0.0)
        self.input.release(Action.MOVE_UP)
        self.run_for(0.05)
        self.assertEqual(self.player.hp, config.PLAYER_MAX_HP - config.GOLEM_LASER["damage"])
        self.run_for(config.PLAYER_HURT_TIME + 0.1)
        hp = self.player.hp
        self.player.facing = Facing.LEFT
        self.start_pattern(LASER)
        self.run_until_release(0.05)
        self.player.dodge_cooldown_left = 0.0
        self.tap(Action.DODGE)  # 발사 직전 회피: 무적
        self.run_for(0.1)
        self.assertEqual(self.player.hp, hp)

    def dodge_before_release(self, pattern, seconds_before):
        self.player.facing = Facing.LEFT
        self.player.dodge_cooldown_left = 0.0
        self.start_pattern(pattern)
        self.run_until_release(seconds_before)
        self.tap(Action.DODGE)
        self.run_for(seconds_before + 0.4)

    def test_perfect_dodge_resets_cooldown(self):
        self.dodge_before_release(KICK, 0.2)  # 노란색 공격이 터지기 0.2초 전, 범위 안에서 회피
        self.assertEqual(self.player.hp, config.PLAYER_MAX_HP)
        self.assertEqual(self.player.dodge_cooldown_left, 0.0)  # 대기 시간 없음
        self.assertGreater(self.player.perfect_text_left, 0.0)
        self.tap(Action.DODGE)  # 바로 다시 회피 가능
        self.assertEqual(self.player.state, "dodge")

    def test_early_dodge_is_not_perfect(self):
        self.dodge_before_release(KICK, config.PLAYER_PERFECT_DODGE_WINDOW + 0.1)
        self.assertGreater(self.player.dodge_cooldown_left, 0.0)

    def test_dodging_red_attack_is_not_perfect(self):
        self.dodge_before_release(SLAM, 0.2)  # 빨간(패링 가능) 공격: 피해도 퍼펙트 아님
        self.assertGreater(self.player.dodge_cooldown_left, 0.0)

    def test_receive_attack_results(self):
        from game.combat.enemy_attack import EnemyAttack
        here = frozenset({(self.player.col, self.player.row)})
        self.assertEqual(self.player.receive_attack(EnemyAttack(frozenset({(0, 0)}), 10)), MISSED)
        self.assertEqual(self.player.receive_attack(EnemyAttack(here, 10, dodgeable=False)), HIT)
        self.player.hp = 5
        self.player.receive_attack(EnemyAttack(here, 10))
        self.assertEqual(self.player.hp, config.PLAYER_MAX_HP)  # 0 이 되면 다시 채움 (사망 미정)

    def test_player_strike_hits_golem(self):
        self.golem.state_left = 99  # 쉬게 둠
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(0.4)
        self.input.release(Action.MOVE_RIGHT)  # (6,3) 오른쪽 보기, 골렘 바로 앞
        self.tap(Action.ATTACK)
        self.run_for(0.5)
        self.assertEqual(self.golem.hp, config.GOLEM_MAX_HP - config.PLAYER_ATTACK_DAMAGE[0])


if __name__ == "__main__":
    unittest.main()


class GolemSpriteTest(unittest.TestCase):
    """골렘 그림: 방향별 그림을 발 밑이 2×2칸 바닥 가운데에 오게 2배로 그리고, 못 읽으면 임시 도형."""

    class Rec:
        def __init__(self, sprite_ok):
            self.sprite_ok = sprite_ok
            self.calls = []

        def draw_sprite_frame(self, *args, **kwargs):
            self.calls.append(("draw_sprite_frame", args))
            return self.sprite_ok

        def __getattr__(self, name):
            return lambda *a, **k: self.calls.append((name, a))

    def setUp(self):
        self.golem = Golem(6, 4, open_room())
        self.grid = Grid(16, 10, config.RENDER_TILE_SIZE)

    def test_view_follows_facing(self):
        for facing, view in (((0, -1), "south"), ((0, 1), "north"), ((1, 0), "east"), ((-1, 0), "west")):
            self.golem.facing = facing
            self.assertEqual(self.golem.view, view)
            self.assertTrue(self.golem.sprite_path().endswith(f"golem\{view}.png")
                            or self.golem.sprite_path().endswith(f"golem/{view}.png"))

    def test_sprite_feet_on_bottom_center_of_body(self):
        self.golem.facing = (0, -1)
        rec = self.Rec(True)
        self.golem.draw(rec, self.grid)
        name, args = rec.calls[0]
        self.assertEqual(name, "draw_sprite_frame")
        size, scale, tile = config.GOLEM_SPRITE_SIZE, config.RENDER_SCALE, config.RENDER_TILE_SIZE
        self.assertEqual(args[2:4], (size, size))
        self.assertEqual(args[6:8], (size * scale, size * scale))
        left, bottom, _, _ = self.grid.tile_to_pixel_rect(6, 4)
        self.assertAlmostEqual(args[4], left + tile * config.GOLEM_BODY[0] / 2)  # 발 칸 가로 가운데
        self.assertAlmostEqual(args[5], bottom - config.GOLEM_SPRITE_FOOT_MARGIN["south"] * scale)  # 발 밑 = 칸 바닥
        shapes = [c for c in rec.calls if c[0] == "fill_rect"]
        self.assertEqual(len(shapes), 4)  # 임시 도형 없이 체력·게이지 막대만

    def test_falls_back_to_shapes_without_image(self):
        rec = self.Rec(False)
        self.golem.draw(rec, self.grid)
        shapes = [c for c in rec.calls if c[0] == "fill_rect"]
        self.assertGreater(len(shapes), 4)  # 다리·몸통·팔·코어 + 막대

    def test_hit_blinks_sprite(self):
        rec = self.Rec(True)
        self.golem.flash_left = config.GOLEM_HIT_FLASH_TIME
        drawn = []
        for _ in range(6):
            rec.calls.clear()
            self.golem.draw(rec, self.grid)
            drawn.append(any(c[0] == "draw_sprite_frame" for c in rec.calls))
            self.golem.flash_left -= 0.016
        self.assertIn(True, drawn)
        self.assertIn(False, drawn)

    def test_sprite_files_match_config(self):
        from tests.test_player_assets import COLOR_TYPE_RGBA, read_png_header, read_rgba_pixels
        size = config.GOLEM_SPRITE_SIZE
        for view, margin in config.GOLEM_SPRITE_FOOT_MARGIN.items():
            path = str(config.GOLEM_IMAGE_DIR / f"{view}.png")
            with self.subTest(view=view):
                _, width, height, color_type = read_png_header(path)
                self.assertEqual((width, height, color_type), (size, size, COLOR_TYPE_RGBA))
                pixels = read_rgba_pixels(path)
                self.assertTrue(all(p[3] in (0, 255) for row in pixels for p in row))
                rows = [y for y in range(size) if any(p[3] for p in pixels[y])]
                self.assertEqual(size - 1 - rows[-1], margin)  # 발 밑 아래 투명 줄 수
                self.assertGreaterEqual(rows[0], config.GOLEM_SPRITE_HEAD_ROW - 1)
