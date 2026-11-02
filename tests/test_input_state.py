import unittest

from game.input.input_state import Action, InputState


class InputStateTest(unittest.TestCase):
    def setUp(self):
        self.state = InputState()

    def test_press_sets_held_and_pressed(self):
        self.state.press(Action.QUIT)
        self.assertTrue(self.state.is_held(Action.QUIT))
        self.assertTrue(self.state.was_pressed(Action.QUIT))

    def test_pressed_lasts_one_frame(self):
        self.state.press(Action.QUIT)
        self.state.begin_frame()
        self.assertTrue(self.state.is_held(Action.QUIT))
        self.assertFalse(self.state.was_pressed(Action.QUIT))

    def test_repeated_press_while_held_is_not_new_press(self):
        self.state.press(Action.QUIT)
        self.state.begin_frame()
        self.state.press(Action.QUIT)
        self.assertFalse(self.state.was_pressed(Action.QUIT))

    def test_release(self):
        self.state.press(Action.QUIT)
        self.state.begin_frame()
        self.state.release(Action.QUIT)
        self.assertFalse(self.state.is_held(Action.QUIT))
        self.assertTrue(self.state.was_released(Action.QUIT))

    def test_release_without_press_is_ignored(self):
        self.state.release(Action.QUIT)
        self.assertFalse(self.state.was_released(Action.QUIT))

    def test_release_all(self):
        self.state.press(Action.QUIT)
        self.state.release_all()
        self.assertFalse(self.state.is_held(Action.QUIT))
        self.assertTrue(self.state.was_released(Action.QUIT))

    def test_quit_request(self):
        self.assertFalse(self.state.quit_requested)
        self.state.request_quit()
        self.assertTrue(self.state.quit_requested)

    def test_move_direction_none(self):
        self.assertEqual(self.state.move_direction(), (0, 0))

    def test_move_direction_straight(self):
        for action, vector in (
            (Action.MOVE_UP, (0, 1)),
            (Action.MOVE_DOWN, (0, -1)),
            (Action.MOVE_LEFT, (-1, 0)),
            (Action.MOVE_RIGHT, (1, 0)),
        ):
            state = InputState()
            state.press(action)
            self.assertEqual(state.move_direction(), vector)

    def test_two_keys_never_make_diagonal(self):
        # 나중에 누른 방향을 따른다
        self.state.press(Action.MOVE_UP)
        self.state.press(Action.MOVE_LEFT)
        self.assertEqual(self.state.move_direction(), (-1, 0))

    def test_releasing_latest_key_falls_back_to_previous(self):
        self.state.press(Action.MOVE_UP)
        self.state.press(Action.MOVE_LEFT)
        self.state.release(Action.MOVE_LEFT)
        self.assertEqual(self.state.move_direction(), (0, 1))

    def test_repeat_press_does_not_reorder(self):
        self.state.press(Action.MOVE_UP)
        self.state.press(Action.MOVE_LEFT)
        self.state.press(Action.MOVE_UP)  # 이미 누르고 있음 (키 반복 등)
        self.assertEqual(self.state.move_direction(), (-1, 0))

    def test_release_all_clears_move(self):
        self.state.press(Action.MOVE_RIGHT)
        self.state.release_all()
        self.assertEqual(self.state.move_direction(), (0, 0))


if __name__ == "__main__":
    unittest.main()
