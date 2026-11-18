"""후면 공격 칼 자리 어림 (2026-11-18): 보이는 칼날 조각(파란, 가늘고 긴 덩어리)의 끝에서 칼 길이(24)만큼
몸 쪽으로 들어간 곳을 손으로, 칼날 방향을 각도로. 칼은 몸 뒤(가려짐). 결과를 OVERRIDES 에 옮겨 쓴다."""
import math
import sys

sys.path.insert(0, '.')
import build_remake_preview as b  # noqa: E402

BLADE = 24  # old_sword.png: 손(가운데)에서 칼끝까지


def estimate(frame):
    px = frame.load()
    blue = [(x, y) for y in range(b.CELL) for x in range(b.CELL) if b.is_blue(px[x, y])]
    body = [(x, y) for y in range(b.CELL) for x in range(b.CELL) if px[x, y][3] and not b.is_blue(px[x, y])]
    cx = sum(p[0] for p in body) / len(body)
    cy = sum(p[1] for p in body) / len(body)
    best = None
    for comp in sorted(b.components(blue), key=len, reverse=True):
        xs, ys = [p[0] for p in comp], [p[1] for p in comp]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs) / len(xs)
        syy = sum((y - my) ** 2 for y in ys) / len(ys)
        sxy = sum((x - mx) * (y - my) for x, y in comp) / len(xs)
        ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
        ux, uy = math.cos(ang), math.sin(ang)
        proj = [(x - mx) * ux + (y - my) * uy for x, y in comp]
        length = max(proj) - min(proj)
        width = len(comp) / max(1, length)
        if width > 3.5 and len(comp) > 15:
            continue  # 넓은 잔상
        a = (mx + ux * min(proj), my + uy * min(proj))
        c = (mx + ux * max(proj), my + uy * max(proj))
        tip, base = (a, c) if math.dist(a, (cx, cy)) > math.dist(c, (cx, cy)) else (c, a)
        dx, dy = tip[0] - base[0], tip[1] - base[1]
        n = math.hypot(dx, dy) or 1
        hand = (tip[0] - BLADE * dx / n, tip[1] - BLADE * dy / n)
        angle = math.degrees(math.atan2(-dy, dx))  # 위 90, 오른쪽 0
        best = (round(hand[0]), round(hand[1]), round(angle), True)
        break
    return best


for r in range(3):
    frames = b.cells('attack_back_gpt_68.png', r)
    print('hit', r + 1, [estimate(f) for f in frames[1:]])
