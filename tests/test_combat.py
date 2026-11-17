"""공격 판정(Strike)과 연습용 허수아비 테스트 (pico2d 없이)."""
import unittest

from game import config
from game.combat.strike import Strike, attack_tiles
from game.combat.training_dummy import TrainingDummy
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.state_machine import ATTACK
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid
from game.world.tile_map import TileMap

DT = 1 / 120


class StrikeTest(unittest.TestCase):
    def test_reach_and_wall_stop(self):
        walls = {(5, 2)}
        is_wall = lambda c, r: (c, r) in walls
        self.assertEqual(attack_tiles(Strike(2, 2, (1, 0), 1, 10), is_wall), [(3, 2)])
        self.assertEqual(attack_tiles(Strike(2, 2, (1, 0), 2, 10), is_wall), [(3, 2), (4, 2)])
        # 벽 너머는 맞지 않는다
        self.assertEqual(attack_tiles(Strike(3, 2, (1, 0), 2, 10), is_wall), [(4, 2)])
        self.assertEqual(attack_tiles(Strike(2, 2, (0, 1), 2, 10), is_wall), [(2, 3), (2, 4)])

    def test_attack_tiles_width(self):
        # 가로 3칸: 바라보는 방향 앞 1칸과 그 양옆. 줄마다 벽이면 그 줄만 막힌다.
        is_wall = lambda c, r: (c, r) == (3, 3)
        self.assertEqual(sorted(attack_tiles(Strike(2, 2, (1, 0), 1, 10, width=3), is_wall)), [(3, 1), (3, 2)])
        self.assertEqual(sorted(attack_tiles(Strike(2, 2, (0, 1), 1, 10, width=3), lambda c, r: False)),
                         [(1, 3), (2, 3), (3, 3)])

    def test_player_hitbox_sizes(self):
        # 1·2타 앞 1칸 × 가로 3칸, 3타 앞 2칸 × 가로 1칸 (2026-11-17 사용자 결정)
        self.assertEqual(config.PLAYER_ATTACK_REACH, (1, 1, 2))
        self.assertEqual(config.PLAYER_ATTACK_WIDTH, (3, 3, 1))


class TrainingDummyTest(unittest.TestCase):
    def test_hit_flashes_shakes_and_pops_number(self):
        dummy = TrainingDummy(3, 3, max_hp=30)
        self.assertTrue(dummy.take_hit(10, (1, 0)))
        self.assertEqual(dummy.hp, 20)
        self.assertGreater(dummy.flash_left, 0)
        self.assertGreater(dummy.shake_offset()[0], 0)  # 맞은 방향(오른쪽)으로 밀림
        self.assertEqual([p.amount for p in dummy.popups], [10])
        dummy.update(1.0)
        self.assertEqual(dummy.flash_left, 0)
        self.assertEqual(dummy.shake_offset(), (0.0, 0.0))
        self.assertEqual(dummy.popups, [])
        self.assertEqual((dummy.col, dummy.row), (3, 3))  # 칸 위치는 그대로

    def test_falls_at_zero_hp_and_stands_up_later(self):
        dummy = TrainingDummy(0, 0, max_hp=20)
        dummy.take_hit(12, (0, 1))
        dummy.take_hit(12, (0, 1))
        self.assertEqual(dummy.hp, 0)
        self.assertTrue(dummy.is_down)
        self.assertFalse(dummy.take_hit(10, (0, 1)))  # 쓰러진 동안은 맞지 않음
        dummy.update(config.DUMMY_DOWN_TIME - 0.1)
        self.assertTrue(dummy.is_down)
        dummy.update(0.2)
        self.assertFalse(dummy.is_down)
        self.assertEqual(dummy.hp, 20)


ROOM = """
#######
#.....#
#P.D..#
#.....#
#######
"""


class AttackHitTest(unittest.TestCase):
    def setUp(self):
        tile_map = TileMap.from_text(ROOM)
        self.scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        self.input = InputState()
        self.dummy = self.scene.dummies[0]

    def step(self):
        self.scene.update(DT, self.input)
        self.input.begin_frame()

    def run_for(self, seconds):
        for _ in range(round(seconds / DT)):
            self.step()

    def walk(self, action, seconds):
        self.input.press(action)
        self.run_for(seconds)
        self.input.release(action)
        self.run_for(0.3)

    def click(self):
        self.input.press(Action.ATTACK)
        self.step()
        self.input.release(Action.ATTACK)

    def test_dummy_blocks_movement(self):
        self.walk(Action.MOVE_RIGHT, 1.0)  # (1,2) → (2,2) 에서 허수아비 (3,2) 에 막힘
        self.assertEqual((self.scene.player.col, self.scene.player.row), (2, 2))

    def test_one_hit_per_swing_at_hit_frame(self):
        self.walk(Action.MOVE_RIGHT, 1.0)
        self.click()
        self.assertEqual(self.dummy.hp, self.dummy.max_hp)  # 클릭한 순간에는 아직 안 맞음
        while self.scene.player.state == ATTACK:
            self.step()
        self.assertEqual(self.dummy.hp, self.dummy.max_hp - config.PLAYER_ATTACK_DAMAGE[0])  # 한 번만

    def test_combo_damages_each_hit(self):
        self.walk(Action.MOVE_RIGHT, 1.0)
        for _ in range(10):  # 0.15초마다 연타: 다음 타를 계속 예약 → 3타까지 이어짐 (그 뒤는 쿨타임)
            self.click()
            self.run_for(0.15)
        self.run_for(1.0)
        self.assertEqual(self.dummy.hp, max(0, self.dummy.max_hp - sum(config.PLAYER_ATTACK_DAMAGE)))

    def test_thrust_reaches_two_tiles_but_slashes_do_not(self):
        # (1,2) 에서 오른쪽을 보면 허수아비 (3,2) 는 두 칸 앞: 1·2타는 닿지 않고 3타만 닿는다
        self.scene.player.facing = Facing.RIGHT  # 시작 칸 (1,2) 에서 오른쪽을 봄
        hits = []
        for _ in range(3):
            self.click()
            before = self.dummy.hp
            # 한 타 시간보다 조금 짧게: 다음 클릭이 콤보로 이어지고, 그 사이에 이번 타의 판정 프레임이 지난다
            self.run_for(max(config.PLAYER_ATTACK_DURATIONS) * 0.8)
            hits.append(before - self.dummy.hp)
        self.assertEqual(hits[:2], [0, 0])
        self.assertEqual(hits[2], config.PLAYER_ATTACK_DAMAGE[2])

    def test_draw_dummies_and_player(self):
        calls = []

        class Rec:
            def __getattr__(self, name):
                return lambda *a, **k: calls.append(name)

        self.scene.draw(Rec())
        self.assertIn("fill_rect", calls)  # 허수아비 도형
        self.assertIn("draw_sprite_frame", calls)  # 주인공


if __name__ == "__main__":
    unittest.main()
