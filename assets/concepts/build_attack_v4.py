"""ChatGPT 공격 참고 시트 v3 (타마다 한 장, 2행 × 4열 = 8칸, 칼 = 파란 단색, 두 손 잡기) → 게임 공격 그림.

build_attack_v3.py 와 같은 가공을 하되, 타마다 8칸 + 마지막에 복귀(Idle 몸) = 9프레임을 만든다.
- 칸 찾기: 시트를 2행 × 4열로 나누고, 칸마다 그 칸에 중심이 있는 그림 덩어리들을 묶는다.
- 크기: 3타 첫 칸(가장 곧게 선 자세)의 키를 Idle 키에 맞춘 배율에 가로·세로 보정(0.88 × 0.95)을 곱해 모든 칸에 쓴다.
- 칼: 파란 칼에서 오른손 위치·각도를 자동으로 뽑고, 파란색만 지운다. 칼 앞의 손·팔은 칼 앞 레이어로 따로 저장한다.
Pillow 필요(게임 실행에는 필요 없음).
사용: 저장소 루트에서
  `python assets/concepts/build_attack_v4.py <1타 시트> <2타 시트> <3타 시트> <출력 폴더>`
  → side_1~3.png, side_1~3_hand.png, sword_table.txt, sheet_x3.png, combo_preview.gif
"""
import math
import os
import sys

HIT_SHEETS, OUT_DIR = sys.argv[1:4], sys.argv[4]
sys.argv = [sys.argv[0], HIT_SHEETS[0], OUT_DIR]  # 아래 모듈들은 argv[1], argv[2] 를 읽는다
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ATTACK_SCALE_X', '0.88')
os.environ.setdefault('ATTACK_SCALE_Y', '1.02')  # 가드 자세가 조금 웅크려 있어 키를 Idle 에 맞추려면 세로를 덜 줄인다
import build_attack_from_reference as ref  # noqa: E402
import build_attack_v2 as v2  # noqa: E402
import build_attack_v3 as v3  # noqa: E402
from PIL import Image  # noqa: E402

config = v2.config
W, H = ref.W, ref.H
COLS, ROWS = 4, 2
CELLS = COLS * ROWS
# 잔상: (타, 프레임) → (회전 방향 +1 반시계 / -1 시계, 꼬리 = 몇 프레임 전 칼 각도) 또는 'line'(찌르기)
# 프레임 사이 각도 차이가 작으면 호가 짧아 도끼날처럼 보이므로, 베는 순간 한 프레임에만 두 프레임 전부터 이어지는 큰 호를 그린다.
# 1타: 머리 뒤(③) → 위(④) → 앞(⑤) → 앞 아래(⑥) 로 시계 방향. 2타: 뒤 아래(②) → 앞 아래(③) → 앞 위(④) → 위(⑤) 반시계.
SMEARS = {(0, 5): (-1, 2), (1, 3): (+1, 2), (2, 3): 'line'}  # 1타 ⑥, 2타 ④, 3타 ④


def components(im):
    """초록이 아닌 픽셀(칼 포함)의 큰 덩어리들: (상자, 중심)."""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    out = []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if seen[y * w + x] or ref.is_bg(px[x, y]):
                continue
            stack = [(x, y)]
            seen[y * w + x] = 1
            x0 = x1 = x
            y0 = y1 = y
            n = sx = sy = 0
            while stack:
                cx, cy = stack.pop()
                n += 1
                sx += cx
                sy += cy
                x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and not ref.is_bg(px[nx, ny]):
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            if n > 200:
                out.append(((x0, y0, x1 + 1, y1 + 1), (sx / n, sy / n), n))
    return out


def find_cells(im):
    """2행 × 4열 칸마다 그 칸 안에 중심이 있는 덩어리들을 묶은 상자 (왼쪽 위부터 시간 순서)."""
    w, h = im.size
    boxes = [None] * CELLS
    for box, (cx, cy), n in components(im):
        k = int(cy // (h / ROWS)) * COLS + int(cx // (w / COLS))
        b = boxes[k]
        boxes[k] = box if b is None else (min(b[0], box[0]), min(b[1], box[1]), max(b[2], box[2]), max(b[3], box[3]))
    assert all(boxes), boxes
    return boxes


def body_height(im, box):
    px = im.load()
    ys = [y for y in range(box[1], box[3]) for x in range(box[0], box[2], 2)
          if not ref.is_bg(px[x, y]) and not v3.is_blue(px[x, y])]
    return max(ys) - min(ys)


def main():
    sheets_src = [Image.open(p).convert('RGB') for p in HIT_SHEETS]
    cells = [find_cells(im) for im in sheets_src]
    base = ref.IDLE_HEIGHT / body_height(sheets_src[2], cells[2][0])  # 3타 첫 칸: 가장 곧게 선 자세
    sx, sy = base * ref.SCALE_X, base * ref.SCALE_Y
    print('scale', round(sx, 4), round(sy, 4))
    bodies, hands, blues = [], [], []
    for im, boxes in zip(sheets_src, cells):
        clean = im.copy()
        cp, ip = clean.load(), im.load()
        for y in range(im.height):
            for x in range(im.width):
                if v3.is_blue(ip[x, y]):
                    cp[x, y] = (0, 255, 0)
        rb, rh, rbl = [], [], []
        for box in boxes:
            guard, tip, _ = v3.sword_geometry(im, box)
            f = ref.shrink(clean, box, (sx, sy))
            fx, fb = ref.back_foot_x(f)
            ox, oy = ref.STAND_BACK_FOOT_X - fx, ref.FOOT_ROW - fb
            c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            c.paste(f, (ox, oy), f)
            cell = im.crop(box)
            mask = Image.new('L', cell.size, 0)
            mask.putdata([255 if v3.is_blue(q) else 0 for q in cell.getdata()])
            bl = Image.new('L', (W, H), 0)
            bl.paste(mask.resize(f.size, Image.BOX), (ox, oy))
            to_game = lambda pt: ((pt[0] - box[0]) * sx + ox, (pt[1] - box[1]) * sy + oy)
            g, t = to_game(guard), to_game(tip)
            ln = math.hypot(t[0] - g[0], t[1] - g[1])
            ux, uy = (t[0] - g[0]) / ln, (t[1] - g[1]) / ln
            hand = (g[0] - ux * v3.HAND_BEHIND_GUARD, g[1] - uy * v3.HAND_BEHIND_GUARD)
            deg = math.degrees(math.atan2(-uy, ux))
            hole = set()
            for k in range(-6, int(ln) + 3):
                cx, cy = g[0] + ux * k, g[1] + uy * k
                for a in range(-2, 3):
                    for b in range(-2, 3):
                        q = (int(cx) + a, int(cy) + b)
                        if 0 <= q[0] < W and 0 <= q[1] < H:
                            hole.add(q)
            v3.fill_holes(c, hole)
            pre = ref.clean_body(c)
            hox, hoy = ref.fit_head(pre)
            c = ref.with_idle_head(pre)
            if hand[1] < hoy + 18:
                v3.restore_arm(c, pre, hand, (hox + 17, hoy + 23))
            rb.append(c)
            rh.append((hand, deg))
            rbl.append(bl)
        bodies.append(rb)
        hands.append(rh)
        blues.append(rbl)
    centers = [v3.feet_center(b) for rb in bodies for b in rb]
    gdx = round(v3.IDLE_FEET_CENTER - sum(centers) / len(centers))
    print('feet centers', [round(c, 1) for c in centers], 'shift', gdx)
    idle = Image.open(os.path.join(ref.ROOT, 'assets/images/player/idle/side.png')).convert('RGBA')
    recover = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    recover.alpha_composite(idle.crop((0, 0, 32, 48)), (32, 8))
    recover_sword = (49, 42, -60, False)  # 복귀(Idle 몸): 칼을 오른쪽 아래로 내림
    table, sheets, hand_sheets = [], [], []
    for hit in range(3):
        row_t, frames, hframes, swords = [], [], [], []
        for i in range(CELLS):
            (hx, hy), deg = hands[hit][i]
            body = v3.shifted(bodies[hit][i], gdx)
            entry = (int(hx + gdx), int(hy), round(deg), False)
            hand_c = (entry[0] + 0.5, entry[1] + 0.5)
            row_t.append(entry)
            swords.append({'hand': list(hand_c), 'angle': entry[2], 'blade': v2.BLADE})
            frames.append(body)
            hl = v3.front_layer(body, v3.shifted_l(blues[hit][i], gdx), entry)
            if not v3.near_hand(hl, hand_c):
                print('no hand pixels -> glove', hit + 1, i + 1)
                hl.alpha_composite(v3.glove(hand_c))
            hframes.append(hl)
        row_t.append(recover_sword)
        hand_c = (recover_sword[0] + 0.5, recover_sword[1] + 0.5)
        swords.append({'hand': list(hand_c), 'angle': recover_sword[2], 'blade': v2.BLADE})
        frames.append(recover)
        hframes.append(v3.glove(hand_c))
        out = []
        for i, body in enumerate(frames):
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            kind = SMEARS.get((hit, i))
            if kind == 'line':
                v2.draw_lines(img, swords[i])
            elif kind:
                v2.draw_arc(img, swords[i - kind[1]], swords[i], kind[0])
            img.alpha_composite(body)
            out.append(img)
        table.append(row_t)
        sheets.append(out)
        hand_sheets.append(hframes)
    n_frames = CELLS + 1
    os.makedirs(OUT_DIR, exist_ok=True)
    for n in range(3):
        for suffix, frames in (('', sheets[n]), ('_hand', hand_sheets[n])):
            s = Image.new('RGBA', (W * n_frames, H), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                s.alpha_composite(f, (W * i, 0))
            s.save(os.path.join(OUT_DIR, f'side_{n + 1}{suffix}.png'))
    text = 'PLAYER_ATTACK_SWORD = (\n'
    for row_t in table:
        text += '    (\n        ' + ',\n        '.join(f'({a}, {b}, {c}, {d})' for a, b, c, d in row_t) + ',\n    ),\n'
    text += ')\n'
    with open(os.path.join(OUT_DIR, 'sword_table.txt'), 'w', encoding='utf-8') as fp:
        fp.write(text)
    # 확인용: 게임처럼 몸 → 칼 → 칼 앞 레이어
    sword_img = v2.sword_image()
    bg = (24, 20, 32, 255)
    view = Image.new('RGBA', (W * n_frames, H * 3), bg)
    for r in range(3):
        for i in range(n_frames):
            full = v2.with_sword(sheets[r][i], sword_img, table[r][i])
            full.alpha_composite(hand_sheets[r][i])
            view.alpha_composite(full, (W * i, H * r))
    view.resize((view.width * 3, view.height * 3), Image.NEAREST).save(os.path.join(OUT_DIR, 'sheet_x3.png'))
    print(text)


if __name__ == '__main__':
    main()
