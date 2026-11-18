"""칸 레이캐스트 테스트 (2026-11-18: 골렘 레이저가 벽을 통과하지 않게)."""
import unittest

from game.physics.raycast import first_open_stop


def walls(*tiles):
    s = set(tiles)
    return lambda c, r: (c, r) in s


class FirstOpenStopTest(unittest.TestCase):
    def test_no_wall_reaches_end(self):
        self.assertEqual(first_open_stop((0.5, 0.5), (5.5, 2.5), walls()), ((5.5, 2.5), False))

    def test_stops_in_front_of_wall_horizontal(self):
        self.assertEqual(first_open_stop((0.5, 0.5), (6.5, 0.5), walls((3, 0))), ((2.5, 0.5), True))

    def test_stops_in_front_of_wall_diagonal(self):
        point, blocked = first_open_stop((0.5, 0.5), (6.5, 6.5), walls((4, 4)))
        self.assertTrue(blocked)
        self.assertLess(point[0], 4)  # 벽 칸 (4,4) 앞

    def test_wall_beyond_end_does_not_block(self):
        self.assertEqual(first_open_stop((0.5, 0.5), (2.5, 0.5), walls((3, 0))), ((2.5, 0.5), False))

    def test_leftward_and_downward(self):
        self.assertEqual(first_open_stop((6.5, 6.5), (0.5, 6.5), walls((2, 6))), ((3.5, 6.5), True))
        self.assertEqual(first_open_stop((1.5, 6.5), (1.5, 0.5), walls((1, 3))), ((1.5, 4.5), True))


if __name__ == "__main__":
    unittest.main()
