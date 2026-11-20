"""검 전기 이펙트 (2026-11-20 사용자: 전기 한번 해줘봐). 불(build_fire_flame.py)과 같은 형식의 시트를 직접 그린다.

- 칼날 가장자리를 따라 지그재그 번개 줄기가 칼끝 쪽으로 기어가고(1~4 픽셀 떨어져), 짧은 번개가 바깥으로 튀며 갈라진다.
- 줄기는 흰 심 + 하늘색 + 파란 테두리, 둘레에 옅은 파란 빛. 튀는 불꽃(점) 몇 개. 칼날 둘레에 옅은 푸른 빛이 늘 깔림.
- 전기는 빨리 바뀌어야 해 줄기마다 2장씩만 유지하고 새로 그린다 (24장 한 바퀴, 장마다 정해진 씨앗이라 늘 같은 그림).
출력 (assets/images/effects/sword_enchant/):
- lightning.png: 칼 그림 방향(칼끝 오른쪽, 손 (40, 12)) 80×24 × 24장 반복
- lightning_ignite.png: E 로 입힐 때 12장. 손잡이에서 전기가 튀기 시작해 칼끝까지 번짐 (앞머리에 큰 방전)
- lightning_front_3_f5.png / f6.png: 정면 3타 찌르기용 칼 그림 (공격 칸 96×64 × 24장), 칼날 윤곽을 따라
"""
import math
import os
import random

from PIL import Image

import build_fire_flame as ff

OUT = ff.OUT
FRAMES = ff.FRAMES
IGNITE_FRAMES = ff.IGNITE_FRAMES
CORE = (245, 252, 255, 255)
BRIGHT = (150, 222, 255, 255)
EDGE = (64, 140, 255, 235)
HALO = (50, 110, 245, 160)
BLADE_GLOW = [(120, 190, 255, 150), (70, 120, 245, 90)]


def dist_map(blade, w, h):
    return {(x, y): min(math.hypot(x - bx, y - by) for bx, by in blade) for y in range(h) for x in range(w)}


def crawl(rnd, start, axis, dist, lo, hi, length):
    """칼날에서 lo~hi 떨어진 띠 안을 축 방향(axis = (ax, ay))으로 지그재그로 기어가는 줄기 (픽셀 목록)."""
    pts = [start]
    x, y = start
    ax, ay = axis
    nx, ny = -ay, ax  # 축에 수직
    side_step = 0
    for _ in range(length):
        if side_step == 0 or rnd.random() < 0.45:
            side_step = rnd.choice((-1, 0, 1))
        cand = (x + ax + nx * side_step, y + ay + ny * side_step)
        if cand not in dist or not (lo <= dist[cand] <= hi):
            cand = (x + ax, y + ay)
            if cand not in dist or not (lo - 0.5 <= dist[cand] <= hi + 0.5):
                break
        x, y = cand
        pts.append((x, y))
    return pts


def jump(rnd, start, dist, length):
    """칼날에서 바깥으로 튀는 짧은 번개 (거리가 늘어나는 쪽으로), 가끔 갈래."""
    pts = [start]
    branches = []
    x, y = start
    for k in range(length):
        nbrs = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and (x + dx, y + dy) in dist]
        out = [p for p in nbrs if dist[p] > dist[(x, y)]]
        if not out:
            break
        x, y = rnd.choice(out)
        pts.append((x, y))
        if k == 1 and rnd.random() < 0.5:
            branches.append(jump(rnd, (x, y), dist, max(1, length - 3))[0])
    return pts, branches


def paint(im, blade, lines, sparks, glow_limit=None):
    """줄기들을 그린다: 먼저 둘레 빛, 그다음 테두리·밝은 색, 마지막 흰 심. 칼날 픽셀은 가리지 않음."""
    px = im.load()
    w, h = im.size

    def put(p, c, only_if_weaker=True):
        if 0 <= p[0] < w and 0 <= p[1] < h and p not in blade:
            if not only_if_weaker or px[p][3] < c[3]:
                px[p] = c

    for bx, by in blade:  # 칼날 둘레 옅은 빛
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0), (0, -2), (0, 2)):
            p = (bx + dx, by + dy)
            if glow_limit is None or glow_limit(p):
                put(p, BLADE_GLOW[0] if abs(dx) + abs(dy) == 1 else BLADE_GLOW[1])
    for line in lines:
        for x, y in line:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    put((x + dx, y + dy), HALO)
    for line in lines:
        for i, p in enumerate(line):
            put(p, BRIGHT if 0 < i < len(line) - 1 else EDGE, only_if_weaker=False)
    for line in lines:  # 흰 심: 줄기 가운데 부분
        for p in line[1:-2]:
            put(p, CORE, only_if_weaker=False)
    for p in sparks:
        put(p, CORE if (p[0] + p[1]) % 2 else BRIGHT, only_if_weaker=False)


def edge_points(blade, dist, d):
    return [p for p, v in dist.items() if d - 0.5 <= v <= d + 0.5]


def bolts(seed, blade, dist, axis, along_key, front=None, flare_at=None, start=-1e9):
    """한 장의 번개들: 기어가는 줄기 3~4개, 튀는 번개 2~3개, 불꽃 점. front 가 있으면 그 앞(축 방향)은 아직 없음."""
    rnd = random.Random(seed)
    near = [p for p in edge_points(blade, dist, 1.5) if along_key(p) >= start + 1 and (front is None or along_key(p) <= front)]
    lines, sparks = [], []
    if not near:
        return lines, sparks
    for _ in range(rnd.randint(4, 6)):
        line = crawl(rnd, rnd.choice(near), axis, dist, 1, 3.5, rnd.randint(6, 14))
        line = [p for p in line if along_key(p) >= start]  # 가드 아래(손잡이)로는 가지 않음
        if front is not None:
            line = [p for p in line if along_key(p) <= front + 2]
        if len(line) > 2:
            lines.append(line)
    for _ in range(rnd.randint(3, 4)):
        main, branches = jump(rnd, rnd.choice(near), dist, rnd.randint(3, 7))
        lines.append(main)
        lines.extend(b for b in branches if len(b) > 1)
    if flare_at is not None:  # 번지는 앞머리의 큰 방전
        heads = [p for p in near if abs(along_key(p) - flare_at) <= 2] or near[-3:]
        for _ in range(3):
            main, branches = jump(rnd, rnd.choice(heads), dist, rnd.randint(5, 8))
            lines.append(main)
            lines.extend(branches)
    for line in lines:
        if rnd.random() < 0.6:
            ex, ey = line[-1]
            sparks.append((ex + rnd.choice((-2, -1, 1, 2)), ey + rnd.choice((-2, -1, 1, 2))))
    return lines, sparks


def sword_sheets():
    blade = ff.blade_pixels()
    dist = dist_map(blade, ff.W, ff.H)
    tip = max(x for x, _ in blade)

    def along(p):
        return p[0]

    def frame(i, front=None, flare=None, salt=0):
        im = Image.new('RGBA', (ff.W, ff.H), (0, 0, 0, 0))
        # 2장마다 새 번개 (너무 빨리 바뀌면 깜빡임처럼 보임)
        lines, sparks = bolts(10_000 * salt + i // 2, blade, dist, (1, 0), along, front, flare, start=ff.BLADE_FROM_X)
        limit = None if front is None else (lambda p: p[0] <= front)
        paint(im, blade, lines, sparks, limit)
        return im

    strip = Image.new('RGBA', (ff.W * FRAMES, ff.H), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.alpha_composite(frame(i), (i * ff.W, 0))
    strip.save(os.path.join(OUT, 'lightning.png'))
    ignite = Image.new('RGBA', (ff.W * IGNITE_FRAMES, ff.H), (0, 0, 0, 0))
    for k in range(IGNITE_FRAMES):
        front = ff.BLADE_FROM_X + 1 + (tip + 3 - (ff.BLADE_FROM_X + 1)) * (k + 1) / IGNITE_FRAMES
        ignite.alpha_composite(frame(2 * k, front, front, salt=1), (k * ff.W, 0))
    ignite.save(os.path.join(OUT, 'lightning_ignite.png'))


def art_sheets():
    for k in ff.ART_BLADE_TOP:
        blade = ff.art_blade(k)
        dist = dist_map(blade, 96, 64)
        strip = Image.new('RGBA', (96 * FRAMES, 64), (0, 0, 0, 0))
        for i in range(FRAMES):
            im = Image.new('RGBA', (96, 64), (0, 0, 0, 0))
            # 칼이 보는 사람 쪽(화면 아래)으로 뻗어 줄기는 칼끝 쪽(아래)으로 기어감
            lines, sparks = bolts(20_000 + k * 100 + i // 2, blade, dist, (0, 1), lambda p: p[1], start=ff.ART_BLADE_TOP[k])
            paint(im, blade, lines, sparks)
            strip.alpha_composite(im, (i * 96, 0))
        strip.save(os.path.join(OUT, f'lightning_front_3_f{k}.png'))


if __name__ == '__main__':
    sword_sheets()
    art_sheets()
    print('lightning', FRAMES, 'ignite', IGNITE_FRAMES, 'art', list(ff.ART_BLADE_TOP))
