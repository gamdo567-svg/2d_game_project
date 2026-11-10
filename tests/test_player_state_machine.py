import unittest

from transitions import MachineError

from game.player.state_machine import IDLE, JUMP, PARRY, STATES, WALK, PlayerStateMachine


class PlayerStateMachineTest(unittest.TestCase):
    def test_states(self):
        self.assertEqual(STATES, [IDLE, WALK, JUMP, PARRY])

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

    def test_jump_and_parry_from_idle_or_walk(self):
        for start_walking in (False, True):
            for trigger, state, end in (("jump", JUMP, "land"), ("parry", PARRY, "end_parry")):
                with self.subTest(walking=start_walking, trigger=trigger):
                    fsm = PlayerStateMachine()
                    fsm.update_movement(start_walking)
                    fsm.trigger(trigger)
                    self.assertEqual(fsm.state, state)
                    fsm.trigger(end)
                    self.assertEqual(fsm.state, IDLE)

    def test_no_new_action_during_jump(self):
        fsm = PlayerStateMachine()
        fsm.trigger("jump")
        for trigger in ("parry", "jump", "start_walk"):
            with self.assertRaises(MachineError):
                fsm.trigger(trigger)
        fsm.update_movement(True)  # 점프 중에는 idle/walk 전환을 하지 않는다
        self.assertEqual(fsm.state, JUMP)

    def test_no_auto_transitions(self):
        self.assertFalse(hasattr(PlayerStateMachine(), "to_walk"))


if __name__ == "__main__":
    unittest.main()
