import unittest

from transitions import MachineError

from game.player.state_machine import IDLE, STATES, WALK, PlayerStateMachine


class PlayerStateMachineTest(unittest.TestCase):
    def test_states(self):
        self.assertEqual(STATES, [IDLE, WALK])

    def test_starts_idle(self):
        self.assertEqual(PlayerStateMachine().state, IDLE)

    def test_walk_and_back_to_idle(self):
        fsm = PlayerStateMachine()
        fsm.update_movement(True)
        self.assertEqual(fsm.state, WALK)
        fsm.update_movement(True)
        self.assertEqual(fsm.state, WALK)
        fsm.update_movement(False)
        self.assertEqual(fsm.state, IDLE)

    def test_callback_on_state_change_only(self):
        changes = []
        fsm = PlayerStateMachine(on_state_changed=changes.append)
        fsm.update_movement(False)  # 이미 idle: 전환 없음
        fsm.update_movement(True)
        fsm.update_movement(True)
        fsm.update_movement(False)
        self.assertEqual(changes, [WALK, IDLE])

    def test_invalid_transition_is_rejected(self):
        fsm = PlayerStateMachine()
        with self.assertRaises(MachineError):
            fsm.trigger("stop_walk")  # idle 에서는 stop_walk 불가

    def test_no_auto_transitions(self):
        self.assertFalse(hasattr(PlayerStateMachine(), "to_walk"))


if __name__ == "__main__":
    unittest.main()
