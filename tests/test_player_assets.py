"""주인공 스프라이트 파일이 코드가 기대하는 규격인지 확인한다 (pico2d·Pillow 없이 PNG를 직접 읽음)."""
import struct
import unittest
import zlib

from game import config
from game.player.player import SHADOW_PATH, SPRITE_FALLBACK, sprite_sheet_path
from game.player.state_machine import IDLE, JUMP, STATES, WALK

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


IDLE_FIXED_TOP_ROWS = 19   # 후드·얼굴·어깨 (스프라이트 생성 시 망토 줄은 19~43)
IDLE_FIXED_FEET_ROWS = 4   # 부츠
HEAD_ROWS = 17             # 후드·얼굴·턱
LEG_ROWS = 8
FRAMES = {
    IDLE: config.PLAYER_IDLE_FRAMES,
    WALK: config.PLAYER_WALK_FRAMES,
    JUMP: config.PLAYER_JUMP_FRAMES,
}
AIRBORNE_FRAMES = {(JUMP, 2)}  # 공중에서 발을 당긴 프레임: 발이 바닥 줄에 닿지 않는다


def frames_of(state, view):
    """시트를 프레임별 [y][x] 픽셀 목록으로 나눈다."""
    w = config.PLAYER_SPRITE_WIDTH
    pixels = read_rgba_pixels(sprite_sheet_path(state, view))
    count = len(pixels[0]) // w
    return [[row[i * w:(i + 1) * w] for row in pixels] for i in range(count)]


class PlayerAssetTest(unittest.TestCase):
    def test_sheets_exist_with_expected_size(self):
        frames = FRAMES
        # 상태를 추가하면 FRAMES 도 갱신 (전용 그림이 없는 상태는 SPRITE_FALLBACK)
        self.assertEqual(set(frames) | set(SPRITE_FALLBACK), set(STATES))
        for state in FRAMES:
            expected_width = config.PLAYER_SPRITE_WIDTH * frames[state]
            for view in VIEWS:
                path = sprite_sheet_path(state, view)
                with self.subTest(path=path):
                    signature, width, height, color_type = read_png_header(path)
                    self.assertEqual(signature, PNG_SIGNATURE)
                    self.assertEqual((width, height), (expected_width, config.PLAYER_SPRITE_HEIGHT))
                    self.assertEqual(color_type, COLOR_TYPE_RGBA)  # 투명 배경

    def test_frames_are_clean_and_aligned(self):
        # 발이 맨 아래 줄에 닿아야 idle <-> walk 전환과 프레임 전환 때 위아래로 튀지 않는다.
        # 초록 배경(#00FF00) 제거 후 반투명 경계나 초록 잔여 픽셀이 남으면 안 된다.
        h = config.PLAYER_SPRITE_HEIGHT
        for state in FRAMES:
            for view in VIEWS:
                for index, frame in enumerate(frames_of(state, view)):
                    with self.subTest(state=state, view=view, frame=index):
                        opaque_rows = set()
                        for y, row in enumerate(frame):
                            for r, g, b, a in row:
                                self.assertIn(a, (0, 255))
                                if a:
                                    opaque_rows.add(y)
                                    self.assertLessEqual(g, max(r, b) + 10, "초록 잔여 픽셀")
                        if (state, index) not in AIRBORNE_FRAMES:
                            self.assertEqual(max(opaque_rows), h - 1)

    def test_idle_moves_only_cape(self):
        # Idle: 후드·얼굴·몸통 윗부분과 발은 모든 프레임에서 같은 픽셀 (깜빡임 방지), 망토만 달라진다.
        for view in VIEWS:
            frames = frames_of(IDLE, view)
            with self.subTest(view=view):
                for frame in frames[1:]:
                    self.assertEqual(frame[:IDLE_FIXED_TOP_ROWS], frames[0][:IDLE_FIXED_TOP_ROWS])
                    self.assertEqual(frame[-IDLE_FIXED_FEET_ROWS:], frames[0][-IDLE_FIXED_FEET_ROWS:])
                self.assertGreater(len({tuple(map(tuple, f)) for f in frames}), 1, "망토가 움직이지 않음")

    def test_walk_keeps_idle_head_and_has_distinct_frames(self):
        # Walk: 머리(후드·얼굴)는 Idle 첫 프레임과 같은 그림을 상하 반동만큼만 옮겨 쓴다.
        # 같은 프레임을 복사해 4프레임을 채우지 않았는지 다리 줄을 비교한다.
        for view in VIEWS:
            head = frames_of(IDLE, view)[0]
            top = min(y for y, row in enumerate(head) if any(p[3] for p in row))
            band = head[top:top + HEAD_ROWS]
            walk = frames_of(WALK, view)
            with self.subTest(view=view):
                for index, frame in enumerate(walk):
                    shifts = [dy for dy in range(-2, 3) if frame[top + dy:top + dy + HEAD_ROWS] == band]
                    self.assertTrue(shifts, f"{index}번 프레임 머리 모양이 다름")
                legs = [tuple(map(tuple, f[-LEG_ROWS:])) for f in walk]
                self.assertEqual(len(set(legs)), len(legs), "다리 자세가 같은 프레임이 있음")

    def test_shadow_is_translucent(self):
        signature, width, height, color_type = read_png_header(SHADOW_PATH)
        self.assertEqual((width, height), (config.PLAYER_SHADOW_WIDTH, config.PLAYER_SHADOW_HEIGHT))
        alphas = {p[3] for row in read_rgba_pixels(SHADOW_PATH) for p in row}
        self.assertTrue(any(0 < a < 255 for a in alphas))


if __name__ == "__main__":
    unittest.main()
