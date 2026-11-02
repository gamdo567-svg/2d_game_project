import unittest

from game.player.facing import Facing, facing_for_direction, sprite_view


class FacingForDirectionTest(unittest.TestCase):
    def test_no_input_keeps_current(self):
        self.assertEqual(facing_for_direction(0, 0, Facing.LEFT), Facing.LEFT)

    def test_straight_directions(self):
        self.assertEqual(facing_for_direction(0, -1, Facing.UP), Facing.DOWN)
        self.assertEqual(facing_for_direction(0, 1, Facing.DOWN), Facing.UP)
        self.assertEqual(facing_for_direction(1, 0, Facing.DOWN), Facing.RIGHT)
        self.assertEqual(facing_for_direction(-1, 0, Facing.DOWN), Facing.LEFT)

    def test_diagonal_keeps_matching_current(self):
        # 위로 걷다가 오른쪽을 함께 누르면 뒷모습을 유지한다.
        self.assertEqual(facing_for_direction(1, 1, Facing.UP), Facing.UP)
        # 오른쪽으로 걷다가 위를 함께 누르면 측면을 유지한다.
        self.assertEqual(facing_for_direction(1, 1, Facing.RIGHT), Facing.RIGHT)

    def test_diagonal_from_unrelated_facing_uses_side(self):
        self.assertEqual(facing_for_direction(-1, -1, Facing.UP), Facing.LEFT)
        self.assertEqual(facing_for_direction(1, -1, Facing.LEFT), Facing.RIGHT)


class SpriteViewTest(unittest.TestCase):
    def test_views(self):
        self.assertEqual(sprite_view(Facing.DOWN), ("front", False))
        self.assertEqual(sprite_view(Facing.UP), ("back", False))
        self.assertEqual(sprite_view(Facing.RIGHT), ("side", False))
        self.assertEqual(sprite_view(Facing.LEFT), ("side", True))


if __name__ == "__main__":
    unittest.main()
