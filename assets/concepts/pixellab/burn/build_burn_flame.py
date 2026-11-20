"""불 붙은 몸에서 타오르는 불꽃 혀 (2026-11-20 사용자: 불타는 느낌이 전혀 안 듦 → 불 이펙트를 잘 만들어 달라).

칼 불꽃(sword_enchant/build_fire_flame.py)과 같은 방법: 바닥 줄에서 불꽃 덩어리가 끊임없이 생겨 위로 솟으며
흔들리고 줄어들고 식는다. 가까운 덩어리는 열이 더해져 한 덩어리 불꽃 혀가 되고, 꼭대기에서는 떨어져 나가
작은 불덩이로 흩어진다. 아래는 넓고 뜨겁고(흰빛·노랑) 위로 갈수록 가늘게 갈라지며 주황 → 빨강 → 검붉게 식는다.
반복이 끊기지 않게 덩어리마다 태어나는 때를 한 바퀴(0~1) 안에 두고 나이 = (t - 태어난 때) mod 1.
출력: assets/images/effects/burn/flame.png (W×H 프레임 FRAMES 장, 아래 가운데 = 불이 붙은 자리).
"""
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'images', 'effects', 'burn')
W, H = 24, 40
FRAMES = 16
BASE_Y = H - 4  # 불이 붙은 줄 (위에서부터)
SEED = 11
COUNT = 170

HEAT_COLOURS = [
    (3.0, (255, 248, 214, 255)),  # 흰빛
    (1.8, (255, 214, 90, 255)),   # 노랑
    (0.95, (255, 146, 38, 255)),  # 주황
    (0.5, (232, 76, 28, 240)),   # 빨강
    (0.22, (140, 34, 26, 200)),   # 검붉음 (가장자리)
]


def make_particles():
    rnd = random.Random(SEED)
    out = []
    for _ in range(COUNT):
        x0 = W / 2 + rnd.gauss(0, 2.2)
        out.append({
            'x0': x0, 'y0': BASE_Y + rnd.uniform(-1, 2),
            'rise': rnd.uniform(22, 36),  # 일생 동안 오르는 높이
            'drift': (W / 2 - x0) * rnd.uniform(0.5, 0.9),  # 위로 가며 가운데로 모임 (혀 모양)
            'r0': rnd.uniform(2.4, 3.8),
            'life': rnd.uniform(0.25, 0.45),
            'born': rnd.random(),
            'wig': rnd.uniform(1.0, 2.6), 'ph': rnd.uniform(0, 6.28), 'freq': rnd.uniform(6, 11),
        })
    return out


def draw_frame(i, parts):
    t = i / FRAMES
    heat = [[0.0] * W for _ in range(H)]
    for p in parts:
        age = ((t - p['born']) % 1.0) / p['life']
        if age >= 1.0:
            continue
        cy = p['y0'] - p['rise'] * age ** 1.15
        cx = p['x0'] + p['drift'] * age + p['wig'] * math.sin(p['ph'] + age * p['freq']) * age
        r = p['r0'] * (1 - 0.8 * age)
        strength = 1.15 * (1 - age) ** 0.9
        for y in range(max(0, int(cy - r * 2.2 - 1)), min(H, int(cy + r + 2))):
            for x in range(max(0, int(cx - r - 1)), min(W, int(cx + r + 2))):
                dy = y + 0.5 - cy
                dy = dy / 2.2 if dy < 0 else dy  # 위로 길쭉 (혀)
                d = math.hypot(x + 0.5 - cx, dy)
                if d < r:
                    heat[y][x] += (1 - d / r) * strength
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    for y in range(H):
        for x in range(W):
            for limit, colour in HEAT_COLOURS:
                if heat[y][x] >= limit:
                    px[x, y] = colour
                    break
    return im


def main():
    parts = make_particles()
    strip = Image.new('RGBA', (W * FRAMES, H), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.alpha_composite(draw_frame(i, parts), (i * W, 0))
    os.makedirs(OUT, exist_ok=True)
    strip.save(os.path.join(OUT, 'flame.png'))
    print('burn flame', FRAMES)


if __name__ == '__main__':
    main()
