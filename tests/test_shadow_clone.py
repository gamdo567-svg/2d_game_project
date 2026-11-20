"""어둠 능력 테스트 (2026-11-20 사용자 결정: 3타를 다 때리면 그림자 분신, 같이 평타, 피해 절반, 흩어지는 조건). pico2d 없이."""
import unittest

from game import config
from game.combat.strike import Strike
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.shadow_clone import ShadowClones
from tests.test_player import make_player

DT = 1 / 60


class ShadowCloneLogicTest(unittest.TestCase):
    def test_clone_attacks_with_half_damage_from_its_own_spot(self):
        c = ShadowClones()
        c.spawn(3, 3, Facing.LEFT)
        c.on_attack_start((1, 0), (6, 3))
        strike = Strike(6, 3, (1, 0), 1, 10, 3)
        [s] = c.strikes((1, 0), strike)
        self.assertEqual((s.col, s.row), (3, 3))
        self.assertEqual(s.direction, Facing.LEFT.value)  # 자기 방향
        self.assertEqual(s.damage, 5)  # 절반
        self.assertEqual((s.reach, s.width), (1, 3))  # 같은 타 범위

    def test_attacking_on_clone_tile_scatters_it(self):
        c = ShadowClones()
        c.spawn(3, 3, Facing.LEFT)
        c.on_attack_start((1, 0), (3, 3))
        self.assertEqual(c.clones, [])
        self.assertTrue(c.puffs)  # 검은 연기로 흩어짐

    def test_idle_five_seconds_scatters(self):
        c = ShadowClones()
        c.spawn(3, 3, Facing.LEFT)
        for _ in range(round((config.SHADOW_CLONE_IDLE - 0.2) / DT)):
            c.update(DT, (4, 3), True)
        self.assertEqual(len(c.clones), 1)
        c.on_attack_start((1, 0), (4, 3))  # 같이 치면 다시 5초
        for _ in range(round((config.SHADOW_CLONE_IDLE - 0.2) / DT)):
            c.update(DT, (4, 3), True)
        self.assertEqual(len(c.clones), 1)
        for _ in range(30):
            c.update(DT, (4, 3), True)
        self.assertEqual(c.clones, [])

    def test_too_far_scatters(self):
        c = ShadowClones()
        c.spawn(3, 3, Facing.LEFT)
        c.update(DT, (3 + config.SHADOW_CLONE_RANGE, 3), True)
        self.assertEqual(len(c.clones), 1)
        c.update(DT, (3 + config.SHADOW_CLONE_RANGE + 1, 3), True)
        self.assertEqual(c.clones, [])

    def test_losing_dark_scatters(self):
        c = ShadowClones()
        c.spawn(3, 3, Facing.LEFT)
        c.spawn(5, 3, Facing.LEFT)
        c.update(DT, (5, 4), False)  # 검의 어둠이 풀림
        self.assertEqual(c.clones, [])

    def test_at_most_three_oldest_scatters(self):
        c = ShadowClones()
        for col in range(4):
            c.spawn(col, 0, Facing.DOWN)
        self.assertEqual([k.col for k in c.clones], [1, 2, 3])


class PlayerShadowCloneTest(unittest.TestCase):
    def setUp(self):
        self.player = make_player()
        self.input = InputState()

    def tap(self, action):
        self.input.begin_frame()
        self.input.press(action)
        self.player.update(DT, self.input)
        self.input.begin_frame()
        self.input.release(action)

    def run_for(self, seconds, holding=None):
        strikes = []
        for _ in range(round(seconds / DT)):
            self.input.begin_frame()
            self.player.update(DT, self.input)
            strikes += self.player.strikes
        return strikes

    def enchant_dark(self):
        self.tap(Action.ELEMENT_3)
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.assertEqual(self.player.enchant.active, "dark")

    def combo(self):
        self.input.begin_frame()
        self.input.press(Action.ATTACK)
        strikes = self.run_for(2.3)
        self.input.release(Action.ATTACK)
        strikes += self.run_for(0.2)
        return strikes

    def test_third_hit_leaves_clone_then_clone_attacks_along(self):
        self.enchant_dark()
        self.combo()
        self.assertEqual(len(self.player.clones.clones), 1)
        clone = self.player.clones.clones[0]
        self.assertEqual((clone.col, clone.row), (self.player.col, self.player.row))
        # 옆 칸으로 옮겨 치면 분신도 같이 침 (피해 절반)
        self.input.begin_frame()
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(0.3)
        self.input.release(Action.MOVE_RIGHT)
        self.run_for(1.2)  # 쿨타임이 끝나도록
        self.tap(Action.ATTACK)
        strikes = self.run_for(0.8)
        mine = [s for s in strikes if (s.col, s.row) == (self.player.col, self.player.row)]
        theirs = [s for s in strikes if (s.col, s.row) == (clone.col, clone.row)]
        self.assertEqual(len(mine), 1)
        self.assertEqual(len(theirs), 1)
        self.assertEqual(theirs[0].damage, round(mine[0].damage * config.SHADOW_CLONE_DAMAGE_SCALE))

    def test_player_hit_scatters_all_clones_but_clones_are_never_hit(self):
        # 맞으면 사라지는 건 본체, 그림자는 맞지 않음 (2026-11-20 사용자)
        from game.combat.enemy_attack import EnemyAttack
        self.player.clones.spawn(1, 1, Facing.DOWN)
        self.player.clones.spawn(2, 1, Facing.DOWN)
        self.player.receive_attack(EnemyAttack(frozenset({(1, 1), (2, 1)}), 10))  # 분신 칸만 덮는 공격
        self.assertEqual(len(self.player.clones.clones), 2)
        tile = (self.player.col, self.player.row)
        self.player.receive_attack(EnemyAttack(frozenset({tile}), 10))  # 본체가 맞음
        self.assertEqual(self.player.clones.clones, [])

    def test_no_clone_without_dark(self):
        self.combo()
        self.assertEqual(self.player.clones.clones, [])


if __name__ == "__main__":
    unittest.main()
