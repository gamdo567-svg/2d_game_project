"""골렘 ① 두 손 내려찍기 충격 이펙트 프레임 생성기 (시안).

원본 해상도(1x) 160×160 캔버스, 가운데 (80, 80) 가 손이 땅에 닿는 지점 (앞 3×3칸의 가운데).
- 작은 충격 고리, 짧은 금(하얗게 번쩍인 뒤 어둡게 식음)
- 돌 파편: 포물선으로 튀어 그림자 위에 떨어지고 한 번 튐
- 먼지: 바깥으로 퍼지며 살짝 떠오르고 옅어짐
- 끝나면 아무것도 남지 않음 (픽셀 단위로 흩어짐)
색은 골렘 그림의 팔레트, 외곽선은 검정 (발 구르기 이펙트와 같은 규칙).

출력: 같은 폴더 golem_slam_impact_sheet.png (+ .json), 미리보기
실행: python build_golem_slam_impact.py
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
S = 160
C = S // 2
FRAMES = 16
FPS = 12

K = (5, 4, 6, 255)
D0 = (15, 14, 20, 255)
D1 = (24, 24, 34, 255)
D3 = (49, 51, 67, 255)
M1 = (57, 62, 76, 255)
M3 = (86, 96, 101, 255)
L1 = (110, 118, 123, 255)
L2 = (121, 131, 134, 255)
L3 = (148, 162, 163, 255)
W2 = (250, 254, 254, 255)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
rng = random.Random(11)


def keep(x, y, alpha):
    return (BAYER[y % 4][x % 4] + 0.5) / 16 < alpha


def clamp01(v):
    return max(0.0, min(1.0, v))


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def put(img, x, y, c):
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


# ---------------------------------------------------------------- 짧은 금
crack_px: dict[tuple[int, int], float] = {}
for i in range(7):
    a = math.radians(i * 360 / 7 + rng.uniform(-15, 15))
    r_end, r, pts = rng.uniform(22, 40), 5.0, []
    while r < r_end:
        pts.append((C + r * math.cos(a), C + r * math.sin(a)))
        r += rng.uniform(5, 8)
        a += math.radians(rng.uniform(-18, 18))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for x, y in line_pts(x0, y0, x1, y1):
            crack_px.setdefault((x, y), math.hypot(x - C, y - C))
crack_key = {p: rng.random() for p in crack_px}


def draw_cracks(img, f):
    reveal = 42 * ease_out(f / 2.0)
    fade = clamp01((f - 8) / 6)
    for (x, y), dist in crack_px.items():
        if dist > reveal or (fade > 0 and fade > crack_key[(x, y)] * 0.6 + (1 - dist / 42) * 0.4):
            continue
        if f < 2:
            put(img, x, y, W2)
        elif f < 3:
            put(img, x, y, L2)
        else:
            put(img, x, y, D0)
            if (x, y + 1) not in crack_px and img.getpixel((x, min(S - 1, y + 1)))[3] == 0:
                put(img, x, y + 1, M1)


# ---------------------------------------------------------------- 돌 파편
ROCKS = [
    [".1111..", "155431.", "1544321", "1433221", ".13221.", "..111.."],
    [".111.", "15431", "14321", ".111."],
    ["..111.", ".15431", "154321", "14321.", ".111.."],
    [".11.", "1541", "1321", ".11."],
]
ROCK_COL = {"1": K, "2": D3, "3": M1, "4": M3, "5": L3}


def rock_img(idx, flip):
    rows = ROCKS[idx]
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in ROCK_COL:
                im.putpixel((x, y), ROCK_COL[ch])
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


class Rock:
    def __init__(self):
        self.idx = rng.choice([0, 1, 1, 2, 3, 3])
        a = math.radians(rng.uniform(0, 360))
        d = rng.uniform(18, 58)
        self.s = (C + 4 * math.cos(a), C + 4 * math.sin(a))
        self.e = (C + d * math.cos(a), C + d * math.sin(a))
        self.b = (self.e[0] + 3 * math.cos(a), self.e[1] + 3 * math.sin(a))
        self.t0, self.T, self.peak = rng.uniform(0.3, 1.2), rng.uniform(4, 6), rng.uniform(10, 24)
        self.gone = rng.uniform(9, 12)

    def draw(self, shadow, body, f):
        u = (f - self.t0) / self.T
        if u < 0:
            return
        if u <= 1:
            gx, gy, h, fly = *(p + (q - p) * u for p, q in zip(self.s, self.e)), self.peak * 4 * u * (1 - u), True
        else:
            v = min(1.0, (f - self.t0 - self.T) / 1.5)
            gx, gy = (p + (q - p) * v for p, q in zip(self.e, self.b))
            h, fly = (3 * 4 * v * (1 - v), v < 1)
        fade = clamp01((f - self.gone) / 2.5)
        spr = rock_img(self.idx, fly and int(f) % 2 == 1)
        w, hh = spr.size
        if fade < 0.35 and h < 22:
            sw = max(2, int(w * (1 - h / 40)))
            ImageDraw.Draw(shadow).ellipse((int(gx - sw / 2), int(gy + hh / 2 - 1), int(gx + sw / 2), int(gy + hh / 2 + 1)),
                                           fill=D0)
        x0, y0 = int(round(gx - w / 2)), int(round(gy - hh / 2 - h))
        px = spr.load()
        for yy in range(hh):
            for xx in range(w):
                if px[xx, yy][3] and (fade == 0 or keep(x0 + xx, y0 + yy, 1 - fade)):
                    put(body, x0 + xx, y0 + yy, px[xx, yy])


rocks = [Rock() for _ in range(13)]


class Chip:
    def __init__(self):
        a = math.radians(rng.uniform(0, 360))
        d = rng.uniform(30, 70)
        self.s = (C + 3 * math.cos(a), C + 3 * math.sin(a))
        self.e = (C + d * math.cos(a), C + d * math.sin(a))
        self.t0, self.T, self.peak = rng.uniform(0.2, 1.0), rng.uniform(3, 5), rng.uniform(8, 20)
        self.col = rng.choice([M3, L1, D3])

    def draw(self, body, f):
        u = (f - self.t0) / self.T
        if u < 0 or u > 1.2:
            return
        u = min(u, 1)
        x = self.s[0] + (self.e[0] - self.s[0]) * u
        y = self.s[1] + (self.e[1] - self.s[1]) * u - self.peak * 4 * u * (1 - u)
        put(body, int(x), int(y), self.col)


chips = [Chip() for _ in range(22)]


class Puff:
    def __init__(self, ang):
        self.a = math.radians(ang)
        self.r0, self.r1 = rng.uniform(6, 12), rng.uniform(30, 52)
        self.z0, self.z1 = rng.uniform(4, 6), rng.uniform(7, 10)
        self.t0, self.life = rng.uniform(0.4, 1.2), rng.uniform(7, 10)

    def draw(self, img, f):
        u = (f - self.t0) / self.life
        if not 0 <= u <= 1:
            return
        e = ease_out(u * 1.4)
        r = self.r0 + (self.r1 - self.r0) * e
        cx, cy = C + r * math.cos(self.a), C + r * math.sin(self.a) * 0.8 - 6 * u
        rad = (self.z0 + (self.z1 - self.z0) * e) * (1 - 0.35 * clamp01((u - 0.55) / 0.45))
        alpha = 1 - clamp01((u - 0.55) / 0.45)
        for y in range(int(cy - rad - 1), int(cy + rad + 2)):
            for x in range(int(cx - rad - 1), int(cx + rad + 2)):
                dx, dy = x - cx + 0.5, y - cy + 0.5
                d = math.hypot(dx, dy)
                if d > rad or not keep(x, y, alpha):
                    continue
                side = (dx + dy) / (d or 1)
                col = (M1 if side > -0.3 else L1) if d > rad - 1.2 else (L3 if side < -0.45 and d > rad * 0.35
                                                                       else M3 if side > 0.45 else L2)
                put(img, x, y, col)


puffs = [Puff(i * 360 / 11 + rng.uniform(-12, 12)) for i in range(11)]


def draw_ring(img, f):
    if f > 3:
        return
    r = 8 + 38 * ease_out(f / 3)
    alpha = 1 - f / 4
    for a in range(0, 1440):
        t = math.radians(a / 4)
        x, y = int(C + r * math.cos(t)), int(C + r * math.sin(t) * 0.85)
        if keep(x, y, alpha):
            put(img, x, y, L3)
    if f == 0:
        ImageDraw.Draw(img).ellipse((C - 9, C - 8, C + 9, C + 8), fill=W2)


def render(f):
    ground = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_cracks(ground, f)
    shadows = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for r in rocks:
        r.draw(shadows, body, f)
    for c in chips:
        c.draw(body, f)
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
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for layer in (ground, shadows, body, dust, fx):
        out.alpha_composite(layer)
    return out


def main():
    frames = [render(f) for f in range(FRAMES)]
    cols = 8
    rows = math.ceil(FRAMES / cols)
    sheet = Image.new("RGBA", (S * cols, S * rows), (0, 0, 0, 0))
    meta = {"frames": [], "meta": {"fps": FPS, "frame_size": [S, S], "anchor": [C, C], "loop": False}}
    for i, fr in enumerate(frames):
        x, y = (i % cols) * S, (i // cols) * S
        sheet.paste(fr, (x, y))
        meta["frames"].append({"frame": {"x": x, "y": y, "w": S, "h": S}, "duration": round(1000 / FPS)})
    sheet.save(OUT / "golem_slam_impact_sheet.png")
    sheet.save(ROOT / "assets" / "images" / "effects" / "golem_slam.png")  # 게임이 읽는 사본 (config.GOLEM_SLAM_EFFECT)
    (OUT / "golem_slam_impact_sheet.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print("last frame empty:", frames[-1].getbbox() is None)
    return frames


if __name__ == "__main__":
    main()
