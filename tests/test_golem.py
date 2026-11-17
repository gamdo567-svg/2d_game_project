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


class GolemAreaTest(unittest.TestCase):
    def setUp(self):
        self.golem = Golem(6, 4, open_room())

    def test_occupies_two_by_two(self):
        self.assertEqual(self.golem.tiles, {(6, 4), (7, 4), (6, 5), (7, 5)})
        self.assertEqual(self.golem.distance_to((5, 4)), 1)
        self.assertEqual(self.golem.distance_to((2, 5)), 4)

    def test_front_area_toward_player(self):
        self.golem.facing = (-1, 0)
        area = self.golem.front_area(3, 3, (5, 3))  # 주인공이 아래쪽 줄에 있으면 아래로 넓힘
        self.assertEqual(area, {(c, r) for c in (3, 4, 5) for r in (3, 4, 5)})
        self.golem.facing = (0, 1)
        area = self.golem.front_area(3, 5, (8, 7))
        self.assertEqual(area, {(c, r) for c in (6, 7, 8) for r in (6, 7, 8)})  # 위쪽 벽(9)에서 멈춤

    def test_stomp_area_six_by_six(self):
        self.assertEqual(self.golem.stomp_area(), {(c, r) for c in range(4, 10) for r in range(2, 8)})

    def test_laser_line_until_wall(self):
        self.golem.aim = (2.5, 5.0)  # 몸 가운데 (7, 5) 에서 왼쪽으로
        self.assertEqual(self.golem.laser_tiles(), {(c, 5) for c in range(1, 6)})


class GolemBehaviorTest(unittest.TestCase):
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

    def test_mid_kick_and_far_laser(self):
        self.make(None, roll=0.0)
        self.advance(DT, (2, 4))  # 거리 4: 차기
        self.assertEqual(self.golem.pattern, KICK)
        self.make(None, roll=0.0)
        self.advance(DT, (14, 8))  # 멀다: 레이저
        self.assertEqual(self.golem.pattern, LASER)

    def test_approaches_until_near(self):
        # 주인공이 멀리 있으면 레이저를 한 번 쏜 뒤에는 쿨타임 동안 걸어서 다가와 가까운 패턴을 쓴다
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
