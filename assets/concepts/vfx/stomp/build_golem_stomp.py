"""골렘 발 구르기(8x8) 이펙트 프레임 생성기 (시안, 게임 코드와 무관).

원본 해상도(1x) 288x288 캔버스, 가운데 (144,144) 가 발 구르는 지점.
- 거미줄 금: 가운데서 퍼지며 하얗게 번쩍인 뒤 어두운 틈으로 식음, 아래 가장자리에 밝은 턱
- 크레이터: 가운데 움푹 팬 자국 (왼쪽 위 그늘, 오른쪽 아래 밝은 벽)
- 바닥 판: 크레이터 둘레의 바닥이 깨져 솟아오름 (윗면 + 두께 + 그림자 + 검은 외곽선)
- 돌: 공중으로 포물선을 그리며 날아가 그림자 위에 떨어지고 한 번 튐
- 먼지: 바깥으로 퍼지며 옅어짐 / 충격파 고리 / 섬광
- 사라질 때: 바깥부터 픽셀 단위(베이어 디더)로 흩어짐

출력: 같은 폴더에 golem_stomp_sheet.png (+ .json), 게임 배율 미리보기 GIF·정지 컷,
      그리고 게임이 읽는 사본 assets/images/effects/golem_stomp.png (6열 × 5줄, 프레임 288×288).
실행: python build_golem_stomp.py
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
S = 288
C = S // 2
FRAMES = 30
FPS = 12

# 골렘 팔레트 (golem_simple south.png 에서 뽑은 색)
K = (5, 4, 6, 255)          # 외곽선
D0 = (15, 14, 20, 255)      # 가장 어두움
D1 = (24, 24, 34, 255)
D2 = (36, 37, 50, 255)
D3 = (49, 51, 67, 255)
M1 = (57, 62, 76, 255)
M2 = (77, 87, 94, 255)
M3 = (86, 96, 101, 255)
L1 = (110, 118, 123, 255)
L2 = (121, 131, 134, 255)
L3 = (148, 162, 163, 255)
W1 = (216, 224, 224, 255)
W2 = (250, 254, 254, 255)

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def keep(x: int, y: int, alpha: float) -> bool:
    """베이어 디더: alpha(0~1) 만큼의 픽셀만 남긴다."""
    return (BAYER[y % 4][x % 4] + 0.5) / 16 < alpha


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def ease_out(t: float) -> float:
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def put(img: Image.Image, x: int, y: int, c) -> None:
    if 0 <= x < S and 0 <= y < S:
        img.putpixel((x, y), c)


def line_pts(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def outline(layer: Image.Image, colour=K) -> Image.Image:
    """불투명 픽셀 둘레(상하좌우)에 외곽선을 붙인다."""
    src = layer.load()
    out = layer.copy()
    dst = out.load()
    w, h = layer.size
    for y in range(h):
        for x in range(w):
            if src[x, y][3] == 0:
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] > 0:
                        dst[x, y] = colour
                        break
    return out


rng = random.Random(7)

# ---------------------------------------------------------------- 금 (거미줄)
CRATER_R = 17
crack_px: dict[tuple[int, int], float] = {}   # 픽셀 -> 드러나는 거리(가운데로부터)


def add_path(points):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        for x, y in line_pts(x0, y0, x1, y1):
            dist = math.hypot(x - C, y - C)
            if dist >= CRATER_R - 2:
                crack_px.setdefault((x, y), dist)


N_RAD = 9
rad_angles = [i * 360 / N_RAD + rng.uniform(-12, 12) for i in range(N_RAD)]
rad_paths = []
for a in rad_angles:
    r_end = rng.uniform(112, 134)
    pts, r, ang = [], CRATER_R - 1, math.radians(a)
    while r < r_end:
        pts.append((C + r * math.cos(ang), C + r * math.sin(ang)))
        r += rng.uniform(7, 11)
        ang += math.radians(rng.uniform(-14, 14))
    rad_paths.append(pts)
    add_path(pts)
    # 잔가지
    for _ in range(2):
        k = rng.randrange(2, max(3, len(pts) - 1))
        bx, by = pts[k]
        ba = math.atan2(by - C, bx - C) + math.radians(rng.choice([-1, 1]) * rng.uniform(30, 55))
        L = rng.uniform(10, 22)
        add_path([(bx, by), (bx + L * 0.5 * math.cos(ba) + rng.uniform(-2, 2), by + L * 0.5 * math.sin(ba)),
                  (bx + L * math.cos(ba), by + L * math.sin(ba))])


def point_at_radius(path, rr):
    best = min(path, key=lambda p: abs(math.hypot(p[0] - C, p[1] - C) - rr))
    return best


for rr in (38, 66, 96):
    for i in range(N_RAD):
        if rr > 90 and rng.random() < 0.3:
            continue  # 바깥 고리는 군데군데 끊김
        p0 = point_at_radius(rad_paths[i], rr)
        p1 = point_at_radius(rad_paths[(i + 1) % N_RAD], rr)
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        # 고리는 바깥으로 살짝 휘고 꺾임
        dx, dy = mx - C, my - C
        dl = math.hypot(dx, dy) or 1
        bulge = rng.uniform(-3, 6)
        mid = (mx + dx / dl * bulge, my + dy / dl * bulge)
        add_path([p0, mid, p1])

crack_fade_key = {p: rng.random() for p in crack_px}


def draw_cracks(img: Image.Image, f: int) -> None:
    reveal = 140 * ease_out(f / 4.0)
    fade = clamp01((f - 17) / 11)
    for (x, y), dist in crack_px.items():
        if dist > reveal:
            continue
        # 바깥 금부터 사라짐
        if fade > 0 and fade > crack_fade_key[(x, y)] * 0.55 + (1 - dist / 140) * 0.45:
            continue
        age = f - (4.0 * (1 - (1 - dist / 140) ** (1 / 3)) if dist < 140 else 4)
        if age < 1.2:
            put(img, x, y, W2)
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in crack_px and 0 <= nx < S and 0 <= ny < S and img.getpixel((nx, ny))[3] == 0:
                    put(img, nx, ny, L3)
        elif age < 2.5:
            put(img, x, y, L2)
        elif age < 4:
            put(img, x, y, M2)
        else:
            put(img, x, y, D0)
            # 아래쪽 가장자리가 빛을 받는 턱 (입체감)
            if (x, y + 1) not in crack_px and img.getpixel((x, min(S - 1, y + 1)))[3] == 0:
                put(img, x, y + 1, M1)


def draw_crater(img: Image.Image, f: int) -> None:
    if f < 1:
        return
    fade = clamp01((f - 19) / 8)
    r = CRATER_R * ease_out(f / 2.5) * (1 - 0.5 * fade)   # 사라질 때 메워지듯 작아짐
    if fade >= 1:
        return
    for y in range(int(C - r - 3), int(C + r + 4)):
        for x in range(int(C - r - 3), int(C + r + 4)):
            dx, dy = x - C + 0.5, y - C + 0.5
            d = math.hypot(dx, dy)
            if d > r + 2:
                continue
            if fade > 0 and not keep(x, y, 1 - fade):
                continue
            side = (dx + dy) / (d or 1)  # +1 = 오른쪽 아래, -1 = 왼쪽 위
            if d > r:            # 둘레 턱
                put(img, x, y, L1 if side > 0.2 else D2)
            elif d > r - 3:      # 안쪽 벽: 왼쪽 위는 그늘, 오른쪽 아래는 빛
                put(img, x, y, M2 if side > 0.3 else D0)
            else:                # 바닥
                put(img, x, y, D1 if side > -0.2 else D0)


# ---------------------------------------------------------------- 바닥 판
class Slab:
    def __init__(self, ang: float):
        self.ang = math.radians(ang)
        self.r = rng.uniform(62, 86)
        self.w = rng.uniform(20, 30)   # 둘레 방향 길이
        self.d = rng.uniform(11, 16)   # 반지름 방향 폭
        self.h_max = rng.uniform(6, 10)
        self.thick = rng.choice([3, 4])
        self.t0 = 1.6 + self.r / 60
        self.sink = rng.uniform(19, 23)
        self.seam = rng.random() < 0.6
        self.specks = [(rng.uniform(0.15, 0.85), rng.uniform(0.2, 0.8)) for _ in range(rng.randint(2, 4))]

    def height(self, f: float) -> float | None:
        """땅 위로 나온 높이(px). 음수면 땅 밑에 일부/전부 잠겨 있음. None = 아직/이미 없음."""
        u = f - self.t0
        if u < 0:
            return None
        under = -(self.d + self.thick + 2)                  # 완전히 땅 밑
        # 땅을 뚫고 솟음 → 살짝 넘침 → 자리 잡음
        rise = [under, under * 0.35, self.h_max * 0.55, self.h_max * 1.15, self.h_max * 0.95, self.h_max]
        h = rise[int(u)] if u < len(rise) - 1 else self.h_max
        if f > self.sink:                                   # 천천히 땅속으로 가라앉음
            t = clamp01((f - self.sink) / 6)
            h = self.h_max + (under - self.h_max) * (t * t)
            if t >= 1:
                return None
        return h

    def corners(self, h: float):
        cx, cy = C + self.r * math.cos(self.ang), C + self.r * math.sin(self.ang)
        rx, ry = math.cos(self.ang), math.sin(self.ang)       # 바깥 방향
        tx, ty = -ry, rx                                      # 둘레 방향
        pts = []
        for sr, st in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            gx = cx + rx * sr * self.d / 2 + tx * st * self.w / 2
            gy = cy + ry * sr * self.d / 2 + ty * st * self.w / 2
            lift = h if sr < 0 else h * 0.25                  # 안쪽 가장자리가 더 높이 들림
            pts.append((gx, gy - lift))
        ground = []
        for sr, st in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            ground.append((cx + rx * sr * self.d / 2 + tx * st * self.w / 2,
                           cy + ry * sr * self.d / 2 + ty * st * self.w / 2))
        return pts, ground

    def draw(self, shadow: Image.Image, body: Image.Image, f: int) -> None:
        h = self.height(f)
        if h is None:
            return
        top, ground = self.corners(h)
        # 땅 그림자: 땅 위로 나온 만큼만 (가라앉으면 같이 사라짐)
        if h > 1:
            k = min(1.0, h / self.h_max)
            gcx, gcy = sum(p[0] for p in ground) / 4, sum(p[1] for p in ground) / 4
            sd = ImageDraw.Draw(shadow)
            sd.polygon([(gcx + (x - gcx) * (0.6 + 0.4 * k) + 1 + h * 0.3, gcy + (y - gcy) * (0.6 + 0.4 * k) + 2)
                        for x, y in ground], fill=D0)
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for k in range(self.thick, 0, -1):                  # 두께(옆면)
            ld.polygon([(x, y + k) for x, y in top], fill=D2 if k < self.thick else D1)
        ld.polygon(top, fill=M3)                            # 윗면
        # 윗면 가장자리 빛: 왼쪽 위 변은 밝게, 오른쪽 아래 변은 어둡게
        for a, b in zip(top, top[1:] + top[:1]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            tx, ty = mx - sum(p[0] for p in top) / 4, my - sum(p[1] for p in top) / 4
            col = L2 if tx + ty < 0 else M1
            for x, y in line_pts(*a, *b):
                put(layer, x, y, col)
        if self.seam:                                       # 타일 줄눈
            a, b, c2, d = top
            p = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            q = ((d[0] + c2[0]) / 2, (d[1] + c2[1]) / 2)
            for x, y in line_pts(*p, *q):
                if layer.getpixel((x, y))[3]:
                    put(layer, x, y, M1)
        # 돌 질감: 윗면에 작은 패임(어두운 점 + 오른쪽 아래 밝은 점)
        a, b, c2, d = top
        for su, sv in self.specks:
            px_ = a[0] + (b[0] - a[0]) * su + (d[0] - a[0]) * sv + (c2[0] - b[0] - d[0] + a[0]) * su * sv
            py_ = a[1] + (b[1] - a[1]) * su + (d[1] - a[1]) * sv + (c2[1] - b[1] - d[1] + a[1]) * su * sv
            x, y = int(px_), int(py_)
            if layer.getpixel((x, y)) == M3 and layer.getpixel((x + 1, y + 1)) == M3:
                put(layer, x, y, M1)
                put(layer, x + 1, y + 1, L1)
        # 땅 밑에 잠긴 부분은 잘라냄: 발자리(footprint) 아래 가장자리보다 아래는 안 보임
        fp = Image.new("L", (S, S), 0)
        ImageDraw.Draw(fp).polygon(ground, fill=255)
        fpx = fp.load()
        bottom = {}
        for x in range(S):
            ys = [y for y in range(S) if fpx[x, y]]
            if ys:
                bottom[x] = max(ys)
        for x in list(bottom):
            for nx in (x - 1, x + 1):
                bottom.setdefault(nx, bottom[x])
        px = layer.load()
        for y in range(S):
            for x in range(S):
                if px[x, y][3] and (x not in bottom or y > bottom[x]):
                    px[x, y] = (0, 0, 0, 0)
        layer = outline(layer)
        body.alpha_composite(layer)


slab_angles = [i * 360 / 11 + rng.uniform(-8, 8) for i in range(11)]
slabs = [Slab(a) for a in slab_angles]

# ---------------------------------------------------------------- 돌 (포물선)
ROCK_SPRITES = [
    [".1111..", "155431.", "1544321", "1433221", ".13221.", "..111.."],
    [".111.", "15431", "14321", ".111."],
    ["..11111..", ".1554431.", "155544331", "154443321", "144333221", ".1332221.", "..11111.."],
    ["..111.", ".15431", "154321", "14321.", ".111.."],
]
ROCK_COL = {"1": K, "2": D3, "3": M1, "4": M3, "5": L3}


def rock_img(idx: int, turn: int) -> Image.Image:
    rows = ROCK_SPRITES[idx]
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in ROCK_COL:
                im.putpixel((x, y), ROCK_COL[ch])
    # 굴러가는 느낌: 좌우 반전만 (빛 방향이 크게 틀어지지 않게)
    if turn % 2:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


class Rock:
    def __init__(self, big: bool):
        self.idx = 2 if big else rng.choice([0, 0, 1, 3])
        a = math.radians(rng.uniform(0, 360))
        self.start = (C + 12 * math.cos(a), C + 12 * math.sin(a))
        dist = rng.uniform(55, 95) if big else rng.uniform(45, 135)
        self.end = (C + dist * math.cos(a), C + dist * math.sin(a))
        self.bounce_end = (self.end[0] + 6 * math.cos(a), self.end[1] + 6 * math.sin(a))
        self.t0 = rng.uniform(1, 2.5)
        self.T = rng.uniform(5, 8)
        self.peak = rng.uniform(16, 30) if big else rng.uniform(14, 36)
        self.gone = rng.uniform(20, 25.5)

    def state(self, f: float):
        u = (f - self.t0) / self.T
        if u < 0:
            return None
        if u <= 1:
            gx = self.start[0] + (self.end[0] - self.start[0]) * u
            gy = self.start[1] + (self.end[1] - self.start[1]) * u
            return gx, gy, self.peak * 4 * u * (1 - u), True
        v = (f - self.t0 - self.T) / 2.0  # 한 번 튐 (2프레임)
        if v <= 1:
            gx = self.end[0] + (self.bounce_end[0] - self.end[0]) * v
            gy = self.end[1] + (self.bounce_end[1] - self.end[1]) * v
            return gx, gy, 4 * 4 * v * (1 - v), True
        return self.bounce_end[0], self.bounce_end[1], 0.0, False

    def draw(self, shadow: Image.Image, body: Image.Image, f: int) -> None:
        st = self.state(f)
        if st is None:
            return
        gx, gy, h, flying = st
        fade = clamp01((f - self.gone) / 3)
        spr = rock_img(self.idx, int(f) if flying else 0)
        w, hgt = spr.size
        # 그림자: 높을수록 작고 옅게
        sw = max(2, int(w * (1 - min(h, 30) / 60)))
        sd = ImageDraw.Draw(shadow)
        sx, sy = int(gx - sw / 2), int(gy + hgt / 2 - 1)
        if h < 28 and fade < 0.35:
            sd.ellipse((sx, sy, sx + sw, sy + 2), fill=D0)
        x0, y0 = int(round(gx - w / 2)), int(round(gy - hgt / 2 - h))
        px = spr.load()
        for yy in range(hgt):
            for xx in range(w):
                if px[xx, yy][3] and (fade == 0 or keep(x0 + xx, y0 + yy, 1 - fade)):
                    put(body, x0 + xx, y0 + yy, px[xx, yy])


rocks = [Rock(big=i < 4) for i in range(22)]


class Chip:
    """1~2 px 작은 돌 부스러기: 더 멀리, 더 빨리, 금방 사라짐."""

    def __init__(self):
        a = math.radians(rng.uniform(0, 360))
        d = rng.uniform(60, 140)
        self.s = (C + 10 * math.cos(a), C + 10 * math.sin(a))
        self.e = (C + d * math.cos(a), C + d * math.sin(a))
        self.t0, self.T, self.peak = rng.uniform(1, 2), rng.uniform(4, 6), rng.uniform(10, 26)
        self.size = rng.choice([1, 1, 2])
        self.col = rng.choice([M3, L1, D3])
        self.gone = rng.uniform(12, 18)

    def draw(self, body: Image.Image, f: int) -> None:
        u = (f - self.t0) / self.T
        if u < 0 or f > self.gone:
            return
        u = min(u, 1)
        gx = self.s[0] + (self.e[0] - self.s[0]) * u
        gy = self.s[1] + (self.e[1] - self.s[1]) * u - self.peak * 4 * u * (1 - u)
        for dy in range(self.size):
            for dx in range(self.size):
                put(body, int(gx) + dx, int(gy) + dy, self.col)


chips = [Chip() for _ in range(34)]


# ---------------------------------------------------------------- 먼지
class Puff:
    def __init__(self, ang: float):
        self.a = math.radians(ang)
        self.r0 = rng.uniform(14, 24)
        self.r1 = rng.uniform(60, 98)
        self.size0, self.size1 = rng.uniform(5, 8), rng.uniform(9, 14)
        self.t0 = rng.uniform(0.8, 1.8)
        self.life = rng.uniform(9, 13)

    def draw(self, img: Image.Image, f: int) -> None:
        u = (f - self.t0) / self.life
        if u < 0 or u > 1:
            return
        e = ease_out(u * 1.4)
        r = self.r0 + (self.r1 - self.r0) * e
        cx = C + r * math.cos(self.a)
        cy = C + r * math.sin(self.a) - 8 * u
        rad = self.size0 + (self.size1 - self.size0) * e
        alpha = 1 - clamp01((u - 0.55) / 0.45)
        rad *= 1 - 0.35 * clamp01((u - 0.55) / 0.45)
        for y in range(int(cy - rad - 1), int(cy + rad + 2)):
            for x in range(int(cx - rad - 1), int(cx + rad + 2)):
                dx, dy = x - cx + 0.5, y - cy + 0.5
                d = math.hypot(dx, dy)
                if d > rad or not keep(x, y, alpha):
                    continue
                side = (dx + dy) / (d or 1)
                if d > rad - 1.2:
                    col = M1 if side > -0.3 else L1
                elif side < -0.45 and d > rad * 0.35:
                    col = L3
                elif side > 0.45:
                    col = M3
                else:
                    col = L2
                put(img, x, y, col)


puffs = [Puff(i * 360 / 16 + rng.uniform(-10, 10)) for i in range(16)]


def draw_ring(img: Image.Image, f: int) -> None:
    if not 1 <= f <= 6:
        return
    u = (f - 1) / 5
    r = 22 + 120 * ease_out(u)
    alpha = 1 - u * 0.85
    for a in range(0, 3600):
        t = math.radians(a / 10)
        for k, col in ((0, L3), (1, L1)):
            x, y = int(C + (r - k) * math.cos(t)), int(C + (r - k) * math.sin(t))
            if keep(x, y, alpha):
                put(img, x, y, col)


def draw_flash(img: Image.Image, f: int) -> None:
    if f > 1:
        return
    r = 28 if f == 0 else 15
    d = ImageDraw.Draw(img)
    d.ellipse((C - r, C - r, C + r, C + r), fill=W1)
    d.ellipse((C - r + 3, C - r + 3, C + r - 3, C + r - 3), fill=W2)


# ---------------------------------------------------------------- 렌더
def render(f: int) -> Image.Image:
    ground = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_cracks(ground, f)
    draw_crater(ground, f)
    shadows = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bodies = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # 판은 위(먼 쪽)부터 그려 아래 판이 앞에 오게
    for s in sorted(slabs, key=lambda s: math.sin(s.ang)):
        s.draw(shadows, bodies, f)
    rock_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for r in sorted(rocks, key=lambda r: (r.state(f) or (0, 0, 0, 0))[1]):
        r.draw(shadows, rock_layer, f)
    for c in chips:
        c.draw(rock_layer, f)
    # 그림자는 디더로 반투명하게
    sp = shadows.load()
    for y in range(S):
        for x in range(S):
            if sp[x, y][3] and not keep(x, y, 0.55):
                sp[x, y] = (0, 0, 0, 0)
    dust = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for p in puffs:
        p.draw(dust, f)
    fx = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_ring(fx, f)
    draw_flash(fx, f)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for layer in (ground, shadows, bodies, rock_layer, dust, fx):
        out.alpha_composite(layer)
    return out


def main() -> None:
    frames = [render(f) for f in range(FRAMES)]
    cols = 6
    rows = math.ceil(FRAMES / cols)
    sheet = Image.new("RGBA", (S * cols, S * rows), (0, 0, 0, 0))
    meta = {"frames": [], "meta": {"fps": FPS, "frame_size": [S, S], "anchor": [C, C], "loop": False,
                                   "note": "가운데(anchor)가 발 구르는 지점. 원본 1x, 게임은 RENDER_SCALE 로 nearest 확대."}}
    for i, fr in enumerate(frames):
        x, y = (i % cols) * S, (i // cols) * S
        sheet.paste(fr, (x, y))
        meta["frames"].append({"frame": {"x": x, "y": y, "w": S, "h": S}, "duration": round(1000 / FPS)})
    sheet.save(OUT / "golem_stomp_sheet.png")
    game_dir = ROOT / "assets" / "images" / "effects"   # 게임이 읽는 사본 (config.GOLEM_STOMP_EFFECT)
    game_dir.mkdir(parents=True, exist_ok=True)
    sheet.save(game_dir / "golem_stomp.png")
    (OUT / "golem_stomp_sheet.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    # 게임 배율 미리보기: 바닥까지 화면 전체가 같이 흔들림 (카메라 흔들기)
    golem = Image.open(ROOT / "assets/concepts/pixellab/golem_simple/rotations/south.png").convert("RGBA")
    T, N, SC = 32, 10, 2
    W = N * T
    cx = cy = W // 2
    floor = Image.new("RGBA", (W, W), (88, 84, 80, 255))
    fd = ImageDraw.Draw(floor)
    for x in range(0, W, T):
        for y in range(0, W, T):
            fd.rectangle((x, y, x + T - 1, y + T - 1), outline=(76, 72, 68, 255))
    fd.rectangle((T, T, 9 * T - 1, 9 * T - 1), outline=(120, 190, 220, 255))
    shake = [(0, 0), (4, -2), (-4, 2), (3, 1), (-2, -1), (1, 0)]
    seq = [None] * 4 + list(range(FRAMES)) + [None] * 6
    out = []
    for i, f in enumerate(seq):
        world = floor.copy()
        if f is not None:
            world.alpha_composite(frames[f], (cx - C, cy - C))
        world.alpha_composite(golem, (cx - 48, cy - 76))
        sx, sy = shake[f] if f is not None and f < len(shake) else (0, 0)
        screen = Image.new("RGBA", (W, W), (30, 28, 32, 255))
        screen.alpha_composite(world, (sx, sy))
        out.append(screen.resize((W * SC, W * SC), Image.NEAREST))
    out[0].save(OUT / "golem_stomp_ingame_preview.gif", save_all=True, append_images=out[1:],
                duration=round(1000 / FPS), loop=0, disposal=2)
    for name, f in (("impact", 3), ("rising", 4), ("peak", 8), ("settled", 16), ("sinking", 22), ("fading", 25)):
        out[4 + f].save(OUT / f"golem_stomp_ingame_{name}.png")
    print("ok", len(frames))


if __name__ == "__main__":
    main()
