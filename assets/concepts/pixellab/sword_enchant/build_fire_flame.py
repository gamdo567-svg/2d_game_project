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
IGNITE_FRAMES = 12  # 점화 장 수 (game/config.py SWORD_EFFECT_IGNITE_FRAMES 와 같게)

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


def flare_blobs(front, k):
    """불이 번지는 앞머리의 큰 불덩이들 (점화 장 k 마다 조금씩 다르게)."""
    rnd = random.Random(1000 + k)
    out = []
    for _ in range(7):
        side = rnd.choice((-1, 0, 1))
        cx = front - rnd.uniform(-1.5, 3.5)
        cy = MID_Y + side * rnd.uniform(2.5, 4.5) + rnd.uniform(-0.8, 0.8)
        out.append((cx + rnd.uniform(0, 3), cy, rnd.uniform(2.0, 3.2), rnd.uniform(0.9, 1.3)))
    return out


def draw_frame(i, blade, parts, front=None, k=0):
    """front 가 있으면 점화 장: 그 x 까지만 불이 붙어 있고, 앞머리에서 큰 불덩이가 화르륵 일어난다."""
    t = i / FRAMES
    heat = [[0.0] * W for _ in range(H)]
    if front is not None:
        for cx, cy, r, strength in flare_blobs(front, k):
            for y in range(max(0, int(cy - r - 1)), min(H, int(cy + r + 2))):
                for x in range(max(0, int(cx - r - 1)), min(W, int(cx + r + 2))):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d < r:
                        heat[y][x] += (1 - d / r) * strength
    for p in parts:
        boost = 1.0
        if front is not None:
            if p['x0'] > front:
                continue  # 아직 불이 닿지 않은 자리
            boost = 1.0 + 0.5 * max(0.0, 1 - (front - p['x0']) / 8)  # 막 불이 붙은 곳은 더 세게
        age = ((t - p['born']) % 1.0) / p['life']
        if age >= 1.0:
            continue
        # 날아가며 칼끝 쪽으로 가속, 바깥으로 퍼짐, 좌우로 흔들림
        cx = p['x0'] + p['vx'] * age ** 1.2
        cy = p['y0'] + p['vy'] * age + p['wig'] * math.sin(p['ph'] + age * 9) * age
        r = p['r0'] * (1 - 0.75 * age)
        strength = 1.25 * (1 - age) ** 0.7 * boost
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
                if 0 <= x < W and 0 <= y < H and (x, y) not in blade and x >= BLADE_FROM_X                         and (front is None or x <= front):
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
    # 점화 (E 로 입힐 때): 손잡이에서 불이 붙어 칼끝까지 타오르며 번짐. 앞머리 뒤로 날린 불꽃이 앞질러 핥는다.
    tip = max(x for x, _ in blade)
    ignite = Image.new('RGBA', (W * IGNITE_FRAMES, H), (0, 0, 0, 0))
    for k in range(IGNITE_FRAMES):
        front = BLADE_FROM_X + 1 + (tip + 4 - (BLADE_FROM_X + 1)) * (k + 1) / IGNITE_FRAMES
        # 막 불이 붙은 아랫부분이 비어 보이지 않게 덩어리를 한 벌 더 (태어나는 때를 옮긴 것)
        dense = parts + [dict(p, born=(p['born'] + 0.37) % 1.0) for p in parts[::2]]
        ignite.alpha_composite(draw_frame(k, blade, dense, front=front, k=k), (k * W, 0))
    ignite.save(os.path.join(OUT, 'fire_ignite.png'))
    print('fire flame', FRAMES, 'ignite', IGNITE_FRAMES)


if __name__ == '__main__':
    main()


# ----- 찌르기용 칼 그림의 불 (2026-11-20 사용자: 정면 찌르기 때 이펙트가 안 입혀짐) -----
# 정면 3타 찌르는 순간은 보는 사람 쪽으로 내민 큰 칼 그림(weapons/old_sword_front_3.png, 96×64 공격 칸)을 쓴다.
# 옆모습 칼용 불을 늘려 붙이면 뭉툭하고 테두리가 U 자로 보여, 그 그림의 칼날 윤곽에서 직접 불덩이를 피워 올린다
# (칼이 보는 사람 쪽이라 불은 화면 위로 타오름). 출력: fire_front_3_f<장>.png (96×64 × FRAMES, 공격 칸과 같은 자리).
ART = os.path.join(ROOT, 'assets', 'images', 'player', 'weapons', 'old_sword_front_3.png')
ART_BLADE_TOP = {5: 36, 6: 33}  # 장 → 이 줄부터 아래가 칼날 (위는 손·손잡이·가드)


def art_blade(k):
    art = Image.open(ART).convert('RGBA')
    cell = art.crop((k * 96, 0, (k + 1) * 96, 64))
    px = cell.load()
    return {(x, y) for y in range(ART_BLADE_TOP[k], 64) for x in range(96) if px[x, y][3] > 100}


def art_particles(blade):
    rnd = random.Random(SEED + 1)
    edge = sorted({(x + dx, y + dy) for x, y in blade for dx, dy in ((1, 0), (-1, 0), (0, 1))
                   if (x + dx, y + dy) not in blade})
    cx = sum(x for x, _ in blade) / len(blade)
    out = []
    for _ in range(max(60, len(edge) * 3)):
        ex, ey = rnd.choice(edge)
        side = 1 if ex >= cx else -1
        out.append({
            'x0': ex + 0.5, 'y0': ey + 0.5, 'vx': side * rnd.uniform(1.0, 3.5), 'vy': -rnd.uniform(5, 11),
            'r0': rnd.uniform(2.4, 3.8), 'life': rnd.uniform(0.18, 0.3), 'born': rnd.random(),
            'wig': rnd.uniform(0.4, 1.2), 'ph': rnd.uniform(0, 6.28),
        })
    return out


def draw_art_frame(i, blade, parts):
    t = i / FRAMES
    w, h = 96, 64
    heat = [[0.0] * w for _ in range(h)]
    for p in parts:
        age = ((t - p['born']) % 1.0) / p['life']
        if age >= 1.0:
            continue
        cx = p['x0'] + p['vx'] * age + p['wig'] * math.sin(p['ph'] + age * 9) * age
        cy = p['y0'] + p['vy'] * age ** 1.1
        r = p['r0'] * (1 - 0.7 * age)
        strength = 1.25 * (1 - age) ** 0.7
        for y in range(max(0, int(cy - r - 1)), min(h, int(cy + r + 2))):
            for x in range(max(0, int(cx - r - 1)), min(w, int(cx + r + 2))):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d < r:
                    heat[y][x] += (1 - d / r) * strength
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for x, y in blade:  # 칼날 둘레 옅은 빛
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (2, 0), (-2, 0)):
            q = (x + dx, y + dy)
            if q not in blade and 0 <= q[0] < w and 0 <= q[1] < h:
                c = GLOW[0] if abs(dx) + abs(dy) == 1 else GLOW[1]
                if px[q][3] < c[3]:
                    px[q] = c
    for y in range(h):
        for x in range(w):
            if (x, y) in blade:
                continue
            for limit, colour in HEAT_COLOURS:
                if heat[y][x] >= limit:
                    px[x, y] = colour
                    break
    return im


def build_art():
    for k in ART_BLADE_TOP:
        blade = art_blade(k)
        parts = art_particles(blade)
        strip = Image.new('RGBA', (96 * FRAMES, 64), (0, 0, 0, 0))
        for i in range(FRAMES):
            strip.alpha_composite(draw_art_frame(i, blade, parts), (i * 96, 0))
        strip.save(os.path.join(OUT, f'fire_front_3_f{k}.png'))
    print('fire front_3', list(ART_BLADE_TOP))


if __name__ == '__main__':
    build_art()
