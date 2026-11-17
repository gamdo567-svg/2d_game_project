"""회피 테스트 (pico2d 없이): Q, 3칸, 0.25초, 회피 중 무적, 끝난 뒤 1초 대기, 벽·허수아비 앞에서 멈춤."""
import unittest

from game import config
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.movement import GridMover
from game.player.player import sprite_sheet_path
from game.player.state_machine import ATTACK, DODGE, IDLE, WALK
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid
from game.world.tile_map import TileMap

DT = 1 / 120
ROOM = """
############
#..........#
#.P........#
#..........#
#...D......#
############
"""


class DashTest(unittest.TestCase):
    def test_dash_stops_before_blocked_tile(self):
        grid = Grid(10, 3, 32)
        mover = GridMover(grid, 1, 1, speed=6.0, can_enter=lambda c, r: c != 4)
        self.assertEqual(mover.dash(1, 0, 5, 0.25), 2)  # (2,1), (3,1) 까지
        self.assertEqual((mover.col, mover.row), (3, 1))
        mover.update(0.125, 0, 0)
        self.assertAlmostEqual(mover.visual_position[0], 2.0)  # 절반 시간에 절반 거리
        mover.update(0.125, 0, 0)
        self.assertFalse(mover.is_moving)
        self.assertEqual(mover.dash(1, 0, 5, 0.25), 0)  # 바로 앞이 막힘

    def test_dash_starts_from_drawn_position_while_walking(self):
        grid = Grid(10, 3, 32)
        mover = GridMover(grid, 1, 1, speed=6.0)
        mover.update(1 / 12, 1, 0)  # 한 칸의 절반: 그림 위치 1.5
        self.assertEqual(mover.dash(1, 0, 5, 0.25), 5)
        self.assertAlmostEqual(mover.visual_position[0], 1.5)  # 그림이 튀지 않음
        self.assertEqual(mover.col, 7)


class DodgeTest(unittest.TestCase):
    def setUp(self):
        tile_map = TileMap.from_text(ROOM)
        self.scene = FieldScene(Grid(tile_map.cols, tile_map.rows, config.RENDER_TILE_SIZE), tile_map)
        self.player = self.scene.player
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

    def face(self, facing):
        self.player.facing = facing

    def test_dodges_distance_in_facing_direction(self):
        self.face(Facing.RIGHT)
        self.tap(Action.DODGE)
        self.assertEqual(self.player.state, DODGE)
        end = (2 + config.PLAYER_DODGE_DISTANCE, 3)
        self.assertEqual((self.player.col, self.player.row), end)
        self.run_for(config.PLAYER_DODGE_DURATION - 0.05)
        self.assertEqual(self.player.state, DODGE)  # 아직 미끄러지는 중
        self.run_for(0.07)
        self.assertIn(self.player.state, (IDLE, WALK))
        self.assertEqual(self.player.mover.visual_position, end)

    def test_uses_held_direction(self):
        self.face(Facing.RIGHT)
        self.input.press(Action.MOVE_DOWN)
        self.tap(Action.DODGE)
        self.input.release(Action.MOVE_DOWN)
        self.assertEqual((self.player.col, self.player.row), (2, 1))  # 아래로 2칸 뒤 벽
        self.assertEqual(self.player.facing, Facing.DOWN)

    def test_stops_before_wall_and_dummy(self):
        self.face(Facing.UP)
        self.tap(Action.DODGE)
        self.assertEqual((self.player.col, self.player.row), (2, 4))  # 위쪽 벽 앞
        self.run_for(1.5)
        # 아래로 내려가 (2,1) 에서 오른쪽: 허수아비 (4,1) 앞 (3,1) 에서 멈춤
        self.face(Facing.DOWN)
        self.tap(Action.DODGE)
        self.assertEqual((self.player.col, self.player.row), (2, 1))
        self.run_for(1.5)
        self.face(Facing.RIGHT)
        self.tap(Action.DODGE)
        self.assertEqual((self.player.col, self.player.row), (3, 1))

    def test_blocked_dodge_does_nothing(self):
        self.face(Facing.LEFT)
        self.player.mover.col = 1
        self.player.mover._from_col = 1
        self.tap(Action.DODGE)  # 바로 왼쪽이 벽
        self.assertNotEqual(self.player.state, DODGE)
        self.assertEqual(self.player.dodge_cooldown_left, 0.0)

    def test_invincible_only_while_dodging(self):
        self.face(Facing.RIGHT)
        self.assertFalse(self.player.is_invincible)
        self.tap(Action.DODGE)
        self.assertTrue(self.player.is_invincible)
        self.run_for(config.PLAYER_DODGE_DURATION + 0.02)
        self.assertFalse(self.player.is_invincible)

    def test_cooldown_after_dodge(self):
        self.face(Facing.RIGHT)
        self.tap(Action.DODGE)
        self.run_for(config.PLAYER_DODGE_DURATION + 0.02)
        self.face(Facing.LEFT)
        self.tap(Action.DODGE)  # 대기 중: 안 됨
        self.assertNotEqual(self.player.state, DODGE)
        self.run_for(config.PLAYER_DODGE_COOLDOWN)
        self.face(Facing.LEFT)
        self.tap(Action.DODGE)
        self.assertEqual(self.player.state, DODGE)

    def test_no_attack_or_move_while_dodging(self):
        self.face(Facing.RIGHT)
        self.tap(Action.DODGE)
        self.tap(Action.ATTACK)
        self.assertEqual(self.player.state, DODGE)
        self.run_for(config.PLAYER_DODGE_DURATION + 0.02)
        self.tap(Action.ATTACK)
        self.assertEqual(self.player.state, ATTACK)  # 회피 뒤에는 바로 공격 가능

    def test_draws_walk_frames(self):
        self.face(Facing.RIGHT)
        self.tap(Action.DODGE)
        frames = set()
        for _ in range(round(config.PLAYER_DODGE_DURATION / DT) - 2):
            calls = []

            class Rec:
                def __getattr__(self, name):
                    return lambda *a, **k: calls.append((name, a))

            self.player.draw(Rec())
            name, args = calls[0]
            self.assertEqual(args[0], sprite_sheet_path(WALK, "side"))
            frames.add(args[1])
            self.step()
        self.assertEqual(frames, set(range(config.PLAYER_WALK_FRAMES)))


if __name__ == "__main__":
    unittest.main()
