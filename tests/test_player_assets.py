"""주인공 스프라이트 파일이 코드가 기대하는 규격인지 확인한다 (pico2d 없이 PNG 헤더만 읽음)."""
import struct
import unittest

from game import config
from game.player.player import sprite_sheet_path
from game.player.state_machine import STATES

VIEWS = ("front", "back", "side")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
COLOR_TYPE_RGBA = 6


def read_png_header(path):
    with open(path, "rb") as f:
        data = f.read(26)
    width, height = struct.unpack(">II", data[16:24])
    return data[:8], width, height, data[25]


class PlayerAssetTest(unittest.TestCase):
    def test_sheets_exist_with_expected_size(self):
        expected_width = config.PLAYER_SPRITE_WIDTH * config.PLAYER_ANIMATION_FRAMES
        for state in STATES:
            for view in VIEWS:
                path = sprite_sheet_path(state, view)
                with self.subTest(path=path):
                    signature, width, height, color_type = read_png_header(path)
                    self.assertEqual(signature, PNG_SIGNATURE)
                    self.assertEqual((width, height), (expected_width, config.PLAYER_SPRITE_HEIGHT))
                    self.assertEqual(color_type, COLOR_TYPE_RGBA)  # 투명 배경


if __name__ == "__main__":
    unittest.main()
