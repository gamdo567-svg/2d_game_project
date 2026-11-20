"""검 불 이펙트를 직접 그리기 (2026-11-20 사용자: PixelLab VFX 불이 마음에 안 듦 → 직접 만들어 달라).

칼 그림 방향 그대로(칼끝이 오른쪽, 손이 프레임 한가운데 (40, 12)) 80×24 프레임 FRAMES 장을 계산해 그린다.
- 칼날(가드 바로 앞 x 45 ~ 칼끝 x 64, 가운데 줄 y 11) 위·아래 가장자리에서 불꽃 혀가 바깥으로 솟고,
  칼끝 쪽으로 기울어 흐른다 (칼을 세우면 위로 타오름). 혀마다 높이가 출렁이며 칼끝 쪽으로 흘러간다.
- 칼끝에서는 불길이 칼 방향으로 길게 솟는다.
- 불티(알갱이)가 불꽃에서 떨어져 칼끝 쪽·바깥으로 날아가며 식는다.
- 색: 칼날에 붙은 곳은 하얗게 뜨겁고, 바깥으로 갈수록 노랑 → 주황 → 빨강 → 검붉은 끝.
반복이 끊기지 않도록 모든 출렁임은 FRAMES 장 주기의 사인 합으로 만든다.
출력: assets/images/effects/sword_enchant/fire.png (build_effect.py 와 같은 형식)
"""
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'images', 'effects', 'sword_enchant')
W, H = 80, 24
FRAMES = 24
BLADE_X = (45, 64)  # 가드 바로 앞 ~ 칼끝
TOP_EDGE, BOTTOM_EDGE = 9, 13  # 칼날 위·아래 가장자리 줄 (이 줄 바깥이 불꽃 자리)
MID_Y = 11
# 뜨거운 곳 → 식은 곳
PALETTE = [
    (255, 250, 220, 255),  # 흰빛 (칼날에 붙은 곳)
    (255, 222, 110, 255),  # 노랑
    (255, 160, 50, 255),   # 주황
    (232, 88, 34, 255),    # 빨강
    (150, 38, 30, 235),    # 검붉음 (끝)
]


def wave(x, t, terms):
    """주기가 맞는 사인 합 (t 는 0~1 한 바퀴). 반환 0~1."""
    v = 0.0
    total = 0.0
    for kx, kt, amp, phase in terms:
        v += amp * math.sin(2 * math.pi * (kx * x / 40.0 - kt * t) + phase)
        total += amp
    return 0.5 + 0.5 * v / total


# 혀 높이 출렁임 (위·아래 가장자리 따로): 칼끝 쪽(+x)으로 흘러감 = x 와 t 가 같은 부호
TOP_TERMS = [(3, 2, 1.0, 0.3), (5, 3, 0.6, 1.7), (9, 4, 0.35, 4.1)]
BOTTOM_TERMS = [(3, 2, 1.0, 2.2), (6, 3, 0.55, 0.4), (10, 5, 0.3, 3.3)]
TIP_TERMS = [(1, 3, 1.0, 0.0), (2, 5, 0.5, 1.1)]


def tongue_height(x, t, terms):
    """가장자리에서 바깥으로 솟는 불꽃 높이 (픽셀). 손잡이 쪽은 낮고 칼 가운데·끝 쪽이 높다."""
    a, b = BLADE_X
    u = (x - a) / (b - a)  # 0 = 가드, 1 = 칼끝
    base = 1.2 + 2.6 * min(1.0, u * 1.6)
    n = wave(x, t, terms)
    tongues = max(0.0, math.sin(2 * math.pi * (x / 4.0 - 2 * t)))  # 혀 사이 골
    return base * (0.45 + 0.75 * n) * (0.65 + 0.35 * tongues)


def colour_for(r):
    """r = 바깥으로 간 정도 / 혀 높이 (0 = 칼날, 1 = 혀 끝)."""
    if r < 0.18:
        return PALETTE[0]
    if r < 0.42:
        return PALETTE[1]
    if r < 0.66:
        return PALETTE[2]
    if r < 0.88:
        return PALETTE[3]
    return PALETTE[4]


TONGUES = 7  # 한쪽 가장자리의 불꽃 혀 수 (손잡이에서 칼끝으로 흘러감)


def tongue_list(t):
    """이번 장의 불꽃 혀들: (가장자리 x, 바깥 방향 -1 위 / +1 아래, 높이, 밑동 너비, 휘는 정도)."""
    a, b = BLADE_X
    out = []
    for side, offset in ((-1, 0.0), (1, 0.5 / TONGUES)):
        for k in range(TONGUES):
            u = (k / TONGUES + offset + t) % 1.0  # 칼날 위 자리 (0 = 가드, 1 = 칼끝), 한 바퀴에 한 칸씩 흘러감
            grow = math.sin(math.pi * u) ** 0.5  # 가드에서 피어나 가운데에서 크고 칼끝에서 잦아듦
            flick = 0.75 + 0.25 * math.sin(2 * math.pi * (3 * t + k * 0.37 + side * 0.2))
            h = (2.0 + 4.2 * min(1.0, 0.35 + u)) * grow * flick
            out.append((a + u * (b - a), side, h, 1.6 + 1.2 * grow,
                        0.9 * math.sin(2 * math.pi * (2 * t + k * 0.51))))
    return out


def draw_frame(i, embers):
    t = i / FRAMES
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = im.load()
    a, b = BLADE_X
    heat = {}  # 픽셀 → 가장 뜨거운 값 (0 = 가장 뜨거움, 1 = 끝)
    lean = 0.75  # 바깥으로 1 픽셀 갈 때 칼끝 쪽으로 기우는 양
    # 칼날 가장자리에 붙은 얇은 불 띠 (칼을 감싸는 느낌)
    for x in range(a, b + 1):
        for side, edge in ((-1, TOP_EDGE - 1), (1, BOTTOM_EDGE + 1)):
            n = wave(x, t, TOP_TERMS if side < 0 else BOTTOM_TERMS)
            heat[(x, edge)] = min(heat.get((x, edge), 9), 0.15 + 0.3 * n)
    for x0, side, h, w0, curl in tongue_list(t):
        if h < 0.8:
            continue
        edge = TOP_EDGE if side < 0 else BOTTOM_EDGE
        for d in range(1, int(h) + 2):
            f = d / (h + 0.5)
            if f > 1:
                break
            cx = x0 + lean * d + curl * f * f  # 끝으로 갈수록 휘어짐
            half = w0 * (1 - f) ** 0.75 + 0.25
            y = edge + side * d
            for x in range(int(cx - half - 1), int(cx + half + 2)):
                q = abs(x + 0.5 - cx) / (half + 0.5)
                if q > 1:
                    continue
                r = max(f, q * 0.85)
                key = (x, y)
                heat[key] = min(heat.get(key, 9), r)
    # 칼끝 불길: 칼 방향으로 솟는 혀 2개
    for k, (length, width, ph) in enumerate(((12.0, 2.6, 0.0), (8.0, 1.8, 0.5))):
        L = length * (0.8 + 0.2 * wave(0, t + ph, TIP_TERMS))
        sway = math.sin(2 * math.pi * (2 * t + ph))
        for x in range(b - 3, b + int(L) + 1):
            f = (x - (b - 3)) / L
            if f > 1:
                break
            cy = MID_Y + (sway * 1.4 * f * f) + (k - 0.5) * 1.2 * f
            half = width * (1 - f) ** 0.7 + 0.2
            for y in range(int(cy - half - 1), int(cy + half + 2)):
                q = abs(y + 0.5 - cy) / (half + 0.5)
                if q <= 1:
                    key = (x, y)
                    heat[key] = min(heat.get(key, 9), max(f, q * 0.8))
    for (x, y), r in heat.items():
        if not (0 <= x < W and 0 <= y < H):
            continue
        if TOP_EDGE <= y <= BOTTOM_EDGE and x < b - 1:
            continue  # 칼날은 가리지 않음
        px[x, y] = colour_for(r)
    # 불티
    for ex, ey, vx, vy, t0 in embers:
        age = (t - t0) % 1.0
        if age > 0.35:
            continue
        k = age / 0.35
        x = round(ex + vx * k)
        y = round(ey + vy * k)
        if 0 <= x < W and 0 <= y < H and not (TOP_EDGE <= y <= BOTTOM_EDGE and x <= b):
            px[x, y] = PALETTE[1] if k < 0.35 else PALETTE[2] if k < 0.7 else PALETTE[3]
    return im


def make_embers():
    rnd = random.Random(7)
    embers = []
    a, b = BLADE_X
    for _ in range(14):
        side = rnd.choice((-1, 1))
        ex = rnd.uniform(a + 4, b)
        ey = (TOP_EDGE - 2) if side < 0 else (BOTTOM_EDGE + 2)
        embers.append((ex, ey, rnd.uniform(5, 11), side * rnd.uniform(2, 5), rnd.random()))
    return embers


def main():
    embers = make_embers()
    strip = Image.new('RGBA', (W * FRAMES, H), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.alpha_composite(draw_frame(i, embers), (i * W, 0))
    os.makedirs(OUT, exist_ok=True)
    strip.save(os.path.join(OUT, 'fire.png'))
    print('fire', FRAMES)


if __name__ == '__main__':
    main()
