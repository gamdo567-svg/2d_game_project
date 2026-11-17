import unittest

from game.player.movement import GridMover
from game.world.grid import Grid

SPEED = 4.0  # 칸/초 -> 한 칸 0.25초


def make_mover(col=5, row=5):
    return GridMover(Grid(10, 8, 32), col, row, SPEED)


def run(mover, seconds, dx, dy, fps=100):
    dt = 1.0 / fps
    for _ in range(round(seconds * fps)):
        mover.update(dt, dx, dy)


class GridMoverTest(unittest.TestCase):
    def test_starts_idle_at_tile(self):
        mover = make_mover()
        self.assertFalse(mover.is_moving)
        self.assertEqual((mover.col, mover.row), (5, 5))
        self.assertEqual(mover.visual_position, (5, 5))

    def test_logical_position_is_integer_target_while_moving(self):
        mover = make_mover()
        mover.update(0.1, 1, 0)
        self.assertTrue(mover.is_moving)
        self.assertEqual((mover.col, mover.row), (6, 5))
        self.assertIsInstance(mover.col, int)

    def test_visual_position_interpolates(self):
        mover = make_mover()
        mover.update(0.125, 1, 0)  # 한 칸(0.25초)의 절반
        col, row = mover.visual_position
        self.assertAlmostEqual(col, 5.5)
        self.assertAlmostEqual(row, 5.0)

    def test_finishes_step_after_release(self):
        mover = make_mover()
        mover.update(0.1, 1, 0)
        mover.update(0.2, 0, 0)  # 키를 떼도 시작한 칸 이동은 끝낸다
        self.assertFalse(mover.is_moving)
        self.assertEqual(mover.visual_position, (6, 5))

    def test_holding_key_moves_continuously(self):
        mover = make_mover(col=0)
        run(mover, 1.1, 1, 0)  # 1.1초 = 4.4칸, 칸 사이에서 멈추지 않는다
        self.assertAlmostEqual(mover.visual_position[0], 4.4, places=6)
        self.assertTrue(mover.is_moving)

    def test_large_dt_carries_over_without_losing_time(self):
        mover = make_mover(col=0)
        mover.update(0.6, 1, 0)  # 2.4칸 분량
        self.assertAlmostEqual(mover.visual_position[0], 2.4, places=6)

    def test_movement_is_fps_independent(self):
        slow, fast = make_mover(col=0), make_mover(col=0)
        run(slow, 0.9, 1, 0, fps=20)
        run(fast, 0.9, 1, 0, fps=240)
        self.assertAlmostEqual(slow.visual_position[0], fast.visual_position[0], places=6)
        self.assertEqual(slow.col, fast.col)

    def test_vertical_move(self):
        mover = make_mover()
        mover.update(0.25, 0, -1)
        self.assertEqual((mover.col, mover.row), (5, 4))
        self.assertFalse(mover.is_moving)

    def test_diagonal_is_rejected(self):
        with self.assertRaises(ValueError):
            make_mover().update(0.1, 1, 1)

    def test_move_direction(self):
        mover = make_mover()
        self.assertEqual(mover.move_direction, (0, 0))
        mover.update(0.1, -1, 0)
        self.assertEqual(mover.move_direction, (-1, 0))

    def test_cannot_leave_grid(self):
        mover = make_mover(col=0, row=0)
        run(mover, 1.0, -1, 0)
        run(mover, 1.0, 0, -1)
        self.assertEqual((mover.col, mover.row), (0, 0))
        self.assertFalse(mover.is_moving)

    def test_stops_at_far_edge(self):
        mover = make_mover(col=7, row=7)
        run(mover, 2.0, 1, 0)
        self.assertEqual((mover.col, mover.row), (9, 7))  # 10x8 격자의 끝
        run(mover, 1.0, 0, 1)
        self.assertEqual((mover.col, mover.row), (9, 7))

    def test_invalid_start(self):
        with self.assertRaises(ValueError):
            GridMover(Grid(10, 8, 32), 10, 0, SPEED)
        with self.assertRaises(ValueError):
            GridMover(Grid(10, 8, 32), 0, 0, 0)


if __name__ == "__main__":
    unittest.main()


class TurnWhileWalkingTest(unittest.TestCase):
    """걷는 중 방향 바꾸기 (조작감): 반대는 바로, 옆은 칸을 마친 뒤 (사선 금지)."""

    SPEED = 4.0

    def setUp(self):
        self.mover = GridMover(Grid(10, 10, 32), 5, 5, speed=self.SPEED)
        self.mover.update(0.25 / 4, 1, 0)  # 오른쪽으로 한 칸의 1/4

    def test_reverse_turns_back_immediately(self):
        self.mover.update(1e-6, -1, 0)
        self.assertEqual(self.mover.move_direction, (-1, 0))
        self.assertEqual((self.mover.col, self.mover.row), (5, 5))  # 떠나온 칸으로
        self.assertAlmostEqual(self.mover.visual_position[0], 5.25, places=3)  # 그림은 튀지 않음
        self.mover.update(0.25 / 4 + 0.001, 0, 0)  # 남은 1/4칸만큼 시간
        self.assertFalse(self.mover.is_moving)
        self.assertEqual(self.mover.visual_position, (5, 5))

    def test_side_turn_waits_for_tile_no_diagonal(self):
        # 옆 방향은 칸 사이에서 바로 꺾지 않는다 (사선 이동 방지). 칸을 마친 뒤 꺾는다
        for _ in range(10):
            self.mover.update(0.01, 0, 1)
            x, y = self.mover.visual_position
            self.assertTrue(x == round(x) or y == round(y))  # 언제나 가로줄 또는 세로줄 위
        self.mover.update(0.25, 0, 1)
        self.assertEqual(self.mover.col, 6)
        self.assertGreater(self.mover.row, 5)

    def test_blocked_turn_keeps_going(self):
        blocked = set()
        mover = GridMover(Grid(10, 10, 32), 5, 5, speed=self.SPEED, can_enter=lambda c, r: (c, r) not in blocked)
        mover.update(0.25 / 4, 1, 0)
        blocked.add((5, 5))  # 떠나온 칸에 무언가 들어옴
        mover.update(1e-6, -1, 0)  # 되돌아갈 칸이 막혀 있으면 그대로 감
        self.assertEqual(mover.move_direction, (1, 0))
