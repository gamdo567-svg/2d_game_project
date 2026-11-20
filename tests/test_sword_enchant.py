"""검 속성 입히기 테스트 (2026-11-20 사용자 결정, pico2d 없이)."""
import unittest

from game import config
from game.input.input_state import Action, InputState
from game.player.enchant import SwordEnchant
from game.player.state_machine import ATTACK, ENCHANT, HURT, IDLE
from tests.test_player import _RecordingRenderer, make_player


class SwordEnchantLogicTest(unittest.TestCase):
    def test_select_does_not_change_sword(self):
        e = SwordEnchant()
        e.select(2)
        self.assertEqual(e.selected, "dark")
        self.assertIsNone(e.active)

    def test_applied_when_rise_completes(self):
        e = SwordEnchant()
        self.assertTrue(e.press())
        start, end = config.PLAYER_ENCHANT_RISE
        e.update(config.PLAYER_ENCHANT_DURATION * (start + end) / 2)
        self.assertIsNone(e.active)  # 차오르는 중
        self.assertGreater(e.rise, 0.0)
        self.assertLess(e.rise, 1.0)
        e.update(config.PLAYER_ENCHANT_DURATION)
        self.assertEqual(e.active, "fire")

    def test_same_element_again_removes_it(self):
        e = SwordEnchant()
        e.press()
        e.update(config.PLAYER_ENCHANT_DURATION)
        self.assertFalse(e.press())  # 같은 속성: 동작 없이 풀림
        self.assertIsNone(e.active)

    def test_interrupt_before_full_keeps_previous(self):
        e = SwordEnchant()
        e.press()
        e.update(config.PLAYER_ENCHANT_DURATION)
        e.select(1)
        e.press()
        e.update(config.PLAYER_ENCHANT_DURATION * config.PLAYER_ENCHANT_RISE[0])
        e.interrupt()
        e.update(config.PLAYER_ENCHANT_DURATION)
        self.assertEqual(e.active, "fire")


class PlayerEnchantTest(unittest.TestCase):
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

    def test_e_enchants_and_stays_still(self):
        self.tap(Action.ELEMENT_1)
        self.tap(Action.ENCHANT)
        self.assertEqual(self.player.state, ENCHANT)
        self.input.begin_frame()
        self.input.press(Action.MOVE_RIGHT)  # 입히는 중에는 움직이지 않음
        for _ in range(30):
            self.player.update(1 / 60, self.input)
            self.input.begin_frame()
        self.assertEqual((self.player.col, self.player.row), (5, 5))
        self.input.release(Action.MOVE_RIGHT)
        self.run_for(config.PLAYER_ENCHANT_DURATION)
        self.assertNotEqual(self.player.state, ENCHANT)
        self.assertEqual(self.player.enchant.active, "fire")
        self.assertEqual(self.player.sword_effect, ("fire", 1.0))

    def test_number_keys_pick_element(self):
        self.tap(Action.ELEMENT_3)
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.assertEqual(self.player.enchant.active, "dark")

    def test_same_element_e_removes_without_motion(self):
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.tap(Action.ENCHANT)
        self.assertEqual(self.player.state, IDLE)
        self.assertIsNone(self.player.enchant.active)
        self.assertIsNone(self.player.sword_effect)

    def test_hurt_interrupts_enchant(self):
        self.tap(Action.ENCHANT)
        self.run_for(0.1)
        self.player.fsm.trigger("hurt")
        self.assertEqual(self.player.state, HURT)
        self.run_for(config.PLAYER_ENCHANT_DURATION)
        self.assertIsNone(self.player.enchant.active)

    def test_effect_rises_from_hilt_while_enchanting(self):
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION * (sum(config.PLAYER_ENCHANT_RISE) / 2))
        element, rise = self.player.sword_effect
        self.assertEqual(element, "fire")
        self.assertTrue(0.0 < rise < 1.0)
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        effect = [c for c in renderer.calls if c[0] == "draw_frame_rotated"]
        self.assertEqual(len(effect), 1)
        self.assertTrue(effect[0][1][0].endswith("fire_ignite.png"))  # 점화 시트
        self.assertTrue(0 < effect[0][1][1] < config.SWORD_EFFECT_IGNITE_FRAMES - 1)  # 번지는 중간 장

    def test_effect_drawn_on_sword_during_attack(self):
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.tap(Action.ATTACK)
        self.run_for(0.05)
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        effect = [c for c in renderer.calls if c[0] == "draw_frame_rotated"]
        self.assertEqual(len(effect), 1)
        self.assertTrue(effect[0][1][0].endswith("fire.png"))  # 다 붙은 뒤에는 반복 시트

    def test_burst_and_shake_when_fully_charged_then_flick(self):
        # 다 차는 순간 폭발·화면 흔들림, 마지막에 칼을 털어 내림 (2026-11-20 사용자: 더 역동적으로, 털어내는 느낌)
        self.tap(Action.ENCHANT)
        shook, burst_seen, swing_seen = False, False, False
        for _ in range(round(config.PLAYER_ENCHANT_DURATION * 60)):
            self.input.begin_frame()
            self.player.update(1 / 60, self.input)
            shook = shook or bool(self.player.shake_requests)
            renderer = _RecordingRenderer()
            self.player.draw(renderer)
            if self.player.fx.active and any(c[0] == "fill_rect" for c in renderer.calls):
                burst_seen = True
            if any(c[0] == "draw_sprite_frame" and "enchant" in c[1][0] for c in renderer.calls) and                     self.player.enchant.progress >= config.PLAYER_ENCHANT_FRAME_ENDS[config.PLAYER_ENCHANT_FLICK_FRAME - 1]:
                swing_seen = True  # 털어내기 장
        self.assertTrue(shook)
        self.assertTrue(burst_seen)
        self.assertTrue(swing_seen)
        self.assertEqual(self.player.enchant.active, "fire")

    def test_flick_sprays_particles(self):
        self.tap(Action.ENCHANT)
        renderer = _RecordingRenderer()
        counts = []
        for _ in range(round(config.PLAYER_ENCHANT_DURATION * 60) + 20):
            self.input.begin_frame()
            self.player.update(1 / 60, self.input)
            self.player.draw(renderer)
            counts.append(len(self.player.fx.particles))
        flick_at = round(config.PLAYER_ENCHANT_FRAME_ENDS[config.PLAYER_ENCHANT_FLICK_FRAME - 1]
                         * config.PLAYER_ENCHANT_DURATION * 60)
        self.assertGreater(max(counts[flick_at:flick_at + 5]), 10)  # 털어낼 때 불똥이 흩뿌려짐

    def test_flourish_swing_deals_no_damage(self):
        self.tap(Action.ENCHANT)
        for _ in range(round(config.PLAYER_ENCHANT_DURATION * 60) + 5):
            self.input.begin_frame()
            self.player.update(1 / 60, self.input)
            self.assertEqual(self.player.strikes, [])

    def test_effect_on_back_sword_when_idle(self):
        # 칼집 없이 등에 멘 칼에도 속성 이펙트 (2026-11-20 사용자 요청)
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.assertEqual(self.player.state, IDLE)
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        effect = [c for c in renderer.calls if c[0] == "draw_frame_rotated"]
        self.assertEqual(len(effect), 1)
        self.assertEqual(effect[0][1][7], config.PLAYER_BACK_SWORD_HAND["front"][2])  # 등 칼과 같은 각도

    def test_sheathe_frames_draw_back_sword(self):
        # 등에 다시 꽂기 (2026-11-20): 마지막 장들은 손의 칼 대신 등 칼을 그림
        self.tap(Action.ENCHANT)
        sheathed = config.PLAYER_ENCHANT_FRAME_ENDS[config.PLAYER_ENCHANT_SHEATHED_FROM - 1]
        self.run_for(config.PLAYER_ENCHANT_DURATION * sheathed + 0.03)
        self.assertEqual(self.player.state, ENCHANT)
        renderer = _RecordingRenderer()
        self.player.draw(renderer)
        paths = [c[1][0] for c in renderer.calls if c[0] == "draw_sprite_frame"]
        self.assertTrue(any("_back_front" in p for p in paths))  # 등 칼 그림

    def test_move_cancels_tail_after_applied(self):
        # 속성이 입혀진 뒤의 털어내기·힘 풀기·꽂기는 이동으로 끊을 수 있음
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION * config.PLAYER_ENCHANT_RISE[1] + 0.05)
        self.assertEqual(self.player.enchant.active, "fire")
        self.assertEqual(self.player.state, ENCHANT)
        self.input.begin_frame()
        self.input.press(Action.MOVE_RIGHT)
        self.player.update(1 / 60, self.input)
        self.assertNotEqual(self.player.state, ENCHANT)
        self.assertEqual(self.player.enchant.active, "fire")
        self.assertTrue(self.player.mover.is_moving)

    def test_attack_cancels_tail_after_applied(self):
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION * config.PLAYER_ENCHANT_RISE[1] + 0.05)
        self.tap(Action.ATTACK)
        self.assertEqual(self.player.state, ATTACK)

    def test_cannot_cancel_while_charging(self):
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION * config.PLAYER_ENCHANT_RISE[0] + 0.05)
        self.input.begin_frame()
        self.input.press(Action.MOVE_RIGHT)
        self.player.update(1 / 60, self.input)
        self.assertEqual(self.player.state, ENCHANT)
        self.assertIsNone(self.player.enchant.active)

    def test_effect_on_front_thrust_art(self):
        # 정면 3타 찌르는 순간은 찌르기용 칼 그림을 쓰는데, 거기에도 이펙트가 붙어야 함 (2026-11-20 사용자 지적)
        self.tap(Action.ENCHANT)
        self.run_for(config.PLAYER_ENCHANT_DURATION + 0.1)
        self.input.begin_frame()
        self.input.press(Action.ATTACK)  # 누르고 있으면 1 → 2 → 3타
        found = False
        for _ in range(int(2.2 * 60)):
            self.player.update(1 / 60, self.input)
            self.input.begin_frame()
            renderer = _RecordingRenderer()
            self.player.draw(renderer)
            paths = [c[1][0] for c in renderer.calls if c[0] == "draw_sprite_frame"]
            if any(p.endswith("old_sword_front_3.png") for p in paths):
                self.assertTrue(any("fire_front_3_f" in p for p in paths))  # 그 칼 전용 불 시트
                found = True
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
