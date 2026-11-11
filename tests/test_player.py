import unittest
from pathlib import Path

from game import config
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.player import LEFT_SHEET_STATES, SHADOW_PATH, Player, sprite_sheet_path
from game.player.state_machine import IDLE, JUMP, PARRY, WALK
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
    return Player(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE), col, row)


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
        self.assertEqual(args[6:8], (config.PLAYER_RENDER_WIDTH, config.PLAYER_RENDER_HEIGHT))
        self.assertTrue(kwargs["flip_horizontal"])
        # 발끝 위치: 4.5칸(보간 중) 칸의 아래 가운데
        tile = config.RENDER_TILE_SIZE
        self.assertAlmostEqual(args[4], 4.5 * tile + tile / 2)
        self.assertAlmostEqual(args[5], 5 * tile)

    def test_sprite_sheet_path(self):
        self.assertEqual(Path(sprite_sheet_path(IDLE, "front")).parts[-2:], ("idle", "front.png"))


class JumpParryTest(unittest.TestCase):
    def setUp(self):
        self.player = make_player()
        self.input = InputState()

    def tap(self, action):
        self.input.begin_frame()
        self.input.press(action)
        self.player.update(1 / 60, self.input)
        self.input.begin_frame()
        self.input.release(action)

    def run_for(self, seconds):
        for _ in range(round(seconds * 60)):
            self.input.begin_frame()
            self.player.update(1 / 60, self.input)

    def test_jump_in_place_then_idle(self):
        self.tap(Action.JUMP)
        self.assertEqual(self.player.state, JUMP)
        heights = []
        for _ in range(round(config.PLAYER_JUMP_DURATION * 60) + 2):
            heights.append(self.player.jump.height)
            self.input.begin_frame()
            self.player.update(1 / 60, self.input)
        self.assertGreater(max(heights), 0)
        self.assertEqual(self.player.state, IDLE)
        self.assertEqual((self.player.col, self.player.row), (5, 5))  # 제자리

    def test_no_movement_during_jump(self):
        self.tap(Action.JUMP)
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(config.PLAYER_JUMP_DURATION * 0.8)
        self.assertEqual(self.player.state, JUMP)
        self.assertEqual(self.player.col, 5)
        self.run_for(config.PLAYER_JUMP_DURATION * 0.2 + STEP)
        self.assertGreater(self.player.col, 5)  # 착지 후 다시 걷는다

    def test_jump_pressed_while_walking_waits_for_tile(self):
        self.input.press(Action.MOVE_RIGHT)
        self.player.update(STEP / 2, self.input)  # 한 칸 이동 도중
        self.assertTrue(self.player.mover.is_moving)
        self.input.begin_frame()
        self.input.press(Action.JUMP)
        self.player.update(STEP / 4, self.input)
        self.assertEqual(self.player.state, WALK)  # 아직 이동 중: 점프 대기
        self.input.begin_frame()
        self.player.update(STEP / 2, self.input)
        self.assertEqual(self.player.state, JUMP)
        self.assertEqual(self.player.col, 6)  # 다음 칸으로는 가지 않고 도착 칸에서 점프
        self.assertFalse(self.player.mover.is_moving)

    def test_parry_starts_immediately_and_blocks_movement(self):
        self.input.press(Action.MOVE_UP)
        self.player.update(STEP / 2, self.input)  # 한 칸 이동 도중
        self.input.begin_frame()
        self.input.press(Action.PARRY)
        self.player.update(1 / 60, self.input)
        self.assertEqual(self.player.state, PARRY)
        self.assertTrue(self.player.parry.is_active)
        self.run_for(config.PLAYER_PARRY_DURATION * 0.9)
        self.assertEqual(self.player.row, 6)  # 진행 중이던 한 칸만 마저 가고 멈춤
        self.assertEqual(self.player.facing, Facing.UP)
        self.run_for(config.PLAYER_PARRY_DURATION * 0.1 + 2 / 60)
        self.assertNotEqual(self.player.state, PARRY)

    def test_parry_window_from_config(self):
        self.tap(Action.PARRY)
        self.run_for(config.PLAYER_PARRY_WINDOW + 1 / 60)
        self.assertFalse(self.player.parry.is_active)
        self.assertEqual(self.player.state, PARRY)

    def test_jump_draws_shadow_and_lifts_sprite(self):
        self.tap(Action.JUMP)
        self.run_for(config.PLAYER_JUMP_DURATION / 2 - 1 / 60)  # 최고점 근처
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        (shadow_name, shadow_args, _), (body_name, body_args, _) = renderer.calls
        self.assertEqual(shadow_args[0], SHADOW_PATH)
        self.assertEqual(body_args[0], sprite_sheet_path(JUMP, "front"))
        tile = config.RENDER_TILE_SIZE
        self.assertGreater(body_args[5], 5 * tile + tile * config.PLAYER_JUMP_HEIGHT * 0.8)

    def test_jump_facing_left_uses_left_sheet(self):
        # 점프는 오른손으로 후드를 잡아 좌우 비대칭: 왼쪽은 뒤집지 않고 전용 그림
        self.assertIn(JUMP, LEFT_SHEET_STATES)
        player = make_player(col=0)
        inp = InputState()
        inp.press(Action.MOVE_LEFT)  # 맵 끝: 움직이지 않고 왼쪽을 봄
        player.update(1 / 60, inp)
        inp.release(Action.MOVE_LEFT)
        inp.begin_frame()
        inp.press(Action.JUMP)
        player.update(1 / 60, inp)
        self.assertEqual(player.state, JUMP)
        renderer = _RecordingRenderer()
        player.draw(renderer)
        body = renderer.calls[-1]
        self.assertEqual(body[1][0], sprite_sheet_path(JUMP, "side_left"))
        self.assertFalse(body[2]["flip_horizontal"])

    def test_walk_facing_left_still_flips_side(self):
        player = make_player()
        inp = InputState()
        inp.press(Action.MOVE_LEFT)
        player.update(1 / 60, inp)
        renderer = _RecordingRenderer()
        player.draw(renderer)
        (name, args, kwargs), = renderer.calls
        self.assertEqual(args[0], sprite_sheet_path(WALK, "side"))
        self.assertTrue(kwargs["flip_horizontal"])

    def test_parry_draws_standing_sprite(self):
        # 패링 애니메이션은 아직 없다 (공격 모션과 함께 제작). 서 있는 그림 첫 프레임만, 검 없이 그린다.
        self.tap(Action.PARRY)
        self.run_for(0.2)
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        (name, args, _), = renderer.calls
        self.assertEqual((args[0], args[1]), (sprite_sheet_path(IDLE, "front"), 0))

class FieldSceneTest(unittest.TestCase):
    def test_player_starts_at_configured_tile(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
        self.assertEqual(
            (scene.player.col, scene.player.row),
            (config.PLAYER_START_COL, config.PLAYER_START_ROW),
        )

    def test_draw_uses_renderer_only(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
        scene.update(0.016, InputState())
        renderer = _RecordingRenderer()
        scene.draw(renderer)
        names = [call[0] for call in renderer.calls]
        self.assertIn("fill_screen", names)
        self.assertIn("draw_sprite_frame", names)

    def test_camera_keeps_player_on_screen(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
        inp = InputState()
        for action in (Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_LEFT, Action.MOVE_DOWN):
            inp.release_all()
            inp.press(action)
            for _ in range(240):  # 4초: 맵 끝까지 이동
                scene.update(1 / 60, inp)
                left, bottom, right, top = scene.grid.tile_to_pixel_rect(*scene.player.mover.visual_position)
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(right, config.SCREEN_WIDTH)
                self.assertGreaterEqual(bottom, 0)
                self.assertLessEqual(top, config.SCREEN_HEIGHT)


if __name__ == "__main__":
    unittest.main()
