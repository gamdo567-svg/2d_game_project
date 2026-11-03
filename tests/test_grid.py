import unittest

from game import config
from game.world.grid import Grid


class GridTest(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(cols=10, rows=8, tile_size=32)

    def test_size_in_pixels(self):
        self.assertEqual(self.grid.width_px, 320)
        self.assertEqual(self.grid.height_px, 256)

    def test_origin_tile_is_bottom_left(self):
        self.assertEqual(self.grid.tile_to_pixel_rect(0, 0), (0, 0, 32, 32))
        self.assertEqual(self.grid.tile_to_pixel(0, 0), (16, 16))

    def test_tile_to_pixel_center(self):
        self.assertEqual(self.grid.tile_to_pixel(3, 2), (3 * 32 + 16, 2 * 32 + 16))

    def test_tile_to_pixel_accepts_fractional_tiles(self):
        # 칸 사이를 보간해서 그릴 때 사용
        x, y = self.grid.tile_to_pixel(2.5, 0)
        self.assertEqual((x, y), (2.5 * 32 + 16, 16))

    def test_pixel_to_tile(self):
        self.assertEqual(self.grid.pixel_to_tile(0, 0), (0, 0))
        self.assertEqual(self.grid.pixel_to_tile(31.9, 31.9), (0, 0))
        self.assertEqual(self.grid.pixel_to_tile(32, 32), (1, 1))
        self.assertEqual(self.grid.pixel_to_tile(-1, -1), (-1, -1))

    def test_round_trip_for_every_tile(self):
        for col in range(self.grid.cols):
            for row in range(self.grid.rows):
                x, y = self.grid.tile_to_pixel(col, row)
                self.assertEqual(self.grid.pixel_to_tile(x, y), (col, row))

    def test_origin_offset(self):
        grid = Grid(cols=4, rows=4, tile_size=16, origin_x=100, origin_y=50)
        self.assertEqual(grid.tile_to_pixel(0, 0), (108, 58))
        self.assertEqual(grid.pixel_to_tile(100, 50), (0, 0))
        self.assertEqual(grid.pixel_to_tile(99, 50), (-1, 0))

    def test_in_bounds(self):
        self.assertTrue(self.grid.in_bounds(0, 0))
        self.assertTrue(self.grid.in_bounds(9, 7))
        self.assertFalse(self.grid.in_bounds(10, 0))
        self.assertFalse(self.grid.in_bounds(0, 8))
        self.assertFalse(self.grid.in_bounds(-1, 0))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            Grid(cols=0, rows=1, tile_size=32)
        with self.assertRaises(ValueError):
            Grid(cols=1, rows=1, tile_size=0)

    def test_render_sizes_follow_scale(self):
        # 표시 크기는 논리(원본) 크기 × RENDER_SCALE 로만 정해진다.
        scale = config.RENDER_SCALE
        self.assertEqual(config.RENDER_TILE_SIZE, config.LOGICAL_TILE_SIZE * scale)
        self.assertEqual(config.PLAYER_RENDER_WIDTH, config.PLAYER_SPRITE_WIDTH * scale)
        self.assertEqual(config.PLAYER_RENDER_HEIGHT, config.PLAYER_SPRITE_HEIGHT * scale)

    def test_confirmed_screen_and_player_art_dimensions(self):
        self.assertEqual((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), (1024, 576))
        self.assertEqual((config.GRID_COLS, config.GRID_ROWS), (32, 18))
        self.assertEqual((config.PLAYER_SPRITE_WIDTH, config.PLAYER_SPRITE_HEIGHT), (32, 48))
        # 2026-11-03: 화면 표시 2배 확대
        self.assertEqual((config.LOGICAL_TILE_SIZE, config.RENDER_TILE_SIZE), (32, 64))
        self.assertEqual((config.PLAYER_RENDER_WIDTH, config.PLAYER_RENDER_HEIGHT), (64, 96))
        self.assertEqual((config.VIEW_COLS, config.VIEW_ROWS), (16, 9))


if __name__ == "__main__":
    unittest.main()
