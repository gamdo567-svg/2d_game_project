"""불 붙음 테스트 (2026-11-20 사용자 결정: 불로 때리면 불이 붙어 체력이 서서히 깎이고, 많이 때릴수록 오래 타며,
회피할 수 있는 캐릭터는 회피하면 꺼진다). pico2d 없이."""
import unittest

from game import config
from game.combat.burn import Burn, BurnFlames
from game.combat.training_dummy import TrainingDummy
from game.enemies.golem import Golem
from game.input.input_state import Action, InputState
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid
from game.world.tile_map import TileMap
from tests.test_player import make_player

DT = 1 / 60


def run(burn: Burn, seconds: float) -> int:
    return sum(burn.update(DT) for _ in range(round(seconds / DT)))


class BurnLogicTest(unittest.TestCase):
    def test_one_hit_burns_for_two_seconds(self):
        b = Burn()
        b.ignite()
        self.assertTrue(b.burning)
        self.assertAlmostEqual(b.time_left, config.BURN_SECONDS_PER_HIT)
        total = run(b, config.BURN_SECONDS_PER_HIT + 0.5)
        self.assertEqual(total, round(config.BURN_DAMAGE_PER_SECOND * config.BURN_SECONDS_PER_HIT))
        self.assertFalse(b.burning)

    def test_more_hits_burn_longer_up_to_max(self):
        b = Burn()
        for _ in range(3):
            b.ignite()
        self.assertAlmostEqual(b.time_left, 3 * config.BURN_SECONDS_PER_HIT)
        for _ in range(10):
            b.ignite()
        self.assertAlmostEqual(b.time_left, config.BURN_MAX_SECONDS)
        total = run(b, config.BURN_MAX_SECONDS + 1)
        self.assertEqual(total, round(config.BURN_DAMAGE_PER_SECOND * config.BURN_MAX_SECONDS))

    def test_extinguish(self):
        b = Burn()
        b.ignite()
        b.extinguish()
        self.assertFalse(b.burning)
        self.assertEqual(run(b, 3.0), 0)

    def test_flames_only_while_burning(self):
        f = BurnFlames(14, 34)
        f.update(0.5, burning=False)
        self.assertEqual(f.pixels(), [])
        f.update(0.5, burning=True)
        self.assertTrue(f.pixels())
        f.update(1.0, burning=False)  # 꺼지면 남은 불꽃도 곧 사라짐
        self.assertEqual(f.pixels(), [])


class TargetBurnTest(unittest.TestCase):
    def test_golem_loses_hp_while_burning_and_fire_stops_on_death(self):
        g = Golem(5, 5, lambda c, r: False, dormant=True)
        g.ignite()
        hp = g.hp
        for _ in range(round(1.05 / DT)):
            g.update(DT, (0, 0), lambda c, r: True)
        self.assertEqual(g.hp, hp - config.BURN_DAMAGE_PER_SECOND)
        self.assertEqual(g.popups[-1].color, config.COLOR_BURN_TEXT)
        g.take_hit(g.hp, (1, 0))
        self.assertFalse(g.burn.burning)

    def test_dummy_burns(self):
        d = TrainingDummy(3, 3)
        d.take_hit(1, (1, 0))
        d.ignite()
        for _ in range(round(2.05 / DT)):
            d.update(DT)
        self.assertEqual(d.hp, d.max_hp - 1 - 2 * config.BURN_DAMAGE_PER_SECOND)


class PlayerBurnTest(unittest.TestCase):
    def test_dodge_puts_fire_out(self):
        player = make_player()
        player.burn.ignite()
        state = InputState()
        state.press(Action.DODGE)
        player.update(DT, state)
        self.assertFalse(player.burn.burning)

    def test_burn_hurts_player_without_stagger(self):
        player = make_player()
        player.burn.ignite()
        state = InputState()
        for _ in range(round(1.05 / DT)):
            state.begin_frame()
            player.update(DT, state)
        self.assertEqual(player.hp, player.max_hp - config.BURN_DAMAGE_PER_SECOND)
        self.assertEqual(player.state, "idle")


ROOM = """
#######
#.....#
#P.D..#
#.....#
#######
"""


class FireStrikeTest(unittest.TestCase):
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

    def walk_next_to_dummy(self):
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(1.0)
        self.input.release(Action.MOVE_RIGHT)
        self.run_for(0.3)

    def test_plain_sword_does_not_ignite(self):
        self.walk_next_to_dummy()
        self.tap(Action.ATTACK)
        self.run_for(0.8)
        self.assertLess(self.dummy.hp, self.dummy.max_hp)
        self.assertFalse(self.dummy.burn.burning)

    def test_fire_sword_ignites(self):
        self.walk_next_to_dummy()
        self.tap(Action.ELEMENT_1)
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.assertEqual(self.scene.player.enchant.active, "fire")
        self.tap(Action.ATTACK)
        self.run_for(0.8)
        self.assertTrue(self.dummy.burn.burning)


if __name__ == "__main__":
    unittest.main()
