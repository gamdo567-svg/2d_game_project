"""골렘 죽음 동작 시트를 계산해 그린다 (2026-11-18 사용자 요청).

지금 골렘 서 있는 그림(assets/images/golem/<dir>.png, 96×96)을 그대로 쓴다. 그림은 검은 테두리로 나뉜 돌덩이로
되어 있어, 테두리가 아닌 픽셀의 덩어리를 부위로 삼는다 (작은 덩어리와 테두리는 가장 가까운 큰 덩어리에 붙임).
동작 (12fps):
  1. 꺼짐 (0~0.5초): 코어와 눈의 푸른 흰빛이 어두운 돌색으로 식는다. 끝 무렵 몸이 1픽셀씩 떨린다.
  2. 무너짐 (0.5~1.6초): 돌덩이가 따로따로 떨어진다. 바깥쪽 돌은 바깥으로 튕기고, 위쪽 돌일수록 늦게 떨어져
     아래에서부터 무너지는 느낌. 중력·바닥 튕김·마찰·조금씩 기울어짐. 바닥은 돌마다 조금 앞뒤로 달라 돌무더기가 된다.
  3. 돌무더기 (1.6~2.7초): 가만히 있음.
  4. 사라짐 (2.7~3.7초): 돌무더기 전체가 고르게 투명해지며 사라진다 (2026-11-18 디더에서 바꿈).
같은 결과가 나오도록 난수 시드를 고정한다. 서쪽은 동쪽을 좌우 반전.
출력: assets/images/golem/death_<dir>.png (가로 한 줄 FRAMES 장, 한 장 CANVAS), golem_death_preview.gif
실행: python build_golem_death.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / "assets" / "images" / "golem"
CANVAS = (176, 120)
FOOT = (88, 104)  # 발 밑 가운데 (게임이 발 칸 바닥 가운데에 맞춘다)
FPS = 12
T_OFF, T_FALL, T_REST, T_FADE = 0.5, 1.1, 1.1, 1.0
FRAMES = round((T_OFF + T_FALL + T_REST + T_FADE) * FPS)
GRAVITY = 520.0  # 원본 픽셀/초²
SEED_MIN = 40  # 이보다 작은 돌덩이는 옆 돌에 붙인다

# 코어·눈의 빛 (푸른 흰색) → 꺼진 돌색 (밝을수록 꺼진 뒤에도 조금 밝게)
GLOW = [(250, 254, 254), (238, 248, 254), (217, 232, 245), (212, 222, 226), (191, 213, 233), (175, 201, 226),
        (160, 180, 196)]
OFF = [(78, 82, 92), (74, 78, 88), (70, 74, 84), (68, 72, 80), (64, 68, 78), (60, 64, 74), (58, 62, 70)]


def is_outline(c) -> bool:
    return max(c[:3]) < 40


def foot_of(img: Image.Image) -> tuple[int, int]:
    px = img.load()
    w, h = img.size
    bottom = max(y for y in range(h) for x in range(w) if px[x, y][3])
    xs = [x for y in range(bottom - 5, bottom + 1) for x in range(w) if px[x, y][3]]
    return (min(xs) + max(xs)) // 2, bottom


def split_parts(img: Image.Image) -> list[dict]:
    """돌덩이 부위로 나눈다: [{"pixels": {(x, y): color}, ...}]."""
    px = img.load()
    w, h = img.size
    opaque = {(x, y) for y in range(h) for x in range(w) if px[x, y][3]}
    inner = {p for p in opaque if not is_outline(px[p])}
    comps, seen = [], set()
    for p in sorted(inner):
        if p in seen:
            continue
        comp, stack = [], [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in inner and q not in seen:
                    seen.add(q)
                    stack.append(q)
        comps.append(comp)
    seeds = [c for c in comps if len(c) >= SEED_MIN]
    owner = {}
    frontier = []
    for i, comp in enumerate(seeds):
        for p in comp:
            owner[p] = i
            frontier.append(p)
    # 나머지(테두리·작은 덩어리)는 가장 가까운 큰 돌에 붙인다 (동시에 한 칸씩 넓히기)
    while frontier:
        nxt = []
        for x, y in frontier:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in opaque and q not in owner:
                    owner[q] = owner[(x, y)]
                    nxt.append(q)
        frontier = nxt
    parts = [{"pixels": {}} for _ in seeds]
    for p, i in owner.items():
        parts[i]["pixels"][p] = px[p]
    return parts


def part_image(part: dict, glow: float) -> tuple[Image.Image, tuple[int, int]]:
    """부위 하나를 자기 크기 그림으로 (glow: 1 = 원래 빛, 0 = 꺼짐). (그림, 왼쪽 위)."""
    xs = [x for x, _ in part["pixels"]]
    ys = [y for _, y in part["pixels"]]
    x0, y0 = min(xs), min(ys)
    img = Image.new("RGBA", (max(xs) - x0 + 1, max(ys) - y0 + 1), (0, 0, 0, 0))
    ipx = img.load()
    for (x, y), c in part["pixels"].items():
        if c[:3] in GLOW:
            off = OFF[GLOW.index(c[:3])]
            c = tuple(round(off[k] + (c[k] - off[k]) * glow) for k in range(3)) + (255,)
        ipx[x - x0, y - y0] = c
    return img, (x0, y0)


def simulate(parts: list[dict], body_box: tuple[int, int, int, int], rng: random.Random) -> list[list[tuple]]:
    """부위마다 무너짐 동안의 (dx, dy, 각도) 를 프레임마다. 좌표는 원래 자리에서 옮긴 양 (원본 픽셀)."""
    bx0, by0, bx1, by1 = body_box
    cx = (bx0 + bx1) / 2
    steps = round(T_FALL * FPS)
    sub = 8
    dt = 1.0 / FPS / sub
    paths = []
    for part in parts:
        xs = [x for x, _ in part["pixels"]]
        ys = [y for _, y in part["pixels"]]
        pcx, ptop, pbot = (min(xs) + max(xs)) / 2, min(ys), max(ys)
        height_ratio = (by1 - pbot) / max(1, by1 - by0)  # 0 = 발, 1 = 머리 꼭대기
        delay = 0.05 + height_ratio * 0.18 + rng.uniform(0, 0.06)  # 아래부터 무너짐
        side = (pcx - cx) / max(1, (bx1 - bx0) / 2)
        vx = side * rng.uniform(28, 46) + rng.uniform(-8, 8)
        vy = -rng.uniform(10, 40) * (0.4 + height_ratio)  # 화면 위가 - (조금 튀어 오름)
        spin = rng.uniform(-110, 110) * (0.5 + abs(side))
        ground = by1 + rng.uniform(-10, 3)  # 돌마다 앞뒤로 다른 바닥 → 무더기
        x = y = ang = 0.0
        resting = False
        path = []
        t = 0.0
        for _ in range(steps):
            for _ in range(sub):
                t += dt
                if t < delay or resting:
                    continue
                vy += GRAVITY * dt
                x += vx * dt
                y += vy * dt
                ang += spin * dt
                if pbot + y >= ground:  # 바닥에 닿음: 튕기고 미끄러짐이 줄어듦
                    y = ground - pbot
                    if abs(vy) < 40:
                        resting = True
                        vx = vy = spin = 0.0
                    else:
                        vy = -vy * 0.28
                        vx *= 0.55
                        spin *= 0.5
            path.append((x, y, ang))
        paths.append(path)
    return paths


def render(view_img: Image.Image, seed: int) -> list[Image.Image]:
    rng = random.Random(seed)
    parts = split_parts(view_img)
    body_box = view_img.getchannel("A").getbbox()
    body_box = (body_box[0], body_box[1], body_box[2] - 1, body_box[3] - 1)
    fx, fy = foot_of(view_img)
    ox, oy = FOOT[0] - fx, FOOT[1] - fy  # 원본 → 캔버스
    paths = simulate(parts, body_box, rng)
    n_off, n_fall, n_rest = round(T_OFF * FPS), round(T_FALL * FPS), round(T_REST * FPS)
    frames = []
    for f in range(FRAMES):
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        glow = max(0.0, 1.0 - f / max(1, n_off - 2))
        shake = (f % 2) * 2 - 1 if n_off - 3 <= f < n_off else 0
        k = f - n_off
        placed = []
        for i, part in enumerate(parts):
            img, (x0, y0) = part_image(part, glow)
            dx = dy = ang = 0.0
            if k >= 0:
                dx, dy, ang = paths[i][min(k, n_fall - 1)]
            if abs(ang) > 1:
                w0, h0 = img.size
                img = img.rotate(ang, resample=Image.NEAREST, expand=True)
                x0 -= (img.width - w0) / 2
                y0 -= (img.height - h0) / 2
            placed.append((y0 + dy + img.height, img, round(x0 + dx + ox + shake), round(y0 + dy + oy)))
        for _, img, x, y in sorted(placed, key=lambda p: p[0]):  # 아래(앞)에 있는 돌을 나중에
            canvas.alpha_composite(img, (x, y))
        fade_k = f - (n_off + n_fall + n_rest)
        if fade_k >= 0:
            # 돌무더기 전체가 고르게 투명해진다 (2026-11-18 사용자 요청: 디더로 듬성듬성 사라지면 노이즈처럼 보임)
            alpha = 1.0 - (fade_k + 1) / (round(T_FADE * FPS) + 1)
            a = canvas.getchannel("A").point(lambda v: round(v * alpha))
            canvas.putalpha(a)
        frames.append(canvas)
    return frames


def main() -> None:
    views = {}
    for i, view in enumerate(("south", "east", "north")):
        views[view] = render(Image.open(SRC / f"{view}.png").convert("RGBA"), seed=11 + i)
    views["west"] = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in views["east"]]
    for view, frames in views.items():
        sheet = Image.new("RGBA", (CANVAS[0] * FRAMES, CANVAS[1]), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.alpha_composite(f, (i * CANVAS[0], 0))
        sheet.save(SRC / f"death_{view}.png")
    bg = (40, 44, 52, 255)
    gif = []
    for i in range(FRAMES):
        im = Image.new("RGBA", (CANVAS[0] * 4, CANVAS[1]), bg)
        for k, view in enumerate(("south", "east", "north", "west")):
            im.alpha_composite(views[view][i], (k * CANVAS[0], 0))
        gif.append(im.convert("RGB").resize((im.width * 2, im.height * 2), Image.NEAREST))
    w, h = gif[0].size
    big = Image.new("RGB", (w, h * len(gif)))
    for k, im in enumerate(gif):
        big.paste(im, (0, k * h))
    pal = big.quantize(colors=256, method=Image.MEDIANCUT, dither=0)
    out = [pal.crop((0, k * h, w, (k + 1) * h)) for k in range(len(gif))]
    out[0].save(HERE / "golem_death_preview.gif", save_all=True, append_images=out[1:] + [out[-1]] * 8,
                duration=round(1000 / FPS), loop=0)
    print("frames", FRAMES, "parts", {v: len(split_parts(Image.open(SRC / f"{v}.png").convert("RGBA")))
                                     for v in ("south", "east", "north")})


if __name__ == "__main__":
    main()
