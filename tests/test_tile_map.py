"""글자 맵(TileMap)과 칸 충돌 판정 테스트 (pico2d 없이)."""
import unittest

from game import config
from game.physics.collision import can_enter
from game.player.movement import GridMover
from game.world.grid import Grid
from game.world.tile_map import TileMap

SMALL = """
#####
#.P.#
#.#.#
#####
"""


class TileMapTest(unittest.TestCase):
    def test_top_line_is_highest_row(self):
        # 파일 맨 위 줄 = 가장 위쪽 행, (0, 0) = 왼쪽 아래 칸
        tile_map = TileMap.from_text(SMALL)
        self.assertEqual((tile_map.cols, tile_map.rows), (5, 4))
        self.assertEqual(tile_map.player_start, (2, 2))
        self.assertTrue(tile_map.is_wall(2, 1))   # 셋째 줄 가운데 '#'
        self.assertFalse(tile_map.is_wall(1, 1))
        self.assertTrue(tile_map.is_wall(0, 0))

    def test_outside_is_wall(self):
        tile_map = TileMap.from_text(SMALL)
        for col, row in ((-1, 1), (5, 1), (1, -1), (1, 4)):
            self.assertTrue(tile_map.is_wall(col, row))

    def test_rejects_bad_maps(self):
        for text in ("", "##\n#", "#x#", "P.P"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                TileMap.from_text(text)

    def test_field_map_file_matches_grid(self):
        # 게임에서 쓰는 맵: 격자와 같은 크기, 시작 칸은 바닥, 바깥 테두리는 벽
        tile_map = TileMap.load(config.FIELD_MAP_PATH)
        self.assertEqual((tile_map.cols, tile_map.rows), (config.GRID_COLS, config.GRID_ROWS))
        self.assertIsNotNone(tile_map.player_start)
        self.assertFalse(tile_map.is_wall(*tile_map.player_start))
        for col in range(tile_map.cols):
            self.assertTrue(tile_map.is_wall(col, 0) and tile_map.is_wall(col, tile_map.rows - 1))
        for row in range(tile_map.rows):
            self.assertTrue(tile_map.is_wall(0, row) and tile_map.is_wall(tile_map.cols - 1, row))


class CollisionTest(unittest.TestCase):
    def setUp(self):
        self.tile_map = TileMap.from_text(SMALL)
        self.grid = Grid(self.tile_map.cols, self.tile_map.rows, 32)

    def test_can_enter_floor_only(self):
        self.assertTrue(can_enter(self.tile_map, 1, 2))
        self.assertFalse(can_enter(self.tile_map, 2, 1))   # 벽
        self.assertFalse(can_enter(self.tile_map, -1, 2))  # 맵 밖

    def make_mover(self):
        return GridMover(self.grid, 2, 2, speed=6.0, can_enter=lambda c, r: can_enter(self.tile_map, c, r))

    def test_mover_stops_at_wall(self):
        mover = self.make_mover()
        mover.update(1.0, 0, -1)  # 아래는 벽
        self.assertEqual((mover.col, mover.row), (2, 2))
        self.assertFalse(mover.is_moving)

    def test_mover_walks_until_wall(self):
        mover = self.make_mover()
        mover.update(1.0, 1, 0)  # 오른쪽으로 1초: 한 칸 간 뒤 벽에 막힘
        self.assertEqual((mover.col, mover.row), (3, 2))
        self.assertFalse(mover.is_moving)
        mover.update(1.0, 0, -1)  # 그 칸에서 아래는 바닥
        self.assertEqual((mover.col, mover.row), (3, 1))


if __name__ == "__main__":
    unittest.main()
