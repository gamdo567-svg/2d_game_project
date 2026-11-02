import unittest

from game.player.movement import GridMover
from game.world.grid import Grid

SPEED = 4.0  # 칸/초 -> 한 칸 0.25초


def make_mover(col=5, row=5, diagonal_time_scale=1.0):
    return GridMover(Grid(10, 8, 32), col, row, SPEED, diagonal_time_scale)


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

    def test_diagonal_move(self):
        mover = make_mover()
        mover.update(0.25, -1, 1)
        self.assertEqual((mover.col, mover.row), (4, 6))
        self.assertFalse(mover.is_moving)

    def test_diagonal_time_scale(self):
        mover = make_mover(diagonal_time_scale=2.0)
        mover.update(0.25, 1, 1)
        self.assertTrue(mover.is_moving)  # 직선의 2배(0.5초)가 걸린다
        self.assertAlmostEqual(mover.visual_position[0], 5.5)

    def test_move_direction(self):
        mover = make_mover()
        self.assertEqual(mover.move_direction, (0, 0))
        mover.update(0.1, -1, -1)
        self.assertEqual(mover.move_direction, (-1, -1))

    def test_cannot_leave_grid(self):
        mover = make_mover(col=0, row=0)
        run(mover, 1.0, -1, -1)
        self.assertEqual((mover.col, mover.row), (0, 0))
        self.assertFalse(mover.is_moving)

    def test_stops_at_far_edge(self):
        mover = make_mover(col=7, row=7)
        run(mover, 2.0, 1, 1)
        self.assertEqual((mover.col, mover.row), (9, 7))  # 10x8 격자의 끝

    def test_diagonal_slides_along_edge(self):
        mover = make_mover(col=3, row=0)
        mover.update(0.25, 1, -1)  # 아래는 막혔으므로 오른쪽으로만
        self.assertEqual((mover.col, mover.row), (4, 0))

    def test_invalid_start(self):
        with self.assertRaises(ValueError):
            GridMover(Grid(10, 8, 32), 10, 0, SPEED)
        with self.assertRaises(ValueError):
            GridMover(Grid(10, 8, 32), 0, 0, 0)


if __name__ == "__main__":
    unittest.main()
