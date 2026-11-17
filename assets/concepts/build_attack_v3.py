"""ChatGPT 공격 참고 시트 v2(칼 = 파란 단색 #0000FF, 두 손 잡기) → 게임 공격 그림.

build_attack_from_reference.py 의 가공(배경 제거, 축소, 팔레트, Idle 머리)을 쓰고, 칼은 다음처럼 분리한다.
1. 칸마다 파란 픽셀로 칼의 직선(각도)과 가드(가장 넓은 곳) 위치를 잰다. 오른손(칼 그림의 손 위치) = 가드 바로 아래.
2. 파란 픽셀만 지운다 (팔·손은 칼 색이 아니므로 그대로 남는다). 칼이 몸을 가리던 구멍은 주변 색으로 메운다.
3. 오른손 레이어: 몸 그림에서 오른손 주먹 둘레만 잘라 따로 저장한다. 게임은 몸 → 칼 → 오른손 순서로 그린다.
4. 칼 위치표(손 위치·각도)를 출력한다 → game/config.py PLAYER_ATTACK_SWORD 에 넣는다.
5. 모든 프레임을 한꺼번에 가로로 옮겨 발 가운데 평균을 Idle 과 맞춘다 (제자리 공격).
Pillow 필요(게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/build_attack_v3.py <참고 시트 v2> <출력 폴더>`
     → side_1~3.png, side_1~3_hand.png, sword_table.txt, sheet_x3.png, combo_preview.gif
"""
import math
import os
import sys

os.environ.setdefault('ATTACK_SCALE_X', '0.88')
os.environ.setdefault('ATTACK_SCALE_Y', '0.95')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_attack_from_reference as ref  # noqa: E402  (sys.argv 의 시트·출력 폴더를 같이 씀)
import build_attack_v2 as v2  # noqa: E402  (잔상 그리기, 확인용 합성)
from PIL import Image  # noqa: E402

config = v2.config
W, H = ref.W, ref.H
SRC, OUT = ref.SRC, ref.OUT
IDLE_FEET_CENTER = 49.5  # Idle 측면 발 가운데 x (96 캔버스)
HAND_BEHIND_GUARD = 2.0  # 오른손 = 가드에서 손잡이 쪽으로 이만큼 (게임 픽셀). 칼 그림의 손-가드 거리와 같게
HAND_RADIUS = 2.6  # 오른손 레이어로 자를 반지름 (게임 픽셀)
GLOVE = (0x30, 0x1E, 0x25, 255)
OUTLINE = (0x12, 0x0C, 0x11, 255)
# 잔상: v2 와 같은 규칙 (타, 프레임) → (회전 방향, 꼬리 각도) 또는 'line'
SMEARS = v2.SMEARS


def is_blue(p):
    r, g, b = p[:3]
    return b > 150 and b > r + 60 and b > g + 60


def sword_geometry(im, box):
    """칸의 파란 칼: (오른손 위치, 칼끝 위치) 원본 좌표. 칼이 없으면 None."""
    x0, y0, x1, y1 = box
    px = im.load()
    blue = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if is_blue(px[x, y])}
    # 옆 칸의 칼끝이 상자 안으로 들어올 수 있어, 가장 큰 파란 덩어리만 이 칸의 칼로 본다
    best = set()
    while blue:
        seed = blue.pop()
        group, stack = {seed}, [seed]
        while stack:
            x, y = stack.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x + 1, y + 1), (x - 1, y - 1),
                      (x + 1, y - 1), (x - 1, y + 1)):
                if q in blue:
                    blue.discard(q)
                    group.add(q)
                    stack.append(q)
        if len(group) > len(best):
            best = group
    pts = [(x + 0.5, y + 0.5) for x, y in best]
    if len(pts) < 30:
        return None
    mx = sum(x for x, _ in pts) / len(pts)
    my = sum(y for _, y in pts) / len(pts)
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    syy = sum((y - my) ** 2 for _, y in pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    dx, dy = math.cos(ang), math.sin(ang)
    proj = [((x - mx) * dx + (y - my) * dy, (x - mx) * -dy + (y - my) * dx) for x, y in pts]
    lo = min(t for t, _ in proj)
    hi = max(t for t, _ in proj)
    # 축을 따라 폭(가로지르는 방향 범위)을 재서 가장 넓은 곳 = 가드
    bins = {}
    for t, s in proj:
        k = int((t - lo) // 2)
        a, b = bins.get(k, (s, s))
        bins[k] = (min(a, s), max(b, s))
    n = int((hi - lo) // 2) + 1
    widths = [(bins[k][1] - bins[k][0]) if k in bins else 0 for k in range(n)]
    guard_k = max(range(n), key=lambda k: widths[k])
    guard_t = lo + guard_k * 2 + 1
    # 칼끝 = 가드에서 먼 끝
    if hi - guard_t >= guard_t - lo:
        tip_t, sign = hi, 1
    else:
        tip_t, sign = lo, -1
    guard = (mx + guard_t * dx, my + guard_t * dy)
    tip = (mx + tip_t * dx, my + tip_t * dy)
    return guard, tip, sign


def fill_holes(img, hole):
    """칼이 지나가던 자리 중 몸 안쪽 구멍을 주변에 가장 많은 색으로 메운다."""
    p = img.load()
    for _ in range(4):
        fills = {}
        for (x, y) in hole:
            if p[x, y][3]:
                continue
            nb = [p[x + a, y + b] for a in (-1, 0, 1) for b in (-1, 0, 1)
                  if (a or b) and 0 <= x + a < W and 0 <= y + b < H and p[x + a, y + b][3]]
            if len(nb) >= 5:
                cols = [c[:3] for c in nb]
                fills[(x, y)] = max(set(cols), key=cols.count) + (255,)
        if not fills:
            break
        for q, c in fills.items():
            p[q] = c


def feet_center(img):
    p = img.load()
    boot = lambda x, y: p[x, y][3] and sum(p[x, y][:3]) < 400
    xs = [x for y in range(ref.FOOT_ROW - 2, ref.FOOT_ROW + 1) for x in range(W) if boot(x, y)]
    return (min(xs) + max(xs)) / 2


def shifted(img, dx):
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.alpha_composite(img, (dx, 0)) if dx >= 0 else out.paste(img, (dx, 0), img)
    return out


def hand_layer(body, hand):
    """몸 그림에서 오른손 주먹 둘레만 자른다."""
    hx, hy = hand
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    p, q = body.load(), out.load()
    for y in range(H):
        for x in range(W):
            if p[x, y][3] and math.hypot(x + 0.5 - hx, y + 0.5 - hy) <= HAND_RADIUS:
                q[x, y] = p[x, y]
    return out


def shifted_l(img, dx):
    out = Image.new('L', (W, H), 0)
    out.paste(img, (dx, 0))
    return out


SWORD_IMG = None


def sword_mask(entry):
    """게임에서 칼 그림이 덮는 칸 (손 위치·각도로 돌려 놓은 칼, 1픽셀 넓힘)."""
    global SWORD_IMG
    if SWORD_IMG is None:
        SWORD_IMG = v2.sword_image()
    hx, hy, deg, _ = entry
    rot = SWORD_IMG.rotate(deg, resample=Image.NEAREST, expand=True)
    big = Image.new('RGBA', (W + 2 * 60, H + 2 * 60), (0, 0, 0, 0))
    big.alpha_composite(rot, (round(60 + hx + 0.5 - rot.width / 2), round(60 + hy + 0.5 - rot.height / 2)))
    a = big.crop((60, 60, 60 + W, 60 + H)).getchannel('A').load()
    out = set()
    for y in range(H):
        for x in range(W):
            if a[x, y]:
                out.update((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    return out


def front_layer(body, blue, entry):
    """칼 앞에 있는 몸 픽셀: 게임 칼이 덮는 자리인데 원본에서 칼(파란색)이 아니었던 곳 = 칼을 쥔 손·팔.
    게임은 몸 → 칼 → 이 레이어 순서로 그려, 원본처럼 손과 팔이 칼 앞에 보이게 한다."""
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    p, q, b = body.load(), out.load(), blue.load()
    for x, y in sword_mask(entry):
        if 0 <= x < W and 0 <= y < H and p[x, y][3] and b[x, y] < 90:
            q[x, y] = p[x, y]
    return out


def near_hand(img, hand, r=2.6):
    p = img.load()
    return any(p[x, y][3] for y in range(H) for x in range(W) if math.hypot(x + 0.5 - hand[0], y + 0.5 - hand[1]) <= r)


def restore_arm(img, pre, hand, shoulder, width=2.6):
    """머리를 바꿔 붙이기 전 그림(pre)에서 손 → 어깨 띠의 픽셀을 다시 덮어씌운다."""
    p, s_ = img.load(), pre.load()
    (hx, hy), (sx_, sy_) = hand, shoulder
    lx, ly = sx_ - hx, sy_ - hy
    ln2 = lx * lx + ly * ly or 1
    for y in range(H):
        for x in range(W):
            if not s_[x, y][3]:
                continue
            k = max(0.0, min(1.0, ((x + 0.5 - hx) * lx + (y + 0.5 - hy) * ly) / ln2))
            if math.hypot(x + 0.5 - (hx + k * lx), y + 0.5 - (hy + k * ly)) <= width:
                p[x, y] = s_[x, y]


def glove(hand):
    """복귀 프레임(Idle 몸)용 주먹: 원본 그림에 손이 없으므로 2×2 장갑 + 외곽선."""
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    q = out.load()
    hx, hy = int(hand[0] - 0.5), int(hand[1] - 0.5)
    for a in range(-1, 3):
        for b in range(-1, 3):
            q[hx + a, hy + b] = GLOVE if 0 <= a <= 1 and 0 <= b <= 1 else OUTLINE
    for a, b in ((-1, -1), (2, -1), (-1, 2), (2, 2)):
        q[hx + a, hy + b] = (0, 0, 0, 0)
    return out


def main():
    im = Image.open(SRC).convert('RGB')
    rows = ref.find_cells(im)
    assert len(rows) == 3 and all(len(r) == 5 for r in rows), [len(r) for r in rows]
    base = sum(ref.IDLE_HEIGHT / (r[-1][3] - r[-1][1]) for r in rows) / len(rows)
    sx, sy = base * ref.SCALE_X, base * ref.SCALE_Y
    # 칼을 지운 원본 (파란 픽셀 → 초록 배경)
    clean = im.copy()
    cp, ip = clean.load(), im.load()
    for y in range(im.height):
        for x in range(im.width):
            if is_blue(ip[x, y]):
                cp[x, y] = (0, 255, 0)
    bodies, hands, blues = [], [], []
    for row in rows:
        rb, rh, rbl = [], [], []
        for box in row[:-1]:
            geo = sword_geometry(im, box)
            f = ref.shrink(clean, box, (sx, sy))
            fx, fb = ref.back_foot_x(f)
            ox, oy = ref.STAND_BACK_FOOT_X - fx, ref.FOOT_ROW - fb
            c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            c.paste(f, (ox, oy), f)
            # 게임 좌표에서 원본 칼(파란색)이 차지하던 비율 (0~255)
            cell = im.crop(box)
            mask = Image.new('L', cell.size, 0)
            mask.putdata([255 if is_blue(q) else 0 for q in cell.getdata()])
            bl = Image.new('L', (W, H), 0)
            bl.paste(mask.resize(f.size, Image.BOX), (ox, oy))
            rbl.append(bl)
            to_game = lambda pt: ((pt[0] - box[0]) * sx + ox, (pt[1] - box[1]) * sy + oy)
            guard, tip, _ = geo
            g, t = to_game(guard), to_game(tip)
            ln = math.hypot(t[0] - g[0], t[1] - g[1])
            ux, uy = (t[0] - g[0]) / ln, (t[1] - g[1]) / ln
            hand = (g[0] - ux * HAND_BEHIND_GUARD, g[1] - uy * HAND_BEHIND_GUARD)
            deg = math.degrees(math.atan2(-uy, ux))
            # 칼이 지나가던 띠 (몸 안쪽 구멍 메우기용)
            hole = set()
            for k in range(-6, int(ln) + 3):
                cx, cy = g[0] + ux * k, g[1] + uy * k
                for a in range(-2, 3):
                    for b in range(-2, 3):
                        q = (int(cx) + a, int(cy) + b)
                        if 0 <= q[0] < W and 0 <= q[1] < H:
                            hole.add(q)
            fill_holes(c, hole)
            pre = ref.clean_body(c)
            hox, hoy = ref.fit_head(pre)
            c = ref.with_idle_head(pre)
            if hand[1] < hoy + 18:
                # 손이 머리 높이 위: 머리를 바꿔 붙이며 덮인 팔(손 → 어깨 띠)을 원래 그림으로 되살린다
                restore_arm(c, pre, hand, (hox + 17, hoy + 23))
            rb.append(c)
            rh.append((hand, deg))
        bodies.append(rb)
        hands.append(rh)
        blues.append(rbl)
    # 제자리 공격: 모든 프레임을 같은 양만큼 옮겨 발 가운데 평균을 Idle 과 맞춘다
    centers = [feet_center(b) for rb in bodies for b in rb]
    gdx = round(IDLE_FEET_CENTER - sum(centers) / len(centers))
    print('feet centers', [round(c, 1) for c in centers], 'shift', gdx)
    idle = Image.open(os.path.join(ref.ROOT, 'assets/images/player/idle/side.png')).convert('RGBA')
    recover = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    recover.alpha_composite(idle.crop((0, 0, 32, 48)), (32, 8))
    recover_sword = config.PLAYER_ATTACK_SWORD[0][-1]
    table, sheets, hand_sheets = [], [], []
    for hit in range(3):
        row_t, frames, hframes = [], [], []
        swords = []
        for i in range(4):
            (hx, hy), deg = hands[hit][i]
            hx += gdx
            body = shifted(bodies[hit][i], gdx)
            entry = (int(hx), int(hy), round(deg), False)
            row_t.append(entry)
            swords.append({'hand': [entry[0] + 0.5, entry[1] + 0.5], 'angle': entry[2], 'blade': v2.BLADE})
            frames.append(body)
            hl = front_layer(body, shifted_l(blues[hit][i], gdx), entry)
            hand_c = (entry[0] + 0.5, entry[1] + 0.5)
            if not near_hand(hl, hand_c):  # 손 자리에 몸 그림이 없으면 (머리에 가려진 경우 등) 주먹을 그린다
                print('no hand pixels -> glove', hit + 1, i + 1)
                hl.alpha_composite(glove(hand_c))
            hframes.append(hl)
        row_t.append(recover_sword)
        swords.append({'hand': [recover_sword[0] + 0.5, recover_sword[1] + 0.5], 'angle': recover_sword[2],
                       'blade': v2.BLADE})
        frames.append(recover)
        hframes.append(glove((recover_sword[0] + 0.5, recover_sword[1] + 0.5)))
        out = []
        for i, body in enumerate(frames):
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            kind = SMEARS.get((hit, i))
            if kind == 'line':
                v2.draw_lines(img, swords[i])
            elif kind:
                prev = dict(swords[i - 1], angle=kind[1]) if kind[1] is not None else swords[i - 1]
                v2.draw_arc(img, prev, swords[i], kind[0])
            img.alpha_composite(body)  # 잔상은 몸 아래
            out.append(img)
        table.append(row_t)
        sheets.append(out)
        hand_sheets.append(hframes)
    os.makedirs(OUT, exist_ok=True)
    for n in range(3):
        for suffix, frames in (('', sheets[n]), ('_hand', hand_sheets[n])):
            s = Image.new('RGBA', (W * 5, H), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                s.alpha_composite(f, (W * i, 0))
            s.save(os.path.join(OUT, f'side_{n + 1}{suffix}.png'))
    with open(os.path.join(OUT, 'sword_table.txt'), 'w', encoding='utf-8') as fp:
        fp.write('PLAYER_ATTACK_SWORD = (\n')
        for row_t in table:
            fp.write('    (' + ', '.join(f'({a}, {b}, {c}, {d})' for a, b, c, d in row_t) + '),\n')
        fp.write(')\n')
    # 확인용: 게임처럼 몸 → 칼 → 오른손
    sword_img = v2.sword_image()
    bg = (24, 20, 32, 255)
    view = Image.new('RGBA', (W * 5, H * 3), bg)
    gif, durs = [], []
    for r in range(3):
        prev_end = 0.0
        for i in range(5):
            full = v2.with_sword(sheets[r][i], sword_img, table[r][i])
            full.alpha_composite(hand_sheets[r][i])
            view.alpha_composite(full, (W * i, H * r))
            if i < 4 or r == 2:
                g = Image.new('RGBA', (W, H), bg)
                g.alpha_composite(full)
                gif.append(g.resize((W * 4, H * 4), Image.NEAREST).convert('P', palette=Image.ADAPTIVE))
                end = config.PLAYER_ATTACK_FRAME_ENDS[r][i]
                durs.append(int((end - prev_end) * config.PLAYER_ATTACK_DURATIONS[r] * 1000))
                prev_end = end
    durs[-1] = 600
    view.resize((view.width * 3, view.height * 3), Image.NEAREST).save(os.path.join(OUT, 'sheet_x3.png'))
    gif[0].save(os.path.join(OUT, 'combo_preview.gif'), save_all=True, append_images=gif[1:],
                duration=durs, loop=0, disposal=2)
    print(open(os.path.join(OUT, 'sword_table.txt'), encoding='utf-8').read())


if __name__ == '__main__':
    main()
