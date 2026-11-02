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


if __name__ == "__main__":
    unittest.main()
