"""맵 바탕 그림 확인 (2026-11-19 지하 미궁 타일): 기본 맵에 짝지은 그림이 있고 크기가 맵과 같아야 한다.

그림은 assets/concepts/pixellab/labyrinth/build_map_bg.py 가 글자 맵에서 만든다. 맵 글자를 바꾸고 다시 만들지 않으면
크기가 달라 이 테스트가 알려 준다 (칸 수가 같은 채 벽만 옮긴 경우는 잡지 못함).
"""
import os
import struct
import unittest

from game import config
from game.world.tile_map import TileMap


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


class MapBackgroundTest(unittest.TestCase):
    def test_background_matches_map(self):
        path = config.map_background_path(config.FIELD_MAP_PATH)
        self.assertTrue(os.path.exists(path), path)
        tile_map = TileMap.load(config.FIELD_MAP_PATH)
        self.assertEqual(png_size(path), (tile_map.cols * config.LOGICAL_TILE_SIZE,
                                          tile_map.rows * config.LOGICAL_TILE_SIZE))

    def test_walltop_bands_match_map(self):
        # 솟은 벽 윗면: 맵 줄마다 MAP_WALL_OVERHANG 높이의 띠 (build_map_bg.py OVERHANG 과 같아야 함)
        path = config.map_walltop_path(config.FIELD_MAP_PATH)
        self.assertTrue(os.path.exists(path), path)
        tile_map = TileMap.load(config.FIELD_MAP_PATH)
        self.assertEqual(png_size(path), (tile_map.cols * config.LOGICAL_TILE_SIZE,
                                          tile_map.rows * config.MAP_WALL_OVERHANG))

    def test_torches_file_and_sheet(self):
        # 횃불 자리 파일과 불꽃 그림(가로 frames 장)이 서로 맞아야 한다
        from game.scenes.field_scene import load_torches
        info = load_torches(config.map_torches_path(config.FIELD_MAP_PATH))
        self.assertIsNotNone(info)
        self.assertTrue(info["torches"])
        self.assertEqual(png_size(config.MAP_TORCH_SHEET), (info["frame_width"] * info["frames"], info["frame_height"]))
        self.assertTrue(os.path.exists(config.MAP_TORCH_GLOW))

    def test_torch_glow_flickers_within_range(self):
        from game.scenes.field_scene import torch_glow_opacity
        values = [torch_glow_opacity(t / 30, 0) for t in range(90)]
        self.assertTrue(all(0.0 <= v <= 1.0 for v in values))
        self.assertGreater(max(values) - min(values), 0.2)  # 실제로 흔들린다
        self.assertNotEqual(torch_glow_opacity(1.0, 0), torch_glow_opacity(1.0, 1))  # 횃불마다 박자가 다르다

    def test_background_path_follows_map_name(self):
        self.assertTrue(config.map_background_path("x/dungeon_1.txt").endswith(os.path.join("maps", "dungeon_1_bg.png")))


if __name__ == "__main__":
    unittest.main()
