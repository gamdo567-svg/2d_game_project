"""불 붙은 몸에서 타오르는 불꽃 혀 (2026-11-20 사용자: 불타는 느낌이 전혀 안 듦 → 불 이펙트를 잘 만들어 달라).

칼 불꽃(sword_enchant/build_fire_flame.py)과 같은 방법: 바닥 줄에서 불꽃 덩어리가 끊임없이 생겨 위로 솟으며
흔들리고 줄어들고 식는다. 가까운 덩어리는 열이 더해져 한 덩어리 불꽃 혀가 되고, 꼭대기에서는 떨어져 나가
작은 불덩이로 흩어진다. 아래는 넓고 뜨겁고(흰빛·노랑) 위로 갈수록 가늘게 갈라지며 주황 → 빨강 → 검붉게 식는다.
반복이 끊기지 않게 덩어리마다 태어나는 때를 한 바퀴(0~1) 안에 두고 나이 = (t - 태어난 때) mod 1.
출력: assets/images/effects/burn/flame_<모양>_<크기>.png (프레임 FRAMES 장, 아래 가운데 = 불이 붙은 자리).

2% 다듬기 (같은 날 사용자: 횃불 그림체 말고 진짜 불 같은 픽셀 불, 지금은 2% 부족):
- 크기 4단계(s·m·l·xl)를 따로 그린다. 게임은 늘리거나 줄이지 않고 캐릭터와 같은 배율로만 그려 점 크기가 같다
  (예전엔 한 장을 0.5~1.4배로 늘려 점 크기가 들쭉날쭉해 다른 게임 그림 같았음).
- 외곽 정리: 가장자리에 흩날리는 외톨이 점을 지운다.
- 색: 탁한 갈색 테두리 → 선명한 진홍, 거의 흰 가운데 → 작고 따뜻한 연노랑.
"""
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'images', 'effects', 'burn')
BASE_W, BASE_H = 24, 40  # 크기 1.0 기준 (원본 픽셀)
FRAMES = 16

HEAT_COLOURS = [
    (3.2, (255, 244, 186, 255)),  # 따뜻한 연노랑 (가운데, 작게)
    (1.9, (255, 210, 78, 255)),   # 노랑
    (1.0, (255, 148, 40, 255)),   # 주황
    (0.55, (238, 82, 30, 255)),   # 다홍
    (0.26, (190, 38, 36, 235)),   # 진홍 (가장자리)
]

# 크기 4단계 (게임 config.BURN_FLAME_SIZES 와 같게): 이름 → 기준 대비 배율
SIZES = {'s': 0.45, 'm': 0.65, 'l': 0.9, 'xl': 1.2}

# 모양 3종: 이름 → (덩어리 수, 바닥 퍼짐, 오르는 높이, 반지름, 씨앗) — 기준 크기 1.0 일 때
VARIANTS = {
    'tall': (170, 2.0, (24, 36), (2.3, 3.6), 11),   # 가늘고 높게 솟는 혀
    'wide': (160, 3.6, (16, 28), (2.6, 4.0), 23),   # 넓은 바닥에서 여러 갈래로
    'lick': (110, 1.6, (12, 22), (1.8, 3.0), 37),   # 작게 날름거리는 불
}


def canvas(k):
    w = max(8, 2 * math.ceil(BASE_W * k / 2))
    h = max(12, math.ceil(BASE_H * k))
    return w, h


def make_particles(k, count, spread, rise, radius, seed):
    w, h = canvas(k)
    base_y = h - max(2, round(4 * k))
    rnd = random.Random(seed)
    out = []
    for _ in range(count):
        x0 = w / 2 + rnd.gauss(0, spread * k)
        out.append({
            'x0': x0, 'y0': base_y + rnd.uniform(-1, 2) * k,
            'rise': rnd.uniform(*rise) * k,  # 일생 동안 오르는 높이
            'drift': (w / 2 - x0) * rnd.uniform(0.5, 0.9),  # 위로 가며 가운데로 모임 (혀 모양)
            'r0': max(1.1, rnd.uniform(*radius) * k),
            'life': rnd.uniform(0.25, 0.45),
            'born': rnd.random(),
            'wig': rnd.uniform(1.0, 2.6) * k, 'ph': rnd.uniform(0, 6.28), 'freq': rnd.uniform(6, 11),
        })
    return out


def draw_frame(i, parts, k):
    w, h = canvas(k)
    t = i / FRAMES
    heat = [[0.0] * w for _ in range(h)]
    for p in parts:
        age = ((t - p['born']) % 1.0) / p['life']
        if age >= 1.0:
            continue
        cy = p['y0'] - p['rise'] * age ** 1.15
        cx = p['x0'] + p['drift'] * age + p['wig'] * math.sin(p['ph'] + age * p['freq']) * age
        r = p['r0'] * (1 - 0.8 * age)
        strength = 1.15 * (1 - age) ** 0.9
        for y in range(max(0, int(cy - r * 2.2 - 1)), min(h, int(cy + r + 2))):
            for x in range(max(0, int(cx - r - 1)), min(w, int(cx + r + 2))):
                dy = y + 0.5 - cy
                dy = dy / 2.2 if dy < 0 else dy  # 위로 길쭉 (혀)
                d = math.hypot(x + 0.5 - cx, dy)
                if d < r:
                    heat[y][x] += (1 - d / r) * strength
    level = [[-1] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            for n, (limit, _) in enumerate(HEAT_COLOURS):
                if heat[y][x] >= limit:
                    level[y][x] = n
                    break
    # 외곽 정리: 이웃(상하좌우)이 둘 미만인 외톨이 점은 지운다 (가장자리를 강제로 식히면 테두리 선처럼 보여 하지 않음)
    for _ in range(2):
        for y in range(h):
            for x in range(w):
                if level[y][x] < 0:
                    continue
                around = [level[y + dy][x + dx] if 0 <= x + dx < w and 0 <= y + dy < h else -1
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if sum(a >= 0 for a in around) < 2:
                    level[y][x] = -1
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if level[y][x] >= 0:
                px[x, y] = HEAT_COLOURS[level[y][x]][1]
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (count, spread, rise, radius, seed) in VARIANTS.items():
        for size, k in SIZES.items():
            w, h = canvas(k)
            parts = make_particles(k, count, spread, rise, radius, seed)
            strip = Image.new('RGBA', (w * FRAMES, h), (0, 0, 0, 0))
            for i in range(FRAMES):
                strip.alpha_composite(draw_frame(i, parts, k), (i * w, 0))
            strip.save(os.path.join(OUT, f'flame_{name}_{size}.png'))
            print(name, size, (w, h))


if __name__ == '__main__':
    main()
