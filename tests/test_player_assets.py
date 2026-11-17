"""주인공 스프라이트 파일이 코드가 기대하는 규격인지 확인한다 (pico2d·Pillow 없이 PNG를 직접 읽음)."""
import struct
import unittest
import zlib

from game import config
from game.player.player import (LEFT_SHEET_STATES, SHADOW_PATH, SPRITE_FALLBACK, attack_hand_sheet_path,
                               attack_sheet_path, sprite_sheet_path, weapon_sheet_path)
from game.player.state_machine import ATTACK, IDLE, JUMP, STATES, WALK

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
FRAMES = {
    IDLE: config.PLAYER_IDLE_FRAMES,
    WALK: config.PLAYER_WALK_FRAMES,
    JUMP: config.PLAYER_JUMP_FRAMES,
}
# 공중 프레임(도약 ~ 내려옴): 발이 바닥 줄에 닿지 않아도 된다 (2026-11-17 PixelLab 점프)
AIRBORNE_FRAMES = {(JUMP, i) for i in range(config.PLAYER_JUMP_TAKEOFF_FRAMES,
                                             config.PLAYER_JUMP_FRAMES - config.PLAYER_JUMP_LANDING_FRAMES)}
HEAD_ROWS = 17             # 후드·얼굴·턱
LEG_ROWS = 8


def views_of(state):
    """상태가 가진 원본 방향. 좌우 비대칭 상태는 왼쪽 전용 그림(side_left)도 있다."""
    return VIEWS + (("side_left",) if state in LEFT_SHEET_STATES else ())


def frame_width(state):
    return config.PLAYER_JUMP_SPRITE_WIDTH if state == JUMP else config.PLAYER_SPRITE_WIDTH


def frame_height(state):
    return config.PLAYER_JUMP_SPRITE_HEIGHT if state == JUMP else config.PLAYER_SPRITE_HEIGHT


def frames_of(state, view):
    """시트를 프레임별 [y][x] 픽셀 목록으로 나눈다."""
    w = frame_width(state)
    pixels = read_rgba_pixels(sprite_sheet_path(state, view))
    count = len(pixels[0]) // w
    return [[row[i * w:(i + 1) * w] for row in pixels] for i in range(count)]


class PlayerAssetTest(unittest.TestCase):
    def test_sheets_exist_with_expected_size(self):
        frames = FRAMES
        # 상태를 추가하면 FRAMES 도 갱신 (전용 그림이 없는 상태는 SPRITE_FALLBACK, 공격은 따로 검사)
        self.assertEqual(set(frames) | set(SPRITE_FALLBACK) | {ATTACK}, set(STATES))
        for state in FRAMES:
            expected_width = frame_width(state) * frames[state]
            for view in views_of(state):
                path = sprite_sheet_path(state, view)
                with self.subTest(path=path):
                    signature, width, height, color_type = read_png_header(path)
                    self.assertEqual(signature, PNG_SIGNATURE)
                    self.assertEqual((width, height), (expected_width, frame_height(state)))
                    self.assertEqual(color_type, COLOR_TYPE_RGBA)  # 투명 배경

    def test_frames_are_clean_and_aligned(self):
        # 발이 맨 아래 줄에 닿아야 idle <-> walk 전환과 프레임 전환 때 위아래로 튀지 않는다.
        # 초록 배경(#00FF00) 제거 후 반투명 경계나 초록 잔여 픽셀이 남으면 안 된다.
        for state in FRAMES:
            h = frame_height(state)
            for view in views_of(state):
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

    def attack_frames(self, hit):
        w = config.PLAYER_ATTACK_SPRITE_WIDTH
        pixels = read_rgba_pixels(attack_sheet_path(hit))
        return [[row[i * w:(i + 1) * w] for row in pixels] for i in range(config.PLAYER_ATTACK_FRAMES)]

    def test_attack_sheets(self):
        # 콤보 타마다 96×64 캔버스 8프레임, 오른쪽 측면만. 발끝 줄이 모든 프레임에서 같다.
        # 반투명 픽셀은 휘두른 잔상(밝은 흰색)뿐이다.
        w, h = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        foot_row = h - 1 - config.PLAYER_ATTACK_FOOT_MARGIN
        for hit in range(1, config.PLAYER_ATTACK_HITS + 1):
            signature, width, height, color_type = read_png_header(attack_sheet_path(hit))
            with self.subTest(hit=hit):
                self.assertEqual((width, height), (w * config.PLAYER_ATTACK_FRAMES, h))
                self.assertEqual(color_type, COLOR_TYPE_RGBA)
            for index, frame in enumerate(self.attack_frames(hit)):
                with self.subTest(hit=hit, frame=index):
                    self.assertTrue(all(min(p[:3]) >= 200 for row in frame for p in row if 0 < p[3] < 255))
                    # 발 줄에는 그림이 있고, 그 아래로는 칼끝만 몇 줄 내려갈 수 있다
                    self.assertTrue(any(p[3] for p in frame[foot_row]))
                    rows_below = [row for row in frame[foot_row + 1:] if any(p[3] for p in row)]
                    self.assertLessEqual(len(rows_below), 3)

    def test_attack_hand_sheets_match_body_sheets(self):
        # 칼 앞 레이어(칼을 쥔 손): 몸 시트와 같은 크기, 그림은 손 둘레에만 있다.
        # 칼이 몸 뒤인 프레임은 비어 있고, 칼이 앞인 프레임은 대부분 손이 있다.
        w, h = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        for hit in range(1, config.PLAYER_ATTACK_HITS + 1):
            path = attack_hand_sheet_path(hit)
            signature, width, height, color_type = read_png_header(path)
            self.assertEqual((width, height), (w * config.PLAYER_ATTACK_FRAMES, h))
            pixels = read_rgba_pixels(path)
            front_frames = with_hand = 0
            for i in range(config.PLAYER_ATTACK_FRAMES):
                hand_x, hand_y, _, behind = config.PLAYER_ATTACK_SWORD[hit - 1][i][:4]
                opaque = [(x, y) for y in range(h) for x in range(w) if pixels[y][i * w + x][3]]
                with self.subTest(hit=hit, frame=i):
                    self.assertTrue(all(abs(x - hand_x) <= 4 and abs(y - hand_y) <= 4 for x, y in opaque))
                    if behind:
                        self.assertEqual(opaque, [])
                    else:
                        front_frames += 1
                        with_hand += bool(opaque)
            with self.subTest(hit=hit):
                self.assertGreaterEqual(with_hand * 2, front_frames)

    def test_front_attack_sheets_and_tables(self):
        # 정면 공격: 1타는 PixelLab 8프레임, 2·3타는 예전 5프레임 그림 (프레임 표·그림 옮김·칼 길이 비율이 따로 있음).
        # 후면은 그림이 없어 표가 모두 None (위를 볼 때 측면 그림).
        w, h = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        self.assertEqual(len(config.PLAYER_ATTACK_SWORD_FRONT), config.PLAYER_ATTACK_HITS)
        for index, frames in enumerate(config.PLAYER_ATTACK_SWORD_FRONT):
            hit = index + 1
            ends = config.PLAYER_ATTACK_FRAME_ENDS_FRONT[index]
            count = config.PLAYER_ATTACK_FRAMES if ends is None else len(ends)
            with self.subTest(hit=hit):
                self.assertEqual(len(frames), count)
                if ends is not None:
                    self.assertEqual(list(ends), sorted(ends))
                    self.assertEqual(ends[-1], 1.0)
                    self.assertEqual(len(config.PLAYER_ATTACK_FRAME_SHIFTS_FRONT[index]), count)
                for path in (attack_sheet_path(hit, "front"), attack_hand_sheet_path(hit, "front")):
                    signature, width, height, color_type = read_png_header(path)
                    self.assertEqual((width, height), (w * count, h))
                for hand_x, hand_y, angle, behind, *rest in frames:
                    self.assertTrue(0 <= hand_x < w and 0 <= hand_y < h)
                    self.assertTrue(all(0 <= length <= 1.0 for length in rest))  # 0 = 칼이 몸 그림에 들어 있음
        self.assertEqual(config.PLAYER_ATTACK_SWORD_BACK, (None, None, None))

    def test_front_big_swing_frame_starts_at_hit_time(self):
        # 정면은 크게 휘두르거나 찌르는 그림(1타 6번째, 2타 5번째, 3타 6번째)이 판정이 나는 순간에 시작한다 (측면과 같은 박자)
        from game.player.actions import frame_for_progress
        for index, swing in ((0, 5), (1, 4), (2, 5)):
            hit_progress = config.PLAYER_ATTACK_HIT_FRAMES[index] / config.PLAYER_ATTACK_FRAMES
            ends = config.PLAYER_ATTACK_FRAME_ENDS_FRONT[index]
            with self.subTest(hit=index + 1):
                self.assertEqual(frame_for_progress(hit_progress, ends), swing)
                self.assertLess(frame_for_progress(hit_progress - 0.01, ends), swing)

    def test_attack_timing_tables_match_hits(self):
        self.assertEqual(len(config.PLAYER_ATTACK_DURATIONS), config.PLAYER_ATTACK_HITS)
        self.assertEqual(len(config.PLAYER_ATTACK_FRAME_ENDS), config.PLAYER_ATTACK_HITS)
        self.assertEqual(len(config.PLAYER_ATTACK_FRAME_SHIFTS), config.PLAYER_ATTACK_HITS)
        for ends, shifts in zip(config.PLAYER_ATTACK_FRAME_ENDS, config.PLAYER_ATTACK_FRAME_SHIFTS):
            self.assertEqual(len(ends), config.PLAYER_ATTACK_FRAMES)
            self.assertEqual(len(shifts), config.PLAYER_ATTACK_FRAMES)
            self.assertEqual(shifts[-1], (0, 0))  # 마지막 프레임은 제자리

    def test_weapon_is_one_image_with_hand_at_center(self):
        # 칼 그림은 한 장: 칼끝이 오른쪽, 한가운데(손)에 주먹이 있고, 투명/불투명만 쓴다.
        w, h = config.PLAYER_SWORD_SPRITE_WIDTH, config.PLAYER_SWORD_SPRITE_HEIGHT
        path = weapon_sheet_path(config.PLAYER_WEAPON)
        signature, width, height, color_type = read_png_header(path)
        self.assertEqual((width, height), (w, h))
        self.assertEqual(color_type, COLOR_TYPE_RGBA)
        pixels = read_rgba_pixels(path)
        self.assertTrue(all(p[3] in (0, 255) for row in pixels for p in row))
        self.assertEqual(pixels[h // 2][w // 2][3], 255)
        right = sum(1 for row in pixels for p in row[w // 2:] if p[3])
        left = sum(1 for row in pixels for p in row[:w // 2] if p[3])
        self.assertGreater(right, left * 2)  # 칼날은 손 오른쪽

    def test_attack_sword_table_matches_frames(self):
        self.assertEqual(len(config.PLAYER_ATTACK_SWORD), config.PLAYER_ATTACK_HITS)
        for hit in config.PLAYER_ATTACK_SWORD:
            self.assertEqual(len(hit), config.PLAYER_ATTACK_FRAMES)
            for hand_x, hand_y, angle, behind in hit:
                self.assertTrue(0 <= hand_x < config.PLAYER_ATTACK_SPRITE_WIDTH)
                self.assertTrue(0 <= hand_y < config.PLAYER_ATTACK_SPRITE_HEIGHT)
                self.assertTrue(-180 <= angle <= 180)
                self.assertIsInstance(behind, bool)

    def test_shadow_is_translucent(self):
        signature, width, height, color_type = read_png_header(SHADOW_PATH)
        self.assertEqual((width, height), (config.PLAYER_SHADOW_WIDTH, config.PLAYER_SHADOW_HEIGHT))
        alphas = {p[3] for row in read_rgba_pixels(SHADOW_PATH) for p in row}
        self.assertTrue(any(0 < a < 255 for a in alphas))


if __name__ == "__main__":
    unittest.main()
