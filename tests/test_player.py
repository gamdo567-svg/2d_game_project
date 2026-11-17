import unittest
from pathlib import Path

from game import config
from game.input.input_state import Action, InputState
from game.player.facing import Facing
from game.player.player import (LEFT_SHEET_STATES, SHADOW_PATH, Player, attack_hand_sheet_path, attack_sheet_path,
                               attack_view,
                               sprite_sheet_path, weapon_sheet_path)
from game.player.state_machine import ATTACK, DODGE, IDLE, JUMP, PARRY, WALK
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
        start_row = self.player.row
        self.input.press(Action.MOVE_UP)
        states = set()
        for _ in range(60):  # 1초, 여러 칸
            self.player.update(1 / 60, self.input)
            states.add(self.player.state)
        self.assertEqual(states, {WALK})
        self.assertEqual(self.player.row, start_row + round(config.PLAYER_MOVE_SPEED))

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

    def test_jump_while_walking_starts_now_and_finishes_tile_in_air(self):
        self.input.press(Action.MOVE_RIGHT)
        self.player.update(STEP / 2, self.input)  # 한 칸 이동 도중
        self.assertTrue(self.player.mover.is_moving)
        self.input.begin_frame()
        self.input.press(Action.JUMP)
        self.player.update(1 / 60, self.input)
        self.assertEqual(self.player.state, JUMP)  # 바로 점프 (2026-11-17 사용자 결정)
        self.input.begin_frame()
        self.player.update(STEP, self.input)
        self.assertEqual(self.player.col, 6)  # 걷던 한 칸은 공중에서 마저 가고, 다음 칸으로는 가지 않음
        self.assertFalse(self.player.mover.is_moving)

    def test_input_buffer_runs_action_pressed_just_before_free(self):
        # 공격 판정 직전(선딜 중이라 아직 끊을 수 없음)에 누른 점프를 기억했다가 판정이 나오자마자 실행 (후딜 캔슬)
        self.tap(Action.ATTACK)
        self.assertEqual(self.player.state, ATTACK)
        hit_time = self.player.combo.current.duration * config.PLAYER_ATTACK_HIT_FRAMES[0] / config.PLAYER_ATTACK_FRAMES
        self.run_for(hit_time - config.PLAYER_INPUT_BUFFER_TIME / 2)
        self.tap(Action.JUMP)
        self.assertEqual(self.player.state, ATTACK)
        self.run_for(config.PLAYER_INPUT_BUFFER_TIME)
        self.assertEqual(self.player.state, JUMP)

    def test_input_buffer_expires(self):
        self.tap(Action.ATTACK)
        self.tap(Action.JUMP)  # 공격 초반에 누른 점프는 기억 시간이 지나 사라짐
        self.run_for(self.player.combo.current.duration + 0.1)
        self.assertNotEqual(self.player.state, JUMP)

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

    def test_jump_facing_left_flips_side_sheet(self):
        # 2026-11-17 점프 그림은 후드를 잡지 않아 좌우 대칭: 왼쪽은 측면 그림을 뒤집는다
        self.assertNotIn(JUMP, LEFT_SHEET_STATES)
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
        self.assertEqual(body[1][0], sprite_sheet_path(JUMP, "side"))
        self.assertTrue(body[2]["flip_horizontal"])

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

class PlayerAttackTest(unittest.TestCase):
    DT = 1 / 60

    def setUp(self):
        self.player = make_player()
        self.input = InputState()

    def step(self):
        self.player.update(self.DT, self.input)
        self.input.begin_frame()

    def run_for(self, seconds):
        for _ in range(round(seconds / self.DT)):
            self.step()

    def click(self):
        self.input.press(Action.ATTACK)
        self.step()
        self.input.release(Action.ATTACK)

    def run_until_idle(self, limit=3.0):
        for _ in range(round(limit / self.DT)):
            if self.player.state != ATTACK:
                return
            self.step()
        self.fail("공격이 끝나지 않음")

    def hit_time(self, index=0):
        return config.PLAYER_ATTACK_DURATIONS[index] * config.PLAYER_ATTACK_HIT_FRAMES[index] / config.PLAYER_ATTACK_FRAMES

    def press(self, action):
        self.input.press(action)
        self.step()
        self.input.release(action)

    def test_cannot_cancel_before_hit(self):
        # 선딜 중에 누른 회피·점프·패링은 공격을 끊지 않는다 (기억 시간이 지나면 사라짐)
        self.click()
        for action in (Action.JUMP, Action.PARRY, Action.DODGE):
            self.press(action)
            self.assertEqual(self.player.state, ATTACK)

    def test_recovery_cancel_after_hit(self):
        # 판정이 나온 뒤에는 회피·점프·패링으로 공격을 바로 끊는다 (후딜 캔슬, 2026-11-17)
        for action, state in ((Action.JUMP, JUMP), (Action.PARRY, PARRY), (Action.DODGE, DODGE)):
            with self.subTest(action=action):
                self.setUp()
                self.click()
                self.run_for(self.hit_time() + 2 * self.DT)
                self.assertEqual(self.player.state, ATTACK)
                self.press(action)
                self.assertEqual(self.player.state, state)

    def test_cancel_last_hit_keeps_cooldown(self):
        # 3타를 끊어도 쿨타임은 걸린다
        self.click()
        for i in range(2):
            self.run_for(config.PLAYER_ATTACK_DURATIONS[i] * 0.8)
            self.click()
        self.run_for(0.1)  # 예약한 다음 타(3타)로 넘어갈 때까지
        self.assertEqual(self.player.combo.index, 2)
        self.run_for(self.hit_time(2) + 2 * self.DT)
        self.press(Action.JUMP)
        self.assertEqual(self.player.state, JUMP)
        self.assertFalse(self.player.combo.can_start)

    def test_attack_while_walking_finishes_step_first(self):
        # 걷는 중에 공격하면 걷던 칸을 빠르게 마저 가서 칸에 선 뒤 공격한다 (미끄러지며 공격하지 않음)
        self.input.press(Action.MOVE_RIGHT)
        for _ in range(3):
            self.step()
        self.assertTrue(self.player.mover.is_moving)
        target = (self.player.col, self.player.row)
        self.input.press(Action.ATTACK)
        self.step()
        self.input.release(Action.ATTACK)
        self.assertNotEqual(self.player.state, ATTACK)  # 아직 걷던 칸을 마저 가는 중
        self.run_for(config.PLAYER_ATTACK_STEP_FINISH_TIME + 2 * self.DT)
        self.assertEqual(self.player.state, ATTACK)
        self.assertFalse(self.player.mover.is_moving)
        self.assertEqual((self.player.col, self.player.row), target)  # 다음 칸으로 가지 않음
        self.assertEqual(self.player.mover.visual_position, (float(target[0]), float(target[1])))

    def test_single_click_plays_first_hit_in_place_then_idle(self):
        self.click()
        self.assertEqual(self.player.state, ATTACK)
        self.assertEqual(self.player.combo.hit_number, 1)
        self.run_for(config.PLAYER_ATTACK_DURATIONS[0] * 0.9)
        self.assertEqual(self.player.state, ATTACK)
        self.assertEqual((self.player.col, self.player.row), (5, 5))
        self.run_for(config.PLAYER_ATTACK_DURATIONS[0] * 0.1 + 2 * self.DT)
        self.assertEqual(self.player.state, IDLE)

    def test_no_movement_during_attack(self):
        self.click()
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(config.PLAYER_ATTACK_DURATIONS[0] * 0.9)
        self.assertEqual((self.player.col, self.player.row), (5, 5))
        self.assertEqual(self.player.state, ATTACK)

    def test_click_during_attack_chains_next_hit_skipping_recovery(self):
        self.click()
        self.click()  # 1타 중에 미리 클릭
        hit1 = self.player.combo.hits[0]
        frames = []
        while self.player.combo.hit_number == 1:
            frames.append(self.player.combo.frame_index)
            self.step()
        self.assertEqual(self.player.state, ATTACK)
        self.assertEqual(self.player.combo.hit_number, 2)
        self.assertNotIn(config.PLAYER_ATTACK_FRAMES - 1, frames)  # 복귀 프레임을 건너뜀
        self.assertLess(hit1.progress, 1.0)
        self.assertEqual(self.player.combo.frame_index, 0)

    def test_three_hits_then_cooldown_blocks_only_attack(self):
        self.click()
        while not self.player.combo.is_last_hit:
            self.click()  # 공격 중 클릭: 다음 타 예약
            hit = self.player.combo.hit_number
            while self.player.combo.hit_number == hit:
                self.step()
            self.assertEqual(self.player.state, ATTACK)
        self.assertEqual(self.player.combo.hit_number, 3)
        self.run_until_idle()
        # 쿨타임: 클릭해도 공격하지 않지만 이동은 된다
        self.click()
        self.assertNotEqual(self.player.state, ATTACK)
        self.input.press(Action.MOVE_RIGHT)
        self.run_for(0.2)
        self.input.release(Action.MOVE_RIGHT)
        self.assertGreater(self.player.col, 5)
        self.run_for(config.PLAYER_ATTACK_COOLDOWN)
        self.click()
        self.assertEqual(self.player.state, ATTACK)
        self.assertEqual(self.player.combo.hit_number, 1)

    def test_click_within_window_after_hit_continues_combo(self):
        self.click()
        self.run_until_idle()
        self.run_for(config.PLAYER_ATTACK_COMBO_WINDOW / 2)
        self.click()
        self.assertEqual(self.player.combo.hit_number, 2)

    def test_click_after_window_restarts_combo(self):
        self.click()
        self.run_until_idle()
        self.run_for(config.PLAYER_ATTACK_COMBO_WINDOW + 0.05)
        self.click()
        self.assertEqual(self.player.combo.hit_number, 1)

    def test_third_hit_does_not_queue_more(self):
        combo = self.player.combo
        combo.index = 2
        combo.queued = False
        combo.request_next()
        self.assertFalse(combo.queued)

    def test_attack_frames_follow_frame_ends(self):
        self.click()
        seen = []
        while self.player.state == ATTACK:
            seen.append(self.player.combo.frame_index)
            self.step()
        self.assertEqual(sorted(set(seen)), list(range(config.PLAYER_ATTACK_FRAMES)))
        self.assertEqual(seen, sorted(seen))

    def test_attack_frame_shift_moves_sprite_forward_only(self):
        # 3타 찌름 프레임: 앞쪽으로 옮겨 그리지만 칸 위치는 그대로
        combo = self.player.combo
        self.click()
        combo.index = 2
        combo.current.reset()
        while combo.frame_index != 2:
            self.step()
        self.player.facing = Facing.RIGHT
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        (name, args, kwargs), _sword, _hand = renderer.calls
        tile, scale = config.RENDER_TILE_SIZE, config.RENDER_SCALE
        shift_x, _ = config.PLAYER_ATTACK_FRAME_SHIFTS[2][2]
        self.assertAlmostEqual(args[4], 5 * tile + tile / 2 + shift_x * scale)
        self.assertEqual((self.player.col, self.player.row), (5, 5))

    def test_attack_draws_hit_sheet_with_feet_on_tile(self):
        self.input.press(Action.MOVE_LEFT)  # 왼쪽 보기
        self.step()
        self.input.release(Action.MOVE_LEFT)
        self.run_for(1.0)
        self.click()
        self.click()
        while self.player.combo.hit_number == 1:
            self.step()
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        (name, args, kwargs), _sword, _hand = renderer.calls
        w, h, scale = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT, config.RENDER_SCALE
        self.assertEqual(args[0], attack_sheet_path(2))
        self.assertEqual(args[2:4], (w, h))
        self.assertEqual(args[6:8], (w * scale, h * scale))
        tile = config.RENDER_TILE_SIZE
        col, row = self.player.col, self.player.row
        self.assertAlmostEqual(args[4], col * tile + tile / 2)
        self.assertAlmostEqual(args[5], row * tile - config.PLAYER_ATTACK_FOOT_MARGIN * scale)
        self.assertTrue(kwargs["flip_horizontal"])

    def _draw_attack_frame(self, facing_left: bool = False, action: Action | None = None):
        # 바라볼 방향으로 한 칸 걸은 뒤 멈추고 공격한다 (기본: 오른쪽, facing_left: 왼쪽)
        action = action or (Action.MOVE_LEFT if facing_left else Action.MOVE_RIGHT)
        self.input.press(action)
        self.step()
        self.input.release(action)
        self.run_for(1.0)
        self.click()
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        return renderer.calls

    def test_attack_draws_one_sword_image_at_hand(self):
        # 몸 그림 다음에 칼 그림 한 장을 그린다: 그림 한가운데(손)가 캔버스의 손 픽셀 가운데에 오고, 각도만큼 돌린다.
        body, sword, hand = self._draw_attack_frame(facing_left=False)
        _, bargs, _ = body
        name, args, kwargs = sword
        scale = config.RENDER_SCALE
        w, h = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        hand_x, hand_y, angle, behind = config.PLAYER_ATTACK_SWORD[0][self.player.combo.frame_index]
        self.assertFalse(behind)
        self.assertEqual(name, "draw_image_rotated")
        self.assertEqual(args[0], weapon_sheet_path(config.PLAYER_WEAPON))
        canvas_left = bargs[4] - w * scale / 2
        canvas_top = bargs[5] + h * scale
        self.assertAlmostEqual(args[1], canvas_left + (hand_x + 0.5) * scale)
        self.assertAlmostEqual(args[2], canvas_top - (hand_y + 0.5) * scale)
        self.assertEqual(args[3:5], (config.PLAYER_SWORD_SPRITE_WIDTH * scale, config.PLAYER_SWORD_SPRITE_HEIGHT * scale))
        self.assertEqual(args[5], angle)
        self.assertFalse(kwargs["flip_horizontal"])

    def test_attack_draws_right_hand_layer_over_sword(self):
        # 두 손 잡기: 칼 다음에 오른손 레이어를 몸과 같은 자리·크기·반전으로 그린다
        body, sword, hand = self._draw_attack_frame(facing_left=True)
        _, bargs, bkw = body
        name, args, kwargs = hand
        self.assertEqual(name, "draw_sprite_frame")
        self.assertEqual(args[0], attack_hand_sheet_path(1))
        self.assertEqual(args[1:], bargs[1:])
        self.assertEqual(kwargs, bkw)

    def test_front_thrust_draws_no_game_sword(self):
        # 정면 3타 찌르는 순간은 칼이 몸 그림에 들어 있어(PixelLab 칼) 게임 칼을 그리지 않는다
        self._draw_attack_frame(action=Action.MOVE_DOWN)
        for _ in range(round(3.0 / self.DT)):
            combo = self.player.combo
            if combo.index == 2 and combo.current is not None and combo.current.progress >= 0.55:
                break
            self.click()
        else:
            self.fail("3타 찌르는 순간에 닿지 못함")
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        self.assertNotIn("draw_image_rotated", [call[0] for call in renderer.calls])

    def test_attack_facing_down_uses_front_sheets(self):
        # 아래를 보면 정면 몸·칼 앞 레이어 시트와 정면 칼 위치표를 쓴다. 반전 없음.
        body, sword, hand = self._draw_attack_frame(action=Action.MOVE_DOWN)
        frame = self.player.combo.frame_index
        hand_x, hand_y, angle, behind = config.PLAYER_ATTACK_SWORD_FRONT[0][frame]
        self.assertFalse(behind)
        self.assertEqual(body[1][0], attack_sheet_path(1, "front"))
        self.assertEqual(hand[1][0], attack_hand_sheet_path(1, "front"))
        _, args, kwargs = sword
        scale = config.RENDER_SCALE
        self.assertEqual(args[3], config.PLAYER_SWORD_SPRITE_WIDTH * scale)
        self.assertEqual(args[5], angle)
        self.assertFalse(kwargs["flip_horizontal"])
        self.assertFalse(body[2]["flip_horizontal"])

    def test_attack_view_uses_side_when_facing_up(self):
        # 후면 공격 그림이 없어 위를 볼 때는 측면 그림. 아래는 정면.
        for index in range(config.PLAYER_ATTACK_HITS):
            self.assertEqual(attack_view(Facing.UP, index), "side")
            self.assertEqual(attack_view(Facing.DOWN, index), "front")
        self.assertEqual(attack_view(Facing.LEFT, 0), "side")

    def test_attack_sword_mirrors_when_facing_left(self):
        # 왼쪽: 손 위치를 좌우로 뒤집고, 칼은 뒤집은 뒤 반대 각도로 돌린다 (칼끝 방향 180 - 각도)
        body, sword, hand = self._draw_attack_frame(facing_left=True)
        _, bargs, _ = body
        _, args, kwargs = sword
        scale, w = config.RENDER_SCALE, config.PLAYER_ATTACK_SPRITE_WIDTH
        hand_x, _, angle, _ = config.PLAYER_ATTACK_SWORD[0][self.player.combo.frame_index]
        canvas_left = bargs[4] - w * scale / 2
        self.assertAlmostEqual(args[1], canvas_left + (w - hand_x - 0.5) * scale)
        self.assertEqual(args[5], -angle)
        self.assertTrue(kwargs["flip_horizontal"])


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

    def test_player_starts_at_map_start_tile(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
        self.assertEqual((scene.player.col, scene.player.row), scene.tile_map.player_start)

    def test_walls_block_player_but_turn_facing(self):
        # 시작 칸 (16, 9)에서 위로: (16, 10)은 바닥, (16, 11)은 가로 벽 → 한 칸만 가고 멈춘다. 방향은 위를 본다.
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
        self.assertTrue(scene.tile_map.is_wall(16, 11))
        inp = InputState()
        inp.press(Action.MOVE_UP)
        for _ in range(120):
            scene.update(1 / 60, inp)
            inp.begin_frame()
            self.assertFalse(scene.tile_map.is_wall(scene.player.col, scene.player.row))
        self.assertEqual((scene.player.col, scene.player.row), (16, 10))
        self.assertEqual(scene.player.facing, Facing.UP)

    def test_draw_fills_wall_tiles(self):
        scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
        renderer = _RecordingRenderer()
        scene.draw(renderer)
        filled = {(c[1][1], c[1][2]) for c in renderer.calls if c[0] == "fill_tile"}
        self.assertEqual(filled, set(scene.tile_map.walls))

    def test_map_size_must_match_grid(self):
        with self.assertRaises(ValueError):
            FieldScene(Grid(10, 10, config.RENDER_TILE_SIZE))

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
