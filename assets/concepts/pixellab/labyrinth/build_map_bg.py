"""지하 미궁 맵 바탕 그림 만들기 (2026-11-19 사용자 요청: 첫 스테이지는 지하 미궁, 낡은 돌 미궁, 벽은 비스듬히(3/4) 보이게).

글자 맵(assets/maps/<이름>.txt)을 읽어 칸마다 PixelLab 타일(tiles_v1, 32×32)을 골라 맵 크기의 그림 한 장으로 합친다.
게임은 이 그림을 바닥에 한 번 그린다 (게임에는 PIL 이 필요 없음). 맵 글자를 바꾸면 이 스크립트를 다시 돌린다.

칸 규칙 (그림이 충돌 칸과 정확히 겹치게 칸 안에서만 그린다):
  - 바닥: 바닥 타일 8종 중 칸 좌표로 정해지는 것 (같은 맵이면 늘 같은 그림). 이끼·웅덩이·꺼진 판은 드물게.
  - 벽: 아래 칸이 바닥이면 '앞에서 보이는 벽' → 위 FACE_TOP 줄은 벽 윗면, 그 아래는 벽돌 앞면(3/4 시점).
    아래도 벽이면 벽 윗면만.
  - 벽 윗면이 바닥과 닿는 가장자리에는 어두운 테두리, 벽 바로 아래·옆 바닥에는 그늘.
출력: assets/images/maps/<이름>_bg.png (맵 칸 수 × 32 픽셀), 미리보기 preview_<이름>_x2.png
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
TILES = os.path.join(HERE, 'tiles_v1')
T = 32
FACE_TOP = 6  # 앞에서 보이는 벽에서 윗면이 차지하는 줄 수 (나머지는 벽돌 앞면). 12 는 벽이 주인공 허리보다 낮아 보였음

# tiles_v1 번호 (0 부터): 바닥 0~7, 벽 윗면 8·9, 벽돌 앞면 10~14 (15 는 쓰지 않음: 뿌리가 지저분함)
FLOOR = [(0, 30), (6, 10), (1, 8), (3, 6), (7, 3), (2, 1), (5, 1), (4, 1)]  # (타일, 비중): 기본 판이 대부분, 이끼·웅덩이·꺼짐은 드물게
WALL_TOP = [(8, 6), (9, 2)]
WALL_FACE = [(14, 6), (10, 4), (11, 2), (12, 1), (13, 1)]
RIM = (14, 15, 20, 255)
FLOOR_DARK = 0.82  # 지하라 바닥을 조금 어둡게
WALL_TOP_DARK = 0.5  # 벽 윗면은 어둡게 (바닥과 구분되게, 위에서 내려다본 벽 꼭대기는 빛을 덜 받음)


def lum_mean(im):
    px = [p for p in im.get_flattened_data() if p[3]]
    return sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px) / len(px)


def match_brightness(tile, target):
    """바닥 변형들의 평균 밝기를 기본 판과 같게 (바둑판처럼 보이지 않게)."""
    f = target / lum_mean(tile)
    out = tile.copy()
    shade(out, (0, 0, T, T), f)
    return out


def pick(choices, col, row, salt):
    """칸 좌표로 정해지는 고르기 (무작위처럼 보이지만 늘 같음)."""
    h = (col * 73856093) ^ (row * 19349663) ^ (salt * 83492791)
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    total = sum(w for _, w in choices)
    r = h % total
    for idx, w in choices:
        if r < w:
            return idx
        r -= w
    return choices[-1][0]


def shade(img, box, factor):
    """box 안 픽셀을 factor 배로 어둡게."""
    px = img.load()
    x0, y0, x1, y1 = box
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            r, g, b, a = px[x, y]
            px[x, y] = (min(255, round(r * factor)), min(255, round(g * factor)), min(255, round(b * factor)), a)


def build(name):
    lines = [l.rstrip('\r\n') for l in open(os.path.join(ROOT, 'assets', 'maps', f'{name}.txt'), encoding='utf-8')
             if l.strip()]
    rows, cols = len(lines), len(lines[0])
    tiles = [Image.open(os.path.join(TILES, f'tile_{i}.png')).convert('RGBA') for i in range(16)]
    base = lum_mean(tiles[0])
    for i, _ in FLOOR:
        tiles[i] = match_brightness(tiles[i], base * FLOOR_DARK)
    for i, _ in WALL_TOP:
        shade(tiles[i], (0, 0, T, T), WALL_TOP_DARK)

    def wall(c, r):  # r = 그림의 줄 (0 = 맨 위). 맵 밖은 벽으로 본다
        return not (0 <= c < cols and 0 <= r < rows) or lines[r][c] == '#'

    img = Image.new('RGBA', (cols * T, rows * T), (0, 0, 0, 255))
    for r in range(rows):
        for c in range(cols):
            x, y = c * T, r * T
            if not wall(c, r):
                img.alpha_composite(tiles[pick(FLOOR, c, r, 1)], (x, y))
                continue
            top = tiles[pick(WALL_TOP, c, r, 2)]
            if not wall(c, r + 1):  # 아래가 바닥: 윗면 + 벽돌 앞면
                img.alpha_composite(top.crop((0, 0, T, FACE_TOP)), (x, y))
                face = tiles[pick(WALL_FACE, c, r, 3)]
                img.alpha_composite(face.crop((0, 0, T, T - FACE_TOP)), (x, y + FACE_TOP))
                shade(img, (x, y + FACE_TOP, x + T, y + FACE_TOP + 2), 0.55)  # 윗면 끝 아래 그늘 (모서리)
                shade(img, (x, y + T - 3, x + T, y + T), 0.7)  # 벽 밑동
            else:
                img.alpha_composite(top, (x, y))
    # 벽 윗면 테두리: 바닥과 닿는 왼쪽·오른쪽·위쪽 가장자리 (앞면이 있는 칸은 윗면 높이까지만)
    px = img.load()
    for r in range(rows):
        for c in range(cols):
            if not wall(c, r):
                continue
            x, y = c * T, r * T
            top_h = FACE_TOP if not wall(c, r + 1) else T
            if not wall(c, r - 1):
                for i in range(T):
                    px[x + i, y] = RIM
            for dc, xx in ((-1, x), (1, x + T - 1)):
                if not wall(c + dc, r):
                    h = top_h if top_h < T else T
                    for j in range(h):
                        px[xx, y + j] = RIM
                    if top_h < T:  # 앞면 옆 가장자리도 어둡게
                        for j in range(top_h, T):
                            px[xx, y + j] = RIM
            if top_h < T:
                for i in range(T):
                    px[x + i, y + top_h - 1] = RIM  # 윗면과 앞면 사이 선
    # 바닥 그늘: 위가 벽이면 위쪽 6줄, 왼쪽·오른쪽이 벽이면 그쪽 3줄
    for r in range(rows):
        for c in range(cols):
            if wall(c, r):
                continue
            x, y = c * T, r * T
            if wall(c, r - 1):
                for k, f in enumerate((0.45, 0.55, 0.65, 0.75, 0.85, 0.92)):
                    shade(img, (x, y + k, x + T, y + k + 1), f)
            if wall(c - 1, r):
                for k, f in enumerate((0.6, 0.75, 0.88)):
                    shade(img, (x + k, y, x + k + 1, y + T), f)
            if wall(c + 1, r):
                for k, f in enumerate((0.6, 0.75, 0.88)):
                    shade(img, (x + T - 1 - k, y, x + T - k, y + T), f)
    out_dir = os.path.join(ROOT, 'assets', 'images', 'maps')
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, f'{name}_bg.png'))
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(os.path.join(HERE, f'preview_{name}_x2.png'))
    return img


if __name__ == '__main__':
    for n in sys.argv[1:] or ['test_room']:
        build(n)
        print('ok', n)
