import unittest

from game import config
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.player import Player, sprite_sheet_path
from game.player.state_machine import IDLE, WALK
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid

STEP = 1.0 / config.PLAYER_MOVE_SPEED  # 한 칸 이동 시간(초)


class _RecordingRenderer:
    """pico2d 없이 그리기 호출을 기록하는 가짜 Renderer."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return record


def make_player(col=5, row=5):
    return Player(Grid(config.GRID_COLS, config.GRID_ROWS, config.TILE_SIZE), col, row)


class PlayerTest(unittest.TestCase):
    def setUp(self):
        self.player = make_player()
        self.input = InputState()

    def test_starts_idle_facing_down(self):
        self.assertEqual(self.player.state, IDLE)
        self.assertEqual(self.player.facing, Facing.DOWN)

    def test_moving_switches_to_walk_then_idle(self):
        self.input.press(Action.MOVE_RIGHT)
        self.player.update(0.01, self.input)
        self.assertEqual(self.player.state, WALK)
        self.assertEqual((self.player.col, self.player.row), (6, 5))

        self.input.release(Action.MOVE_RIGHT)
        self.player.update(STEP, self.input)
        self.assertEqual(self.player.state, IDLE)

    def test_stays_walk_between_tiles_while_key_held(self):
        self.input.press(Action.MOVE_UP)
        states = set()
        for _ in range(60):  # 1초, 여러 칸
            self.player.update(1 / 60, self.input)
            states.add(self.player.state)
        self.assertEqual(states, {WALK})
        self.assertGreater(self.player.row, 9)

    def test_facing_follows_movement(self):
        for action, facing in (
            (Action.MOVE_LEFT, Facing.LEFT),
            (Action.MOVE_UP, Facing.UP),
            (Action.MOVE_RIGHT, Facing.RIGHT),
            (Action.MOVE_DOWN, Facing.DOWN),
        ):
            self.input.press(action)
            self.player.update(STEP, self.input)
            self.input.release(action)
            self.player.update(STEP, self.input)
            self.assertEqual(self.player.facing, facing)

    def test_facing_does_not_change_mid_step(self):
        self.input.press(Action.MOVE_RIGHT)
        self.player.update(STEP / 2, self.input)
        self.input.release(Action.MOVE_RIGHT)
        self.input.press(Action.MOVE_UP)
        self.player.update(STEP / 4, self.input)  # 아직 오른쪽으로 가는 중
        self.assertEqual(self.player.facing, Facing.RIGHT)

    def test_two_keys_move_only_one_axis(self):
        self.input.press(Action.MOVE_UP)
        self.input.press(Action.MOVE_RIGHT)
        for _ in range(30):
            self.player.update(1 / 60, self.input)
        self.assertEqual(self.player.row, 5)  # 위로는 움직이지 않음
        self.assertGreater(self.player.col, 5)
        self.assertEqual(self.player.facing, Facing.RIGHT)

    def test_walk_animation_keeps_cycling_across_tiles(self):
        # 칸이 바뀔 때마다 첫 프레임으로 돌아가면 걷는 동작이 보이지 않는다.
        self.input.press(Action.MOVE_RIGHT)
        seen = set()
        for _ in range(60):  # 1초 = 6칸
            self.player.update(1 / 60, self.input)
            seen.add(self.player.animation.frame_index)
        self.assertEqual(seen, set(range(config.PLAYER_WALK_FRAMES)))

    def test_pressing_into_edge_turns_without_moving(self):
        player = make_player(col=0, row=0)
        self.input.press(Action.MOVE_LEFT)
        player.update(STEP, self.input)
        self.assertEqual((player.col, player.row), (0, 0))
        self.assertEqual(player.facing, Facing.LEFT)
        self.assertEqual(player.state, IDLE)

    def test_idle_animation_plays_while_standing(self):
        self.player.update(config.PLAYER_IDLE_FRAME_DURATION * 1.5, self.input)
        self.assertEqual(self.player.animation.frame_index, 1)

    def test_walk_animation_starts_from_first_frame(self):
        self.player.update(config.PLAYER_IDLE_FRAME_DURATION * 2.5, self.input)  # idle 2번 프레임
        self.input.press(Action.MOVE_DOWN)
        self.player.update(0.001, self.input)
        self.assertEqual(self.player.state, WALK)
        self.assertEqual(self.player.animation.frame_index, 0)

    def test_draw_uses_sprite_for_state_and_facing(self):
        self.input.press(Action.MOVE_LEFT)
        self.player.update(STEP / 2, self.input)
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        name, args, kwargs = renderer.calls[0]
        self.assertEqual(name, "draw_sprite_frame")
        self.assertEqual(args[0], sprite_sheet_path(WALK, "side"))
        self.assertEqual(args[2:4], (config.PLAYER_SPRITE_WIDTH, config.PLAYER_SPRITE_HEIGHT))
        self.assertTrue(kwargs["flip_horizontal"])
        # 발끝 위치: 4.5칸(보간 중) 칸의 아래 가운데
        tile = config.TILE_SIZE
        self.assertAlmostEqual(args[4], 4.5 * tile + tile / 2)
        self.assertAlmostEqual(args[5], 5 * tile)

    def test_sprite_sheet_path(self):
        self.assertTrue(sprite_sheet_path(IDLE, "front").endswith("idle_front.png"))


class FieldSceneTest(unittest.TestCase):
    def test_player_starts_at_configured_tile(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.TILE_SIZE))
        self.assertEqual(
            (scene.player.col, scene.player.row),
            (config.PLAYER_START_COL, config.PLAYER_START_ROW),
        )

    def test_draw_uses_renderer_only(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.TILE_SIZE))
        scene.update(0.016, InputState())
        renderer = _RecordingRenderer()
        scene.draw(renderer)
        names = [call[0] for call in renderer.calls]
        self.assertIn("fill_screen", names)
        self.assertIn("draw_sprite_frame", names)


if __name__ == "__main__":
    unittest.main()
