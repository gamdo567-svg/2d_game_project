"""검 전기 이펙트 2차 (2026-11-20 사용자: 1차 번개가 너무 조잡함, 스파크가 더 튀고 진짜 전기 같게. 1차는 build_lightning_v1.py).

픽셀 번개답게 굵은 덩어리 대신 1 픽셀 흰 줄기를 날카롭게 꺾어 그린다:
- 아크: 칼날 가장자리 띠 위의 두 점(칼 방향으로 6~14 픽셀 떨어진, 같은 쪽)을 잇는 번개. 가운데를 옆으로 밀어내는 방식
  (midpoint displacement, 바깥으로 치우침)으로 날카롭게 꺾이며 칼날에서 튀어나갔다 돌아온다. 흰 심 + 바로 옆 1 픽셀만 파랑.
- 갈래: 아크 중간에서 바깥으로 짧게 갈라지는 하늘색 번개.
- 스파크: 번개 끝과 칼날에서 튀어 나가는 점들이 짧은 꼬리를 남기며 몇 장에 걸쳐 날아가 파랗게 식는다.
- 방전: 4장(약 0.33초)마다 칼끝(입힐 때는 번지는 앞머리)에서 크게 뻗는 번개 둘, 칼날 둘레가 번쩍.
- 칼날 둘레에 얇은 푸른 빛(1 픽셀)이 깜빡이며 늘 깔림.
번개는 장마다 새로 (장마다 정해진 씨앗이라 늘 같은 그림).
출력 (assets/images/effects/sword_enchant/): lightning.png (80×24 × 24), lightning_ignite.png (× 12),
lightning_front_3_f5.png / f6.png (정면 3타 찌르기용 칼 그림, 96×64 × 24)
"""
import math
import os
import random

from PIL import Image

import build_fire_flame as ff

OUT = ff.OUT
FRAMES = ff.FRAMES
IGNITE_FRAMES = ff.IGNITE_FRAMES
WHITE = (250, 254, 255, 255)
CYAN = (140, 225, 255, 255)
BLUE = (70, 150, 255, 220)
DEEP = (45, 85, 220, 150)
BLADE_GLOW = (120, 200, 255, 160)
BLADE_GLOW_FLASH = (170, 230, 255, 190)
MAX_REACH = 4.5  # 아크·갈래가 칼날에서 벗어나는 최대 거리 (픽셀)


def dist_map(blade, w, h):
    return {(x, y): min(math.hypot(x - bx, y - by) for bx, by in blade) for y in range(h) for x in range(w)}


def line_pixels(a, b):
    """두 점 사이 1 픽셀 선 (Bresenham)."""
    (x0, y0), (x1, y1) = (round(a[0]), round(a[1])), (round(b[0]), round(b[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def jagged(rnd, a, b, rough=0.45, depth=3, outward=None):
    """a 에서 b 로 날카롭게 꺾인 번개 꼭짓점들. outward(p) 가 있으면 그 쪽(칼날 바깥)으로 치우쳐 꺾음."""
    pts = [a, b]
    for _ in range(depth):
        new = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            seg = math.hypot(q[0] - p[0], q[1] - p[1])
            nx, ny = -(q[1] - p[1]) / (seg or 1), (q[0] - p[0]) / (seg or 1)
            off = rnd.uniform(-1, 1) * seg * rough
            if outward is not None:  # 칼날 쪽으로 파고들지 않게
                ox, oy = outward((mx, my))
                if nx * ox + ny * oy < 0:
                    nx, ny = -nx, -ny
                off = abs(off) * (1 if rnd.random() < 0.8 else -0.4)
            new += [(mx + nx * off, my + ny * off), q]
        pts = new
    return pts


def polyline(pts):
    out = []
    for p, q in zip(pts, pts[1:]):
        seg = line_pixels(p, q)
        out += seg if not out else seg[1:]
    return out


class Painter:
    def __init__(self, size, blade):
        self.im = Image.new('RGBA', size, (0, 0, 0, 0))
        self.px = self.im.load()
        self.blade = blade
        self.w, self.h = size

    def put(self, p, c, weaker_only=True):
        x, y = p
        if 0 <= x < self.w and 0 <= y < self.h and p not in self.blade:
            if not weaker_only or self.px[x, y][3] < c[3]:
                self.px[x, y] = c

    def bolt(self, pixels, core=WHITE):
        for x, y in pixels:  # 바로 옆 1 픽셀만 파랑 (번개가 굵어 보이지 않게 대각선은 빼고)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.put((x + d[0], y + d[1]), BLUE)
        for p in pixels:
            self.put(p, core, weaker_only=False)


def blade_band(dist, lo, hi, keep):
    return [p for p, v in dist.items() if lo <= v <= hi and keep(p)]


def outward_fn(centre):
    def f(p):
        cx, cy = centre(p)
        dx, dy = p[0] - cx, p[1] - cy
        n = math.hypot(dx, dy) or 1
        return dx / n, dy / n
    return f


def same_side(centre, a, b):
    ca, cb = centre(a), centre(b)
    return (a[0] - ca[0]) * (b[0] - cb[0]) + (a[1] - ca[1]) * (b[1] - cb[1]) > 0


def draw(seed, size, blade, dist, along, centre, start, end, flash=False, front=None):
    """한 장. along(p) = 칼 방향 자리, centre(p) = 그 자리의 칼 가운데 점, start~end = 칼날 범위 (손잡이 쪽 ~ 칼끝).
    front 가 있으면 그 자리(칼 방향)까지만 전기가 번져 있다 (입힐 때)."""
    rnd = random.Random(seed)
    top = end if front is None else min(end, front)
    paint = Painter(size, blade)
    out = outward_fn(centre)
    for bx, by in blade:  # 칼날 둘레 얇은 빛 (깜빡임)
        if along((bx, by)) > top:
            continue
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if rnd.random() < (0.9 if flash else 0.55):
                paint.put((bx + d[0], by + d[1]), BLADE_GLOW_FLASH if flash else BLADE_GLOW)
    band = blade_band(dist, 1.0, 2.0, lambda p: start + 1 <= along(p) <= top)
    if not band:
        return paint.im
    ends = []
    near = lambda pix: [p for p in pix if p in dist and dist[p] <= MAX_REACH]  # 칼에서 멀리 벗어나지 않게
    for _ in range(rnd.randint(4, 5)):  # 아크
        a = rnd.choice(band)
        cands = [q for q in band if 6 <= along(q) - along(a) <= 14 and same_side(centre, a, q)]
        if not cands:
            continue
        b = rnd.choice(cands)
        pts = jagged(rnd, a, b, rough=0.28, depth=3, outward=out)
        paint.bolt(near(polyline(pts)))
        ends += [a, b]
        if rnd.random() < 0.6 and len(pts) > 3:  # 갈래
            m = pts[len(pts) // 2]
            ox, oy = out(m)
            reach = rnd.uniform(2, 4)
            tip = (m[0] + ox * reach + rnd.uniform(-2, 2), m[1] + oy * reach + rnd.uniform(-2, 2))
            paint.bolt(near(polyline(jagged(rnd, m, tip, rough=0.35, depth=2))), core=CYAN)
            ends.append((round(tip[0]), round(tip[1])))
    if flash:  # 방전
        heads = [p for p in band if along(p) >= top - 3] or band
        for _ in range(1):
            m = rnd.choice(heads)
            ox, oy = out(m)
            reach = rnd.uniform(5, 7)
            tip = (m[0] + ox * reach + rnd.uniform(-1.5, 1.5), m[1] + oy * reach + rnd.uniform(-1.5, 1.5))
            paint.bolt(polyline(jagged(rnd, m, tip, rough=0.35, depth=2)))
            ends.append((round(tip[0]), round(tip[1])))
    for e in ends:  # 번개 끝에서 튀는 스파크 (짧은 꼬리)
        if rnd.random() < 0.5:
            ox, oy = out(e)
            vx, vy = ox * rnd.uniform(1.0, 2.0) + rnd.uniform(-1, 1), oy * rnd.uniform(1.5, 3) + rnd.uniform(-1, 1)
            for k, c in enumerate((WHITE, CYAN, DEEP)):
                paint.put((round(e[0] + vx * (2 - k)), round(e[1] + vy * (2 - k))), c, weaker_only=False)
    return paint.im


def sparks_over(im, seed_base, i, band, out, n_frames, blade):
    """여러 장에 걸쳐 날아가는 스파크 (앞 3장에서 태어난 것까지): 흰 머리 + 파란 꼬리, 나이 들수록 식음."""
    px = im.load()
    w, h = im.size
    if not band:
        return
    for born in range(i - 3, i + 1):
        rnd = random.Random(seed_base * 7919 + (born % n_frames))
        for _ in range(rnd.randint(1, 2)):
            o = rnd.choice(band)
            ox, oy = out(o)
            vx = ox * rnd.uniform(1.2, 2.4) + rnd.uniform(-0.8, 0.8)
            vy = oy * rnd.uniform(1.2, 2.4) + rnd.uniform(-0.8, 0.8)
            age = i - born
            head = (round(o[0] + vx * (age + 1)), round(o[1] + vy * (age + 1)))
            trail = (round(o[0] + vx * age), round(o[1] + vy * age))
            for p, c in ((trail, DEEP if age > 1 else BLUE), (head, CYAN if age > 1 else WHITE)):
                if 0 <= p[0] < w and 0 <= p[1] < h and p not in blade and px[p][3] < c[3]:
                    px[p] = c


def sword_sheets():
    blade = ff.blade_pixels()
    dist = dist_map(blade, ff.W, ff.H)
    tip = max(x for x, _ in blade)

    def along(p):
        return p[0]

    def centre(p):
        return (min(p[0], tip), ff.MID_Y)

    def frame(i, front=None, salt=0):
        flash = (i % 4 == 0) if front is None else True
        im = draw(salt * 1000 + i, (ff.W, ff.H), blade, dist, along, centre, ff.BLADE_FROM_X, tip, flash, front)
        top = tip if front is None else front
        sparks_over(im, 11 + salt, i, blade_band(dist, 1.0, 2.0, lambda p: ff.BLADE_FROM_X < p[0] <= top),
                    outward_fn(centre), FRAMES, blade)
        return im

    strip = Image.new('RGBA', (ff.W * FRAMES, ff.H), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.alpha_composite(frame(i), (i * ff.W, 0))
    strip.save(os.path.join(OUT, 'lightning.png'))
    ignite = Image.new('RGBA', (ff.W * IGNITE_FRAMES, ff.H), (0, 0, 0, 0))
    for k in range(IGNITE_FRAMES):
        front = ff.BLADE_FROM_X + 2 + (tip + 2 - (ff.BLADE_FROM_X + 2)) * (k + 1) / IGNITE_FRAMES
        ignite.alpha_composite(frame(k, front, salt=1), (k * ff.W, 0))
    ignite.save(os.path.join(OUT, 'lightning_ignite.png'))


def art_sheets():
    for k, top_row in ff.ART_BLADE_TOP.items():
        blade = ff.art_blade(k)
        dist = dist_map(blade, 96, 64)
        rows = {}
        for x, y in blade:
            rows.setdefault(y, []).append(x)
        bottom = max(rows)

        def along(p):
            return p[1]

        def centre(p, rows=rows, bottom=bottom, top_row=top_row):
            y = min(max(p[1], top_row), bottom)
            xs = rows.get(y) or rows[bottom]
            return ((min(xs) + max(xs)) / 2, y)

        strip = Image.new('RGBA', (96 * FRAMES, 64), (0, 0, 0, 0))
        for i in range(FRAMES):
            im = draw(5000 + k * 100 + i, (96, 64), blade, dist, along, centre, top_row, bottom, i % 4 == 0)
            sparks_over(im, 31 + k, i, blade_band(dist, 1.0, 2.0, lambda p: p[1] > top_row),
                        outward_fn(centre), FRAMES, blade)
            strip.alpha_composite(im, (i * 96, 0))
        strip.save(os.path.join(OUT, f'lightning_front_3_f{k}.png'))


if __name__ == '__main__':
    sword_sheets()
    art_sheets()
    print('lightning', FRAMES, 'ignite', IGNITE_FRAMES, 'art', list(ff.ART_BLADE_TOP))
