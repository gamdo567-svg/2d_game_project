"""후면 패링 시트 만들기 (2026-11-18).

PixelLab 은 후면 쳐올림에서 고개를 옆으로 돌려 그려서, 핵심 자세(서기·당김·쳐올림·막기)를 사용자가 ChatGPT 로 그렸다
(parry_back_kit/README.txt, result_back.png: 회색 배경, 칼과 잔상은 파란 단색).

1. 바깥에서 회색 배경을 채워 지우고, 가로로 떨어진 네 자세를 자른다.
2. 서기 자세의 키를 게임 뒷모습(kit/ref_back_nosword_64.png)의 키에 맞춰 같은 배율로 줄인다 (BOX).
3. 파란 픽셀(칼·잔상)은 파란색 하나로, 나머지(몸)는 지금 게임 주인공 그림에 있는 색 중 가장 가까운 색으로 바꾼다.
4. 디딘 발(아래 줄들) 가운데·발 밑을 게임 뒷모습 그림과 같은 자리에 맞춰 64×64 에 놓는다.
5. 정면과 같은 순서로 시트를 만든다: 칸 0 = 게임 뒷모습, 1~5 = 당김, 쳐올림, 막기, 막기, 당김.
출력: remake_raw/parry_back_sheet_68.png. export_to_game.py 가 읽는다 (VIEW_PARRY['back']).
"""
import os
import sys
from collections import deque

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_parry_front as pf  # noqa: E402  (게임 팔레트)
import build_remake_preview as b  # noqa: E402

RAW = os.path.join(HERE, 'remake_raw')
SRC = os.path.join(HERE, 'parry_back_kit', 'result_back.png')
BLUE = (30, 144, 255, 255)
PICK = [1, 2, 3, 3, 1]  # 0 서기, 1 당김, 2 쳐올림, 3 막기


def remove_bg(im, tol=30):
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
        r, g, bb, a = px[x, y]
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(bb - bg[2]) > tol:
            continue
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))
    return im


def split4(im):
    w, h = im.size
    a = im.getchannel('A').load()
    cols = [any(a[x, y] for y in range(h)) for x in range(w)]
    runs, start = [], None
    for x, c in enumerate(cols + [False]):
        if c and start is None:
            start = x
        elif not c and start is not None:
            runs.append((start, x))
            start = None
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:4])
    return [im.crop((x0, 0, x1, h)).crop(im.crop((x0, 0, x1, h)).getbbox()) for x0, x1 in runs]


def body_height(pose):
    """칼·잔상(파란)을 뺀 몸의 높이."""
    px = pose.load()
    ys = [y for y in range(pose.height) for x in range(pose.width) if px[x, y][3] and not b.is_blue(px[x, y])]
    return max(ys) - min(ys) + 1


def snap(im, palette):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[3] < 128:
                px[x, y] = (0, 0, 0, 0)
            elif b.is_blue(c):
                px[x, y] = BLUE
            else:
                px[x, y] = min(palette, key=lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2) + (255,)
    return out


def feet(im):
    """몸(파란 제외) 아래 4줄의 가로 가운데와 가장 아래 줄."""
    px = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3] and not b.is_blue(px[x, y])]
    bottom = max(y for _, y in pts)
    xs = [x for x, y in pts if y >= bottom - 3]
    return (min(xs) + max(xs)) / 2, bottom


def main():
    ref = Image.open(os.path.join(HERE, '..', 'kit', 'ref_back_nosword_64.png')).convert('RGBA')
    poses = split4(remove_bg(Image.open(SRC)))
    rx0, ry0, rx1, ry1 = ref.getbbox()
    scale = (ry1 - ry0) / body_height(poses[0])
    palette = pf.game_palette()
    rfx, rfy = feet(ref)
    cells = [ref]
    for i in PICK:
        p = poses[i]
        small = snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.BOX), palette)
        fx, fy = feet(small)
        c = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        c.alpha_composite(small, (round(rfx - fx), round(rfy - fy)))
        cells.append(c)
    x0, y0, x1, y1 = ref.getchannel('A').getbbox()
    cx, foot = (x0 + x1) // 2, y1 - 1
    sheet = Image.new('RGBA', (68 * len(cells), 68), (0, 0, 0, 0))
    for k, f in enumerate(cells):
        big = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
        big.alpha_composite(f, (40, 40))
        sheet.alpha_composite(big.crop((40 + cx - 34, 40 + foot - 58, 40 + cx + 34, 40 + foot + 10)), (k * 68, 0))
    sheet.save(os.path.join(RAW, 'parry_back_sheet_68.png'))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(
        os.path.join(HERE, 'parry_back_kit', 'parry_back_sheet_x4.png'))
    print('scale', round(scale, 3), 'saved', sheet.size)


if __name__ == '__main__':
    main()
