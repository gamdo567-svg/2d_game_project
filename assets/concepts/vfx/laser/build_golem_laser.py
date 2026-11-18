"""골렘 ④ 코어 레이저 이펙트 생성기 (2026-11-18 사용자 요청).

세 장을 만든다 (색은 골렘 코어의 하얀·옅은 하늘색 계열, 사라질 때는 바이어 점무늬로 흩어짐):
1. golem_laser_charge.png  충전 구. 64×64 칸, 가로 4 × 세로 12.
   줄(세로) = 크기 단계 0~11 (작은 빛 → 다 큰 구, 마지막 단계는 꽉 차 번쩍임),
   칸(가로) = 빨려 드는 빛 알갱이 위치 4단계 (시간으로 돌려 반짝임).
   게임은 충전 진행도로 줄을, 지난 시간으로 칸을 고른다.
2. golem_laser_beam.png    하얀 레이저 단면 (4×12). 코어에서 조준점까지 늘리고 돌려 그린다.
3. golem_laser_blast.png   조준점 폭발. 160×160 칸 16장 (가로 한 줄), 가운데가 조준점.
   흰 섬광 → 퍼지는 충격 고리 → 흩어지는 불꽃·돌 파편 → 아무것도 남지 않음.

출력: assets/images/effects/ 에 세 장, 이 폴더에 미리보기 golem_laser_preview.gif
실행: python build_golem_laser.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
GAME = ROOT / "images" / "effects"

# 골렘 코어 색 (south.png 에서 뽑음) + 빛 둘레의 푸른 기운
W = (250, 254, 254, 255)
P1 = (238, 248, 254, 255)
P2 = (217, 232, 245, 255)
P3 = (191, 213, 233, 255)
P4 = (160, 180, 196, 255)
G1 = (140, 200, 255, 255)
G2 = (90, 140, 220, 255)
G3 = (52, 82, 160, 255)
# 돌 파편 (골렘 팔레트)
K = (5, 4, 6, 255)
D3 = (49, 51, 67, 255)
M3 = (86, 96, 101, 255)
L2 = (121, 131, 134, 255)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def keep(x: int, y: int, alpha: float) -> bool:
    return (BAYER[y % 4][x % 4] + 0.5) / 16 < alpha


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def ease_out(t: float) -> float:
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def put(img: Image.Image, x: float, y: float, c) -> None:
    x, y = int(round(x)), int(round(y))
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)


def disk(img, cx, cy, r, color, alpha=1.0, wobble=None):
    """채운 원. wobble(angle) 이 있으면 테두리를 흔든다. alpha < 1 이면 점무늬로 듬성듬성."""
    for y in range(int(cy - r - 3), int(cy + r + 4)):
        for x in range(int(cx - r - 3), int(cx + r + 4)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            rr = r + (wobble(math.atan2(dy, dx)) if wobble else 0.0)
            if dx * dx + dy * dy <= rr * rr and keep(x, y, alpha):
                put(img, x, y, color)


def ring(img, cx, cy, r_in, r_out, color, alpha=1.0):
    for y in range(int(cy - r_out - 1), int(cy + r_out + 2)):
        for x in range(int(cx - r_out - 1), int(cx + r_out + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r_in <= d <= r_out and keep(x, y, alpha):
                put(img, x, y, color)


# ---------------------------------------------------------------- 1. 충전 구
CS = 64
STAGES = 12
PHASES = 4


def charge_frame(stage: int, phase: int) -> Image.Image:
    img = Image.new("RGBA", (CS, CS), (0, 0, 0, 0))
    c = CS / 2
    p = stage / (STAGES - 1)
    full = stage == STAGES - 1
    r = 2.0 + 16.0 * ease_out(p * 1.05)
    rng = random.Random(stage * 7 + phase)
    # 빨려 드는 빛 알갱이: 바깥에서 가운데로 휘며 들어온다 (많아지고 빨라짐)
    count = 8 + int(16 * p)
    for k in range(count):
        a0 = k * 2.399 + stage * 0.3
        t = ((phase / PHASES) + k * 0.37) % 1.0  # 0 = 바깥, 1 = 구에 닿음
        dist = r + 3 + (30 - r) * (1 - t)
        a = a0 + t * 0.9
        x, y = c + math.cos(a) * dist, c + math.sin(a) * dist
        col = P1 if t > 0.5 else G1
        disk(img, x, y, 1.0, col)
        tail = 2 if p > 0.4 else 1  # 들어오는 방향 반대로 꼬리
        for j in range(1, tail + 1):
            d2 = dist + j * 1.3
            put(img, c + math.cos(a - 0.08 * j) * d2, c + math.sin(a - 0.08 * j) * d2, G2)
    # 푸른 기운 (점무늬)
    glow = 0.35 + 0.25 * p + (0.15 if phase % 2 else 0.0)
    disk(img, c, c, r + 3 + p * 2, G3, glow * 0.7)
    disk(img, c, c, r + 1.5 + p, G2, glow)
    # 구: 테두리가 살짝 일렁인다
    wob = lambda a: 0.6 * math.sin(a * 5 + phase * 1.6 + stage)  # noqa: E731
    disk(img, c, c, r, G1, wobble=wob)
    disk(img, c, c, r * 0.8, P3, wobble=wob)
    disk(img, c, c, r * 0.6, P1)
    disk(img, c, c, max(0.8, r * 0.38), W)
    if full:  # 다 컸다: 번쩍이며 가장자리까지 하얗게, 십자 빛줄기
        disk(img, c, c, r * 0.85 if phase % 2 else r * 0.7, W)
        arm = r + 5 + (phase % 2) * 3
        for i in range(int(r), int(arm)):
            for col_x, col_y in ((c + i, c), (c - i, c), (c, c + i), (c, c - i)):
                put(img, col_x, col_y, W if i < arm - 2 else P2)
    # 반짝이는 하이라이트 (왼쪽 위)
    if r > 3:
        put(img, c - r * 0.35, c - r * 0.45, W)
        put(img, c - r * 0.35 + 1, c - r * 0.45, W)
    return img


def build_charge() -> Image.Image:
    sheet = Image.new("RGBA", (CS * PHASES, CS * STAGES), (0, 0, 0, 0))
    for s in range(STAGES):
        for ph in range(PHASES):
            sheet.alpha_composite(charge_frame(s, ph), (ph * CS, s * CS))
    return sheet


# ---------------------------------------------------------------- 2. 레이저 단면
def build_beam() -> Image.Image:
    rows = [G2, G1, P3, P2, P1, W, W, P1, P2, P3, G1, G2]
    img = Image.new("RGBA", (4, len(rows)), (0, 0, 0, 0))
    for y, col in enumerate(rows):
        for x in range(4):
            img.putpixel((x, y), col)
    return img


# ---------------------------------------------------------------- 3. 폭발
BS = 160
BF = 16


def build_blast() -> list[Image.Image]:
    rng = random.Random(4)
    c = BS / 2
    sparks = [(rng.uniform(0, 2 * math.pi), rng.uniform(40, 78), rng.uniform(0.55, 1.0)) for _ in range(30)]
    rocks = [(rng.uniform(0, 2 * math.pi), rng.uniform(22, 50), rng.uniform(10, 22), rng.choice((3, 4)))
             for _ in range(10)]
    frames = []
    for f in range(BF):
        t = f / (BF - 1)
        img = Image.new("RGBA", (BS, BS), (0, 0, 0, 0))
        # 바닥에 번지는 푸른 빛 (점점 옅어짐)
        glow = clamp01(1 - t * 1.6)
        if glow > 0:
            disk(img, c, c, 40 + 24 * ease_out(t * 2), G2, glow * 0.18)
        # 충격 고리: 퍼지며 얇아지고 점무늬로 흩어진다
        if 1 <= f <= 11:
            k = (f - 1) / 10
            rr = 26 + 50 * ease_out(k)
            width = 7 * (1 - k) + 1.5
            col = W if k < 0.25 else (P2 if k < 0.55 else G1)
            ring(img, c, c, rr - width, rr, col, clamp01(1.15 - k))
            ring(img, c, c, rr - width - 2, rr - width, G2, clamp01(0.9 - k))
        # 불덩이 (가운데): 처음 꽉 찼다가 줄며 흩어짐
        core = clamp01(1.1 - t * 1.8)
        if core > 0:
            r = 46 * (0.6 + 0.4 * ease_out(min(1, f / 2))) * (0.5 + 0.5 * core)
            wob = lambda a, f=f: 2.0 * math.sin(a * 6 + f)  # noqa: E731
            disk(img, c, c, r + 3, G1, core, wob)
            disk(img, c, c, r, P2, min(1, core * 1.2), wob)
            disk(img, c, c, r * 0.72, P1, min(1, core * 1.4))
            disk(img, c, c, r * 0.45, W)
        if f == 0:  # 첫 장: 화면을 찌르는 흰 섬광 십자
            for i in range(-64, 65):
                for w in (-1, 0, 1):
                    put(img, c + i, c + w, W)
                    put(img, c + w, c + i, W)
        # 불꽃: 바깥으로 날아가며 꼬리를 끌고 식는다
        for a, dist, spd in sparks:
            k = clamp01(t * 1.4 * spd + 0.05)
            if k >= 1 or f == 0:
                continue
            d = 10 + dist * ease_out(k)
            x, y = c + math.cos(a) * d, c + math.sin(a) * d
            col = W if k < 0.3 else (P2 if k < 0.6 else G1)
            if keep(int(x), int(y), clamp01(1.2 - k)):
                disk(img, x, y, 1.2 if k < 0.5 else 0.8, col)
                for j in range(2, 6 if k < 0.5 else 3):
                    put(img, x - math.cos(a) * j, y - math.sin(a) * j, G2)
        # 돌 파편: 튀어 올랐다(화면 위쪽으로) 떨어지며 작아지고, 땅에 닿으면 흩어진다
        for a, dist, height, size in rocks:
            k = clamp01((f - 1) / 11)
            if f < 1 or k >= 1:
                continue
            d = dist * ease_out(k)
            x = c + math.cos(a) * d
            y = c + math.sin(a) * d * 0.6 - height * 4 * k * (1 - k)
            if not keep(int(x), int(y), clamp01(1.4 - k)):
                continue
            for oy in range(-1, size + 1):
                for ox in range(-1, size + 1):
                    edge = ox in (-1, size) or oy in (-1, size)
                    put(img, x + ox, y + oy, K if edge else (L2 if oy == 0 else (M3 if oy < size - 1 else D3)))
        frames.append(img)
    return frames


def main() -> None:
    GAME.mkdir(parents=True, exist_ok=True)
    charge = build_charge()
    charge.save(GAME / "golem_laser_charge.png")
    build_beam().save(GAME / "golem_laser_beam.png")
    blast = build_blast()
    sheet = Image.new("RGBA", (BS * BF, BS), (0, 0, 0, 0))
    for i, fr in enumerate(blast):
        sheet.alpha_composite(fr, (i * BS, 0))
    sheet.save(GAME / "golem_laser_blast.png")

    # 미리보기: 어두운 바닥 위에 충전(빠르게) → 레이저 → 폭발, 2배
    golem = Image.open(ROOT / "images" / "golem" / "south.png").convert("RGBA")
    W_, H_ = 360, 300
    gx, gy = 40, 170  # 골렘 그림 왼쪽 위
    core = (gx + 48, gy + 44)
    aim = (270, 120)
    seq = []

    def base():
        im = Image.new("RGBA", (W_, H_), (24, 24, 30, 255))
        for x in range(0, W_, 32):
            for y in range(H_):
                im.putpixel((x, y), (34, 34, 42, 255))
        for y in range(0, H_, 32):
            for x in range(W_):
                im.putpixel((x, y), (34, 34, 42, 255))
        im.alpha_composite(golem, (gx, gy))
        return im

    for i in range(STAGES * 2):
        im = base()
        st = min(STAGES - 1, i // 2)
        im.alpha_composite(charge.crop(((i % PHASES) * CS, st * CS, (i % PHASES + 1) * CS, (st + 1) * CS)),
                           (core[0] - CS // 2, core[1] - CS // 2))
        seq.append(im)
    beam = build_beam()
    length = math.hypot(aim[0] - core[0], aim[1] - core[1])
    ang = math.degrees(math.atan2(-(aim[1] - core[1]), aim[0] - core[0]))
    for thick in (16, 12, 6):
        im = base()
        b = beam.resize((int(length), thick), Image.NEAREST).rotate(ang, expand=True, resample=Image.NEAREST)
        im.alpha_composite(b, (int((core[0] + aim[0]) / 2 - b.width / 2), int((core[1] + aim[1]) / 2 - b.height / 2)))
        seq.append(im)
    for fr in blast:
        im = base()
        im.alpha_composite(fr, (aim[0] - BS // 2, aim[1] - BS // 2))
        seq.append(im)
    seq = [s.resize((W_ * 2, H_ * 2), Image.NEAREST) for s in seq]
    durations = [80] * (STAGES * 2) + [50] * 3 + [55] * BF
    seq[0].save(OUT / "golem_laser_preview.gif", save_all=True, append_images=seq[1:], duration=durations,
                loop=0, disposal=2)
    print("ok", charge.size, sheet.size)


if __name__ == "__main__":
    main()
