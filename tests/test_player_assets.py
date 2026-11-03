"""주인공 스프라이트 파일이 코드가 기대하는 규격인지 확인한다 (pico2d·Pillow 없이 PNG를 직접 읽음)."""
import struct
import unittest
import zlib

from game import config
from game.player.player import sprite_sheet_path
from game.player.state_machine import IDLE, STATES, WALK

VIEWS = ("front", "back", "side")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
COLOR_TYPE_RGBA = 6


def read_png_header(path):
    with open(path, "rb") as f:
        data = f.read(26)
    width, height = struct.unpack(">II", data[16:24])
    return data[:8], width, height, data[25]


def read_rgba_pixels(path):
    """8비트 RGBA, 비인터레이스 PNG를 [y][x] = (r, g, b, a) 목록으로 읽는다."""
    with open(path, "rb") as f:
        data = f.read()
    pos, idat = 8, b""
    width = height = 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", body)
            assert (bit_depth, color_type, interlace) == (8, COLOR_TYPE_RGBA, 0)
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 4
    rows, prev = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        filter_type, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            left = line[i - 4] if i >= 4 else 0
            up = prev[i]
            up_left = prev[i - 4] if i >= 4 else 0
            if filter_type == 1:
                line[i] = (line[i] + left) & 0xFF
            elif filter_type == 2:
                line[i] = (line[i] + up) & 0xFF
            elif filter_type == 3:
                line[i] = (line[i] + (left + up) // 2) & 0xFF
            elif filter_type == 4:
                p = left + up - up_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                pred = left if pa <= pb and pa <= pc else (up if pb <= pc else up_left)
                line[i] = (line[i] + pred) & 0xFF
        rows.append([tuple(line[x * 4:x * 4 + 4]) for x in range(width)])
        prev = line
    return rows


class PlayerAssetTest(unittest.TestCase):
    def test_sheets_exist_with_expected_size(self):
        frames = {IDLE: config.PLAYER_IDLE_FRAMES, WALK: config.PLAYER_WALK_FRAMES}
        self.assertEqual(set(frames), set(STATES))  # 상태를 추가하면 여기도 갱신
        for state in STATES:
            expected_width = config.PLAYER_SPRITE_WIDTH * frames[state]
            for view in VIEWS:
                path = sprite_sheet_path(state, view)
                with self.subTest(path=path):
                    signature, width, height, color_type = read_png_header(path)
                    self.assertEqual(signature, PNG_SIGNATURE)
                    self.assertEqual((width, height), (expected_width, config.PLAYER_SPRITE_HEIGHT))
                    self.assertEqual(color_type, COLOR_TYPE_RGBA)  # 투명 배경


    def test_walk_frames_are_clean_and_aligned(self):
        # 발이 맨 아래 줄에 닿아야 idle <-> walk 전환과 프레임 전환 때 위아래로 튀지 않는다.
        # 초록 배경(#00FF00) 제거 후 반투명 경계나 초록 잔여 픽셀이 남으면 안 된다.
        w, h = config.PLAYER_SPRITE_WIDTH, config.PLAYER_SPRITE_HEIGHT
        for view in VIEWS:
            pixels = read_rgba_pixels(sprite_sheet_path(WALK, view))
            for frame in range(config.PLAYER_WALK_FRAMES):
                with self.subTest(view=view, frame=frame):
                    opaque_rows = set()
                    for y in range(h):
                        for x in range(frame * w, (frame + 1) * w):
                            r, g, b, a = pixels[y][x]
                            self.assertIn(a, (0, 255))
                            if a:
                                opaque_rows.add(y)
                                self.assertLessEqual(g, max(r, b) + 10, "초록 잔여 픽셀")
                    self.assertEqual(max(opaque_rows), h - 1)


if __name__ == "__main__":
    unittest.main()
