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

    def test_move_direction_straight_and_diagonal(self):
        self.state.press(Action.MOVE_UP)
        self.assertEqual(self.state.move_direction(), (0, 1))
        self.state.press(Action.MOVE_LEFT)
        self.assertEqual(self.state.move_direction(), (-1, 1))

    def test_move_direction_opposite_keys_cancel(self):
        self.state.press(Action.MOVE_LEFT)
        self.state.press(Action.MOVE_RIGHT)
        self.state.press(Action.MOVE_DOWN)
        self.assertEqual(self.state.move_direction(), (0, -1))


if __name__ == "__main__":
    unittest.main()
