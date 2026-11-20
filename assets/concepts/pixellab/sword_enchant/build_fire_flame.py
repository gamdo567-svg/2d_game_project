"""검 불 이펙트 — 타오르는 불꽃 오러 (2026-11-20 사용자: 오러가 불꽃이 나오는 느낌이 아니라 레이저 검처럼 보임).

매끈한 빛 띠 대신, 칼날 가장자리에서 불꽃 덩어리(입자)가 끊임없이 생겨 칼끝 쪽·바깥으로 날리며 줄어들고 식는다.
가까운 덩어리끼리는 열이 더해져 하나의 불꽃 혀로 붙고, 끝에서는 떨어져 나가 작은 불덩이로 흩어진다 (실제 불처럼 들쭉날쭉).
- 열(heat) = 덩어리마다 (1 - 거리/반지름) × 세기 의 합. 열이 높을수록 흰빛 → 노랑 → 주황 → 빨강 → 검붉음.
- 덩어리는 태어날 때 뜨겁고 크며, 날아가며 반지름·세기가 줄어든다.
- 아래에 옅은 붉은 빛(오러)을 칼날 둘레에 깔아 불이 칼을 감싼 느낌.
- 반복이 끊기지 않게 덩어리마다 태어나는 때를 한 바퀴(0~1) 안에 두고 나이 = (t - 태어난 때) mod 1.
칼 그림 방향(칼끝 오른쪽, 손 (40, 12)) 80×24 프레임 FRAMES 장. 출력: assets/images/effects/sword_enchant/fire.png
"""
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'images', 'effects', 'sword_enchant')
SWORD = os.path.join(ROOT, 'assets', 'images', 'player', 'weapons', 'old_sword.png')
W, H = 80, 24
FRAMES = 24
SWORD_AT = (12, 7)
BLADE_FROM_X = 45
TOP_EDGE, BOTTOM_EDGE, MID_Y = 9, 13, 11
SEED = 5
COUNT = 170  # 불꽃 덩어리 수

# 열 문턱 → 색 (높은 것부터)
HEAT_COLOURS = [
    (2.1, (255, 248, 214, 255)),  # 흰빛
    (1.3, (255, 210, 84, 255)),   # 노랑
    (0.68, (255, 142, 36, 250)),   # 주황
    (0.40, (232, 74, 28, 230)),    # 빨강
    (0.20, (150, 36, 28, 190)),    # 검붉음 (불꽃 가장자리)
]
GLOW = [(255, 120, 40, 90), (220, 60, 30, 55)]  # 칼날 둘레 옅은 빛 (안쪽, 바깥)


def blade_pixels():
    sword = Image.open(SWORD).convert('RGBA')
    px = sword.load()
    return {(x + SWORD_AT[0], y + SWORD_AT[1]) for y in range(sword.height) for x in range(sword.width)
            if px[x, y][3] and x + SWORD_AT[0] >= BLADE_FROM_X}


def make_particles(tip):
    rnd = random.Random(SEED)
    out = []
    for n in range(COUNT):
        at_tip = n % 7 == 0
        side = rnd.choice((-1, 1))
        if at_tip:
            x0, y0 = tip - rnd.uniform(0, 2), MID_Y + rnd.uniform(-1.5, 1.5)
            vx, vy = rnd.uniform(9, 15), rnd.uniform(-1.5, 1.5)
        else:
            u = rnd.random()  # 칼날 전체에 고르게
            x0 = BLADE_FROM_X + 1 + u * (tip - BLADE_FROM_X - 1)
            y0 = (TOP_EDGE - 0.5) if side < 0 else (BOTTOM_EDGE + 0.5)
            vx, vy = rnd.uniform(3, 8), side * rnd.uniform(1.5, 4.5)
        out.append({
            'x0': x0, 'y0': y0, 'vx': vx, 'vy': vy,
            'r0': rnd.uniform(2.3, 3.8) * (0.75 + 0.5 * (x0 - BLADE_FROM_X) / (tip - BLADE_FROM_X)),
            'life': rnd.uniform(0.18, 0.32),  # 한 바퀴(2초) 중 비율
            'born': rnd.random(),
            'wig': rnd.uniform(0.6, 1.6), 'ph': rnd.uniform(0, 6.28),
        })
    return out


def draw_frame(i, blade, parts):
    t = i / FRAMES
    heat = [[0.0] * W for _ in range(H)]
    for p in parts:
        age = ((t - p['born']) % 1.0) / p['life']
        if age >= 1.0:
            continue
        # 날아가며 칼끝 쪽으로 가속, 바깥으로 퍼짐, 좌우로 흔들림
        cx = p['x0'] + p['vx'] * age ** 1.2
        cy = p['y0'] + p['vy'] * age + p['wig'] * math.sin(p['ph'] + age * 9) * age
        r = p['r0'] * (1 - 0.75 * age)
        strength = 1.25 * (1 - age) ** 0.7
        for y in range(max(0, int(cy - r - 1)), min(H, int(cy + r + 2))):
            for x in range(max(0, int(cx - r - 1)), min(W, int(cx + r + 2))):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d < r:
                    heat[y][x] += (1 - d / r) * strength
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    # 옅은 빛: 칼날 바로 둘레 1~2 픽셀
    for (bx, by) in blade:
        for dy in (-2, -1, 1, 2):
            for dx in (-1, 0, 1):
                x, y = bx + dx, by + dy
                if 0 <= x < W and 0 <= y < H and (x, y) not in blade and x >= BLADE_FROM_X:
                    c = GLOW[0] if abs(dy) == 1 else GLOW[1]
                    if px[x, y][3] < c[3]:
                        px[x, y] = c
    for y in range(H):
        for x in range(W):
            if (x, y) in blade:
                continue
            h = heat[y][x]
            for limit, colour in HEAT_COLOURS:
                if h >= limit:
                    px[x, y] = colour
                    break
    return im


def main():
    blade = blade_pixels()
    parts = make_particles(max(x for x, _ in blade))
    strip = Image.new('RGBA', (W * FRAMES, H), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.alpha_composite(draw_frame(i, blade, parts), (i * W, 0))
    os.makedirs(OUT, exist_ok=True)
    strip.save(os.path.join(OUT, 'fire.png'))
    print('fire flame', FRAMES)


if __name__ == '__main__':
    main()
