"""전기 능력 테스트 (2026-11-20 사용자 결정: 전기 칼로 때리면 파란 게이지가 차고, E 로 번개를 끄면 게이지만큼 감전).
pico2d 없이."""
import random
import unittest

from game import config
from game.combat.charge import BLACK, NORMAL, WHITE, Charge, StaticField
from game.combat.training_dummy import TrainingDummy
from game.enemies.golem import REST, WINDUP, Golem
from game.input.input_state import Action, InputState
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid
from game.world.tile_map import TileMap

DT = 1 / 60


def burst(c: Charge) -> int:
    """방전 뒤 모임이 끝나 터질 때까지 시간을 흘린다. 터지는 순간의 피해(늘 0, 피해는 감전 동안 나눠서)를 돌려준다."""
    for _ in range(120):
        damage = c.update(DT)
        if c.just_burst:
            return damage
    raise AssertionError("터지지 않음")


def shock_total(c: Charge) -> int:
    """감전이 끝날 때까지 나눠 받은 피해의 합."""
    total = 0
    while c.shocked:
        total += c.update(DT)
    return total


class ChargeLogicTest(unittest.TestCase):
    def test_ten_hits_fill_and_full_discharge(self):
        c = Charge()
        for _ in range(12):
            c.add()
        self.assertAlmostEqual(c.value, 1.0)
        self.assertTrue(c.discharge())
        self.assertEqual(c.value, 0.0)
        self.assertTrue(c.gathering)  # 안의 전기가 모이는 중 (아직 피해 없음)
        self.assertEqual(burst(c), 0)  # 터지는 순간은 연출만
        self.assertAlmostEqual(c.shock_left, config.SHOCK_TIME_FULL, delta=DT)
        self.assertEqual(shock_total(c), config.SHOCK_DAMAGE_FULL)  # 감전 동안 나눠서 다 받음

    def test_shock_damage_drains_in_quick_ticks(self):
        # 한 번에 터지지 않고 빠르게 깎임 (2026-11-20 사용자)
        c = Charge()
        for _ in range(10):
            c.add()
        c.discharge()
        burst(c)
        ticks = []
        while c.shocked:
            d = c.update(DT)
            if d:
                ticks.append(d)
        self.assertGreaterEqual(len(ticks), 10)
        self.assertLessEqual(max(ticks), config.SHOCK_DAMAGE_FULL // 10)  # 한 번에 크게 깎이지 않음

    def test_discharge_scales_with_gauge(self):
        c = Charge()
        for _ in range(5):
            c.add()
        c.discharge()
        burst(c)
        self.assertAlmostEqual(c.shock_left, config.SHOCK_TIME_FULL * 0.5, delta=DT)
        self.assertEqual(shock_total(c), round(config.SHOCK_DAMAGE_FULL * 0.5))

    def test_empty_gauge_does_nothing(self):
        c = Charge()
        self.assertFalse(c.discharge())
        self.assertFalse(c.frozen)

    def test_gauge_does_not_decay(self):
        c = Charge()
        c.add()
        for _ in range(600):
            c.update(DT)
        self.assertAlmostEqual(c.value, config.CHARGE_PER_HIT)

    def test_shock_flickers_black_white(self):
        c = Charge()
        for _ in range(10):
            c.add()
        c.discharge()
        burst(c)
        looks = set()
        for _ in range(60):
            looks.add(c.shock_look)
            c.update(DT)
        self.assertEqual(looks, {BLACK, WHITE, NORMAL})

    def test_static_grows_with_gauge(self):
        weak, strong = StaticField((16, 40), random.Random(1)), StaticField((16, 40), random.Random(1))
        nw = ns = 0
        for _ in range(120):
            weak.update(DT, 0.1, False)
            strong.update(DT, 1.0, False)
            nw += len(weak.arcs)
            ns += len(strong.arcs)
        self.assertGreater(ns, nw * 2)
        empty = StaticField((16, 40))
        empty.update(1.0, 0.0, False)
        self.assertEqual(empty.pixels(), [])


class TargetShockTest(unittest.TestCase):
    def test_golem_shock_damages_freezes_and_cancels_windup(self):
        g = Golem(5, 5, lambda c, r: False)
        for _ in range(10):
            g.add_charge()
        g.state, g.pattern, g.state_left = WINDUP, "slam", 1.0
        hp = g.hp
        self.assertTrue(g.discharge())
        self.assertEqual(g.state, REST)  # 예고는 바로 끊김
        self.assertEqual(g.hp, hp)  # 모이는 동안은 아직 피해 없음
        spot = (g.col, g.row)
        bursts = 0
        for _ in range(round((config.SHOCK_GATHER_TIME + config.SHOCK_TIME_FULL) / DT) - 3):  # 모임·감전 동안 굳어 있음
            g.update(DT, (5, 9), lambda c, r: True)
            bursts += g.burst_now
            if g.hp < hp:
                self.assertEqual(g.popups[-1].color, config.COLOR_SHOCK_TEXT)
            self.assertEqual((g.col, g.row), spot)
            self.assertEqual(g.attacks, [])
        self.assertEqual(bursts, 1)
        for _ in range(10):
            g.update(DT, (5, 9), lambda c, r: True)
        self.assertEqual(g.hp, hp - config.SHOCK_DAMAGE_FULL)

    def test_dummy_shock(self):
        d = TrainingDummy(3, 3)
        d.add_charge()
        self.assertTrue(d.discharge())
        self.assertFalse(d.discharge())  # 게이지를 다 썼음
        for _ in range(round(config.SHOCK_GATHER_TIME / DT) + 2):
            d.update(DT)
        self.assertTrue(d.charge.shocked)
        for _ in range(round(config.SHOCK_TIME_FULL / DT)):
            d.update(DT)
        self.assertEqual(d.hp, d.max_hp - round(config.SHOCK_DAMAGE_FULL * config.CHARGE_PER_HIT))


ROOM = """
#######
#.....#
#P.D..#
#.....#
#######
"""


class LightningSwordTest(unittest.TestCase):
    def setUp(self):
        tile_map = TileMap.from_text(ROOM)
        self.scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        self.input = InputState()
        self.dummy = self.scene.dummies[0]

    def step(self):
        self.scene.update(DT, self.input)
        self.input.begin_frame()

    def tap(self, action):
        self.input.press(action)
        self.step()
        self.input.release(action)

    def run_for(self, seconds):
        for _ in range(round(seconds / DT)):
            self.step()

    def test_hits_charge_then_e_discharges_and_removes_lightning(self):
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(1.0)
        self.input.release(Action.MOVE_RIGHT)
        self.run_for(0.3)
        self.tap(Action.ELEMENT_2)
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.assertEqual(self.scene.player.enchant.active, "lightning")
        before = self.dummy.hp
        self.tap(Action.ATTACK)
        self.run_for(0.8)
        self.assertAlmostEqual(self.dummy.charge.value, config.CHARGE_PER_HIT)
        # 전기를 입힌 검은 평타가 절반
        self.assertEqual(before - self.dummy.hp,
                         round(config.PLAYER_ATTACK_DAMAGE[0] * config.CHARGE_STRIKE_DAMAGE_SCALE))
        hp = self.dummy.hp
        self.tap(Action.ENCHANT)  # 같은 속성으로 E: 번개를 끔 → 방전 (안의 전기가 모였다가 터짐)
        self.assertIsNone(self.scene.player.enchant.active)
        self.assertTrue(self.dummy.charge.gathering)
        self.assertEqual(self.dummy.charge.value, 0.0)
        self.run_for(config.SHOCK_GATHER_TIME + 0.05)
        self.assertTrue(self.dummy.charge.shocked)
        self.run_for(config.SHOCK_TIME_FULL)
        self.assertLess(self.dummy.hp, hp)


if __name__ == "__main__":
    unittest.main()
