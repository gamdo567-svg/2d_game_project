"""검 불 이펙트 — 오러 느낌 (2026-11-20 사용자: 직접 그린 불을 "오러 느낌으로").

불꽃 혀를 따로 그리지 않고, 칼날 둘레를 감싸는 반투명한 빛 덩어리(오러)로 그린다.
- 칼날 윤곽에서 바깥으로 거리를 재어, 안쪽(칼날에 붙은 곳)은 진하고 밝게, 바깥으로 갈수록 옅고 붉게 (반투명 단계).
- 오러 두께가 칼끝 쪽으로 흐르는 물결처럼 출렁이고, 전체가 숨 쉬듯 부풀었다 줄어든다.
- 칼끝에서는 오러가 칼 방향으로 길게 뻗어 사라진다.
- 오러 안에서 밝은 결(흐르는 줄기)이 칼끝 쪽으로 지나가고, 작은 빛 알갱이가 떠올라 사라진다.
칼 그림 방향 그대로(칼끝 오른쪽, 손이 (40, 12)) 80×24 프레임 FRAMES 장. 반복이 끊기지 않게 출렁임은 주기 맞춘 사인.
출력: assets/images/effects/sword_enchant/fire.png
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
SWORD_AT = (12, 7)  # 칼 그림(56×10)을 프레임에 놓는 자리 (칼 한가운데 = 손 = (40, 12))
BLADE_FROM_X = 44  # 이 x 부터를 칼날로 본다 (가드 포함 안 함)
MID_Y = 11

# 오러 단계 (안쪽 → 바깥): 색과 불투명도
LAYERS = [
    (255, 244, 190, 240),  # 칼날에 붙은 흰빛 테
    (255, 196, 70, 215),   # 노랑
    (255, 138, 34, 200),   # 주황
    (246, 88, 30, 165),    # 빨강
    (210, 52, 28, 115),    # 가장 바깥 붉은 기운 (어두운 바닥에서도 보이게 밝게)
]
STREAK = (255, 236, 160, 210)  # 오러 속을 흐르는 밝은 결
MOTE = [(255, 240, 180, 230), (255, 180, 70, 200), (230, 90, 40, 150)]


def blade_pixels():
    sword = Image.open(SWORD).convert('RGBA')
    px = sword.load()
    pts = set()
    for y in range(sword.height):
        for x in range(sword.width):
            if px[x, y][3] and x + SWORD_AT[0] >= BLADE_FROM_X:
                pts.add((x + SWORD_AT[0], y + SWORD_AT[1]))
    return pts


def distance_map(pts):
    """각 픽셀에서 칼날까지의 거리 (칼날 위는 0)."""
    dist = {}
    for y in range(H):
        for x in range(W):
            dist[(x, y)] = min(math.hypot(x - px, y - py) for px, py in pts)
    return dist


def wave(x, t, terms):
    v = sum(a * math.sin(2 * math.pi * (kx * x / 40.0 - kt * t) + ph) for kx, kt, a, ph in terms)
    return v / sum(a for _, _, a, _ in terms)  # -1 ~ 1


TOP = [(2, 2, 1.0, 0.0), (5, 3, 0.5, 1.3), (9, 5, 0.25, 2.9)]
BOTTOM = [(2, 2, 1.0, 1.9), (4, 3, 0.55, 0.2), (8, 4, 0.3, 4.0)]


def draw_frame(i, blade, dist, motes):
    t = i / FRAMES
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    tip = max(x for x, _ in blade)
    breathe = 0.85 + 0.15 * math.sin(2 * math.pi * 2 * t)  # 숨 쉬듯
    for y in range(H):
        for x in range(W):
            if (x, y) in blade:
                continue
            d = dist[(x, y)]
            # 이 픽셀이 붙은 칼날 자리 (칼끝 너머는 칼끝)
            bx = min(x, tip)
            u = max(0.0, (bx - BLADE_FROM_X) / (tip - BLADE_FROM_X))  # 0 = 가드 쪽, 1 = 칼끝
            terms = TOP if y < MID_Y else BOTTOM
            # 두께: 가드 쪽은 얇고 칼끝 쪽이 두꺼움, 칼끝 쪽으로 흐르는 물결
            thick = (3.4 + 3.0 * u) * breathe * (1 + 0.35 * wave(x - 0.8 * abs(y - MID_Y), t, terms))
            if x > tip:  # 칼끝 너머: 칼 방향으로 길게 뻗음
                along = x - tip
                reach = (9 + 3 * wave(0, t, [(0, 3, 1.0, 0.0), (0, 5, 0.4, 1.0)])) * breathe
                if along > reach:
                    continue
                thick = (thick * (1 - along / reach) ** 0.6) + 0.4
                d = abs(y - MID_Y)
            if x < BLADE_FROM_X - 1:
                continue  # 가드·손잡이 쪽에는 오러 없음
            thick *= min(1.0, (x - BLADE_FROM_X + 2) / 6)  # 가드 바로 앞에서 얇게 시작 (가드에 가로줄이 생기지 않게)
            if d > thick:
                continue
            k = min(len(LAYERS) - 1, int(d / thick * len(LAYERS)))
            px[x, y] = LAYERS[k]
    # 오러 속을 흐르는 밝은 결 (위·아래에 하나씩, 칼끝 쪽으로 흘러감)
    for side, ph in ((-1, 0.0), (1, 0.5)):
        for s in range(2):
            u = (t * 2 + ph + s * 0.5) % 1.0
            x0 = BLADE_FROM_X + 2 + u * (tip - BLADE_FROM_X)
            for k in range(4):
                x = round(x0 - k)
                y = MID_Y + side * (3 + (1 if k > 1 else 0))
                if 0 <= x < W and 0 <= y < H and px[x, y][3] and (x, y) not in blade:
                    px[x, y] = STREAK
    # 빛 알갱이: 오러 바깥으로 떠올라 사라짐
    for mx, my, vx, vy, t0 in motes:
        age = (t - t0) % 1.0
        if age > 0.45:
            continue
        k = age / 0.45
        x, y = round(mx + vx * k), round(my + vy * k)
        if 0 <= x < W and 0 <= y < H and (x, y) not in blade:
            px[x, y] = MOTE[min(2, int(k * 3))]
    return im


def make_motes(tip):
    rnd = random.Random(11)
    out = []
    for _ in range(12):
        side = rnd.choice((-1, 1))
        out.append((rnd.uniform(BLADE_FROM_X + 4, tip), MID_Y + side * rnd.uniform(3, 5),
                    rnd.uniform(4, 9), side * rnd.uniform(1.5, 4), rnd.random()))
    return out


def main():
    blade = blade_pixels()
    dist = distance_map(blade)
    motes = make_motes(max(x for x, _ in blade))
    strip = Image.new('RGBA', (W * FRAMES, H), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.alpha_composite(draw_frame(i, blade, dist, motes), (i * W, 0))
    os.makedirs(OUT, exist_ok=True)
    strip.save(os.path.join(OUT, 'fire.png'))
    print('fire aura', FRAMES)


if __name__ == '__main__':
    main()
