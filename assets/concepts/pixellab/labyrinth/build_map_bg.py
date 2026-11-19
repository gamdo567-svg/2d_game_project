"""지하 미궁 맵 바탕 그림 만들기.

2026-11-19 사용자 요청: 첫 스테이지는 지하 미궁, 낡은 돌 미궁, 벽은 비스듬히(3/4) 보이게.
같은 날 사용자 지적: 푸른 회색 돌(tiles_v1)은 하수도 느낌 → 참고 그림처럼 따뜻한 색(베이지 돌바닥·갈색 벽돌 벽),
벽 윗면·바깥은 거의 검고, 횃불 둘레만 따뜻하게 밝게 (tiles_v2 + 횃불 + 빛).

글자 맵(assets/maps/<이름>.txt)을 읽어 칸마다 PixelLab 타일(32×32)을 골라 맵 크기의 그림 한 장으로 합친다.
게임은 이 그림을 바닥에 한 번 그린다 (게임에는 PIL 이 필요 없음). 맵 글자를 바꾸면 이 스크립트를 다시 돌린다.

칸 규칙 (그림이 충돌 칸과 정확히 겹치게 칸 안에서만 그린다):
  - 바닥: 벽돌 바닥 변형 중 칸 좌표로 정해지는 것 (같은 맵이면 늘 같은 그림), 금·부스러기는 드물게.
  - 벽: 아래 칸이 바닥이면 '앞에서 보이는 벽' → 위 FACE_TOP 줄은 벽 윗면, 그 아래는 벽돌 앞면(3/4 시점). 아래도 벽이면 윗면만.
  - 벽 윗면이 바닥과 닿는 가장자리에는 테두리, 벽 바로 아래·옆 바닥에는 그늘.
  - 앞에서 보이는 벽 줄에 TORCH_EVERY 칸마다 횃불을 걸고, 그림 전체를 어둡게 한 뒤 횃불 둘레만 따뜻하게 밝힌다.
출력: assets/images/maps/<이름>_bg.png (맵 칸 수 × 32 픽셀), 미리보기 preview_<이름>_x2.png
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
TILES = os.path.join(HERE, 'tiles_v2')
TORCH = os.path.join(HERE, 'torch_v1.png')
T = 32
FACE_TOP = 6  # 앞에서 보이는 벽에서 윗면이 차지하는 줄 수 (나머지는 벽돌 앞면)

# tiles_v2 번호 (0 부터): 벽돌 바닥 0~5, 큰 판석 6·7(쓰지 않음: 섞으면 얼룩덜룩), 벽 윗면 8·9, 벽돌 앞면 10~13·15
FLOOR = [(0, 30), (2, 6), (4, 6), (1, 3), (3, 2), (5, 2)]  # (타일, 비중)
WALL_TOP = [(8, 3), (9, 1)]
WALL_FACE = [(10, 10), (11, 3), (13, 3), (12, 1), (15, 1)]  # 15 = 빈 벽감, 12 = 쇠창살 환기구 (드물게)
GREY_TO_BROWN = {(0x3a, 0x3a, 0x40): (0x35, 0x25, 0x1b), (0x55, 0x55, 0x5c): (0x5a, 0x41, 0x30),
                 (0x76, 0x76, 0x7c): (0x6e, 0x52, 0x3c)}  # 팔레트의 회색 → 갈색 (하수도 느낌 빼기)
RIM = (10, 7, 6, 255)
WALL_FACE_DARK = 0.8  # 벽 앞면은 바닥보다 어둡게
TORCH_EVERY = 6  # 앞에서 보이는 벽 줄에서 몇 칸마다 횃불
TORCH_SCALE = 0.62
AMBIENT = 0.42  # 횃불 빛이 닿지 않는 곳의 밝기
TORCH_LIGHT = 1.0  # 횃불 바로 앞에서 더해지는 밝기
TORCH_RADIUS = 4.5 * T  # 빛이 닿는 거리 (픽셀)
WARM = (1.08, 0.92, 0.72)  # 횃불 빛 색 (빨강·초록·파랑 배율)


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def lum_mean(im):
    px = [p for p in im.get_flattened_data() if p[3]]
    return sum(lum(p) for p in px) / len(px)


def scale(img, box, factor):
    """box 안 픽셀 밝기를 factor 배로."""
    px = img.load()
    x0, y0, x1, y1 = box
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            r, g, b, a = px[x, y]
            px[x, y] = (min(255, round(r * factor)), min(255, round(g * factor)), min(255, round(b * factor)), a)


def recolor(tile):
    out = tile.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[:3] in GREY_TO_BROWN:
                px[x, y] = GREY_TO_BROWN[c[:3]] + (c[3],)
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


def build(name):
    lines = [l.rstrip('\r\n') for l in open(os.path.join(ROOT, 'assets', 'maps', f'{name}.txt'), encoding='utf-8')
             if l.strip()]
    rows, cols = len(lines), len(lines[0])
    tiles = [recolor(Image.open(os.path.join(TILES, f'tile_{i}.png')).convert('RGBA')) for i in range(16)]
    base = lum_mean(tiles[0])
    for i, _ in FLOOR:  # 바닥 변형 밝기를 기본 판에 맞춤 (바둑판처럼 보이지 않게)
        scale(tiles[i], (0, 0, T, T), base / lum_mean(tiles[i]))
    face_base = lum_mean(tiles[WALL_FACE[0][0]])
    for i, _ in WALL_FACE:  # 벽 앞면 변형 밝기도 기본 벽돌에 맞춤 (벽감 타일이 밝은 베이지라 튀었음)
        scale(tiles[i], (0, 0, T, T), WALL_FACE_DARK * face_base / lum_mean(tiles[i]))

    def wall(c, r):  # r = 그림의 줄 (0 = 맨 위). 맵 밖은 벽으로 본다
        return not (0 <= c < cols and 0 <= r < rows) or lines[r][c] == '#'

    def front(c, r):
        return wall(c, r) and not wall(c, r + 1)

    img = Image.new('RGBA', (cols * T, rows * T), (0, 0, 0, 255))
    for r in range(rows):
        for c in range(cols):
            x, y = c * T, r * T
            if not wall(c, r):
                img.alpha_composite(tiles[pick(FLOOR, c, r, 1)], (x, y))
            elif front(c, r):  # 아래가 바닥: 윗면 + 벽돌 앞면
                img.alpha_composite(tiles[pick(WALL_TOP, c, r, 2)].crop((0, 0, T, FACE_TOP)), (x, y))
                face = tiles[pick(WALL_FACE, c, r, 3)]
                img.alpha_composite(face.crop((0, 0, T, T - FACE_TOP)), (x, y + FACE_TOP))
                scale(img, (x, y + FACE_TOP, x + T, y + FACE_TOP + 2), 0.55)  # 윗면 끝 아래 그늘
                scale(img, (x, y + T - 3, x + T, y + T), 0.7)  # 벽 밑동
            else:
                img.alpha_composite(tiles[pick(WALL_TOP, c, r, 2)], (x, y))
    px = img.load()
    for r in range(rows):  # 벽 윗면 테두리
        for c in range(cols):
            if not wall(c, r):
                continue
            x, y = c * T, r * T
            if not wall(c, r - 1):
                for i in range(T):
                    px[x + i, y] = RIM
            for dc, xx in ((-1, x), (1, x + T - 1)):
                if not wall(c + dc, r):
                    for j in range(T):
                        px[xx, y + j] = RIM
            if front(c, r):
                for i in range(T):
                    px[x + i, y + FACE_TOP - 1] = RIM
    for r in range(rows):  # 바닥 그늘
        for c in range(cols):
            if wall(c, r):
                continue
            x, y = c * T, r * T
            if wall(c, r - 1):
                for k, f in enumerate((0.45, 0.55, 0.65, 0.75, 0.85, 0.92)):
                    scale(img, (x, y + k, x + T, y + k + 1), f)
            if wall(c - 1, r):
                for k, f in enumerate((0.6, 0.75, 0.88)):
                    scale(img, (x + k, y, x + k + 1, y + T), f)
            if wall(c + 1, r):
                for k, f in enumerate((0.6, 0.75, 0.88)):
                    scale(img, (x + T - 1 - k, y, x + T - k, y + T), f)

    # 횃불: 앞에서 보이는 벽 줄을 왼쪽부터 세어 TORCH_EVERY 칸마다 (짧은 줄은 가운데 하나)
    torches = []
    for r in range(rows):
        c = 0
        while c < cols:
            if not front(c, r):
                c += 1
                continue
            start = c
            while c < cols and front(c, r):
                c += 1
            run = list(range(start, c))
            if len(run) < TORCH_EVERY:
                if len(run) >= 2:
                    torches.append((run[len(run) // 2], r))
            else:
                torches += [(cc, r) for cc in run[TORCH_EVERY // 2::TORCH_EVERY]]
    torch = Image.open(TORCH).convert('RGBA')
    torch = torch.crop(torch.getbbox())
    torch = torch.resize((max(1, round(torch.width * TORCH_SCALE)), max(1, round(torch.height * TORCH_SCALE))),
                         Image.NEAREST)
    flames = []
    for c, r in torches:
        x = c * T + (T - torch.width) // 2
        y = r * T + T - 4 - torch.height  # 밑동이 벽 밑에서 조금 위
        img.alpha_composite(torch, (x, y))
        flames.append((x + torch.width / 2, y + torch.height * 0.2))

    # 빛: 전체를 AMBIENT 로 어둡게, 횃불 둘레는 따뜻하게 밝게 (가까울수록 더 밝음)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            light = AMBIENT
            warm = 0.0
            for fx, fy in flames:
                d = math.hypot(x - fx, (y - fy) * 1.15)
                if d < TORCH_RADIUS:
                    k = (1 - d / TORCH_RADIUS) ** 1.6
                    light += TORCH_LIGHT * k
                    warm += k
            warm = min(1.0, warm)
            r_, g_, b_, a_ = px[x, y]
            tint = [1 + (w - 1) * warm for w in WARM]
            px[x, y] = (min(255, round(r_ * light * tint[0])), min(255, round(g_ * light * tint[1])),
                        min(255, round(b_ * light * tint[2])), a_)
    out_dir = os.path.join(ROOT, 'assets', 'images', 'maps')
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, f'{name}_bg.png'))
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(os.path.join(HERE, f'preview_{name}_x2.png'))
    return img, torches


if __name__ == '__main__':
    for n in sys.argv[1:] or ['test_room']:
        _, t = build(n)
        print('ok', n, 'torches', len(t))
