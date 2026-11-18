"""회피 핵심 자세(ChatGPT result_<view>.png)를 게임 크기로 줄이고 색·발을 맞춘다 (2026-11-18).

1. 바깥에서 회색 배경을 채워 지우고, 가로로 떨어진 네 자세(서기·웅크림·돌진·미끄러져 멈춤)를 자른다.
2. 서기 자세의 키를 게임 서 있는 그림(idle/<view>.png 첫 장)의 키에 맞춰 같은 배율로 줄인다.
   GPT 그림은 큰 픽셀 덩어리로 그려져 있어, 평균(BOX)이 아니라 덩어리 가운데 색을 집는다(NEAREST): 테두리가 뭉개지지 않게
   (2026-11-18 사용자 지적: 화질이 뭉개짐).
3. 색은 지금 게임 주인공 그림에 있는 색 중 가장 가까운 색으로 바꾼다.
4. 발(아래 4줄) 가운데·발 밑을 게임 그림과 같은 자리에 맞춰 64×48 칸에 놓는다 (돌진 자세가 32보다 넓어서).
출력: keys_<view>_64x48.png (서기 + 네 자세 = 5칸), 미리보기 keys_preview_x4.png
실행: python build_dodge_keys.py
"""
import os
import sys
from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_parry_front as pf  # noqa: E402  (게임 팔레트)

ROOT = HERE.parents[4]
CELL_W, CELL_H = 64, 48


def remove_bg(im, tol=40):
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    bg = px[3, 3][:3]
    seen = bytearray(w * h)
    q = deque([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
              + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        r, g, b, a = px[x, y]
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tol:
            continue
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))
    return im


def split4(im):
    w, h = im.size
    a = im.getchannel('A').load()
    cols = [sum(1 for y in range(h) if a[x, y]) > 2 for x in range(w)]
    runs, start = [], None
    for x, c in enumerate(cols + [False]):
        if c and start is None:
            start = x
        elif not c and start is not None:
            runs.append((start, x))
            start = None
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:4])
    out = []
    for x0, x1 in runs:
        c = im.crop((x0, 0, x1, h))
        out.append(c.crop(c.getbbox()))
    return out


def snap(im, palette):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[3] < 128:
                px[x, y] = (0, 0, 0, 0)
            else:
                px[x, y] = min(palette, key=lambda p: sum((p[i] - c[i]) ** 2 for i in range(3))) + (255,)
    return out


def feet(im):
    px = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3]]
    bottom = max(y for _, y in pts)
    xs = [x for x, y in pts if y >= bottom - 3]
    return (min(xs) + max(xs)) / 2, bottom


def build(view, palette):
    ref = Image.open(ROOT / f"assets/images/player/idle/{view}.png").convert('RGBA').crop((0, 0, 32, 48))
    poses = split4(remove_bg(Image.open(HERE / f"result_{view}.png")))
    scale = (ref.getbbox()[3] - ref.getbbox()[1]) / poses[0].height
    rfx, rfy = feet(ref)
    cells = []
    base = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
    base.alpha_composite(ref, (16, 0))
    cells.append(base)
    for p in poses:
        small = snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.NEAREST), palette)
        fx, fy = feet(small)
        c = Image.new('RGBA', (CELL_W, CELL_H), (0, 0, 0, 0))
        c.alpha_composite(small, (round(16 + rfx - fx), round(rfy - fy)))
        cells.append(c)
    sheet = Image.new('RGBA', (CELL_W * len(cells), CELL_H), (0, 0, 0, 0))
    for k, c in enumerate(cells):
        sheet.alpha_composite(c, (k * CELL_W, 0))
    sheet.save(HERE / f"keys_{view}_64x48.png")
    print(view, 'scale', round(scale, 3))
    return sheet


def main():
    palette = pf.game_palette()
    sheets = [build(v, palette) for v in ('front', 'side', 'back')]
    prev = Image.new('RGBA', (sheets[0].width, CELL_H * 3), (128, 128, 128, 255))
    for i, s in enumerate(sheets):
        prev.alpha_composite(s, (0, i * CELL_H))
    prev.resize((prev.width * 4, prev.height * 4), Image.NEAREST).save(HERE / "keys_preview_x4.png")


if __name__ == '__main__':
    main()
