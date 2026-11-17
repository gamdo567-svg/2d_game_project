"""ChatGPT 정면·후면 공격 참고 시트(3행 × 5열, 칼 = 파란 단색, 두 손 잡기) → 게임 공격 그림.

측면용 build_attack_v3.py 와 같은 가공을 방향에 맞게 한다.
- 머리: 그 방향의 Idle 머리(idle/front.png, idle/back.png)로 바꿔 붙인다.
- 발: 프레임마다 발 가운데를 그 방향 Idle 의 발 가운데에 맞춘다 (정면·후면은 좌우가 대칭이라 뒷발 기준이 없음).
- 칼 길이 비율: 화면 안쪽·바깥쪽으로 찌르는 칼은 원근으로 짧아 보이므로, 파란 칼 길이 ÷ 칼 그림 길이를 같이 뽑는다.
- 마지막(복귀) 프레임은 그 방향 Idle 몸 + 아래로 내린 칼.
Pillow 필요(게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/build_attack_view.py <참고 시트> <front|back> <출력 폴더>`
     → <방향>_1~3.png, <방향>_1~3_hand.png, sword_table.txt, sheet_x3.png
"""
import math
import os
import sys

SHEET, VIEW, OUT_DIR = sys.argv[1:4]
sys.argv = [sys.argv[0], SHEET, OUT_DIR]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ATTACK_SCALE_X', '0.88')
os.environ.setdefault('ATTACK_SCALE_Y', '0.95')
import build_attack_from_reference as ref  # noqa: E402
import build_attack_v2 as v2  # noqa: E402
import build_attack_v3 as v3  # noqa: E402
from PIL import Image  # noqa: E402

config = v2.config
W, H = ref.W, ref.H
SWORD_REACH = 21  # 칼 그림에서 가드 → 칼끝 거리 (old_sword.png: 가드 30열, 칼끝 51열)

# 그 방향의 Idle 그림으로 머리 바꾸기 기준을 바꾼다 (ref 의 함수들은 이 전역 값을 쓴다)
IDLE = Image.open(os.path.join(ref.ROOT, f'assets/images/player/idle/{VIEW}.png')).convert('RGBA').crop((0, 0, 32, 48))
ref.IDLE_HEAD = IDLE.crop((0, 0, 32, 21))
ref.HEAD_PTS = [(x, y) for y in range(21) for x in range(32) if ref.IDLE_HEAD.getpixel((x, y))[3]]
# 오른쪽 어깨: 정면은 보는 사람 기준 왼쪽, 후면은 오른쪽 (머리 그림 왼쪽 위 기준)
SHOULDER = {'front': (8, 23), 'back': (24, 23)}[VIEW]
# 복귀 프레임 칼: 오른손을 몸 옆에 내리고 칼끝은 아래 (정면은 보는 사람 기준 왼쪽, 후면은 오른쪽)
# 잔상: (타, 프레임) → (회전 방향 +1 반시계 / -1 시계, 꼬리 = 몇 프레임 전 칼 각도) 또는 'thrust'(칼 방향 속도선)
# 정면: 1타 ④ 어깨 위 → 몸 앞을 가로질러 아래로 (시계), 2타 ② 왼쪽 아래 → 왼쪽 위로 올려침 (시계), 3타 ③④ 아래로 찌름
SMEARS = {
    'front': {(0, 3): (-1, 2), (1, 1): (-1, 1), (2, 2): 'thrust', (2, 3): 'thrust'},
    'back': {},
}[VIEW]
RECOVER_SWORD = {'front': (39, 41, -100, False, 0.7), 'back': (56, 41, -80, True, 0.7)}[VIEW]


def isolate(im, rows):
    """칸마다 자기 그림 덩어리만 남긴 잘라낸 그림. 크게 펄럭이는 망토·칼끝이 옆 칸 상자에 들어와도 섞이지 않게,
    상자 안에서 다른 칸 덩어리에 속한 픽셀은 초록 배경으로 칠한다."""
    w, h = im.size
    px = im.load()
    label = [0] * (w * h)
    sizes = {}
    n = 0
    for y in range(h):
        for x in range(w):
            if label[y * w + x] or ref.is_bg(px[x, y]):
                continue
            n += 1
            label[y * w + x] = n
            stack, cnt = [(x, y)], 0
            while stack:
                cx, cy = stack.pop()
                cnt += 1
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not label[ny * w + nx] and not ref.is_bg(px[nx, ny]):
                        label[ny * w + nx] = n
                        stack.append((nx, ny))
            sizes[n] = cnt
    out = []
    for row in rows:
        cells = []
        for box in row:
            x0, y0, x1, y1 = box
            # 이 칸의 덩어리: 상자 가운데 쪽에서 가장 많이 보이는 큰 덩어리들 (상자 안 픽셀의 절반 이상이 상자 안에 있는 것)
            counts = {}
            for y in range(y0, y1):
                for x in range(x0, x1):
                    k = label[y * w + x]
                    if k:
                        counts[k] = counts.get(k, 0) + 1
            mine = {k for k, c in counts.items() if c >= sizes[k] * 0.5}
            cell = im.crop(box)
            cp = cell.load()
            for y in range(y0, y1):
                for x in range(x0, x1):
                    k = label[y * w + x]
                    if k and k not in mine:
                        cp[x - x0, y - y0] = (0, 255, 0)
            cells.append(cell)
        out.append(cells)
    return out


def keep_largest(img):
    """몸(가장 큰 덩어리)에 붙지 않은 조각을 모두 지운다."""
    ref.remove_specks(img, max_size=W * H)


def idle_feet_center():
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    c.alpha_composite(IDLE, (32, 8))
    return v3.feet_center(c)


def main():
    im = Image.open(SHEET).convert('RGB')
    rows = ref.find_cells(im)
    assert len(rows) == 3 and all(len(r) == 5 for r in rows), [len(r) for r in rows]
    # 크기: 측면과 같은 방법 (각 행 마지막 = 서 있는 복귀 자세의 키를 Idle 키에 맞춤)
    base = sum(ref.IDLE_HEIGHT / v3_body_height(im, r[-1]) for r in rows) / len(rows)
    sx, sy = base * ref.SCALE_X, base * ref.SCALE_Y
    target = idle_feet_center()
    cells = isolate(im, rows)
    clean = im.copy()
    cp, ip = clean.load(), im.load()
    for y in range(im.height):
        for x in range(im.width):
            if v3.is_blue(ip[x, y]):
                cp[x, y] = (0, 255, 0)
    recover = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    recover.alpha_composite(IDLE, (32, 8))
    table, sheets, hand_sheets = [], [], []
    for hit, row in enumerate(rows):
        row_t, frames, hframes = [], [], []
        for col, gbox in enumerate(row[:-1]):
            cimg = cells[hit][col]
            box = (0, 0) + cimg.size
            cclean = cimg.copy()
            cc = cclean.load()
            for y in range(cimg.height):
                for x in range(cimg.width):
                    if v3.is_blue(cc[x, y]):
                        cc[x, y] = (0, 255, 0)
            guard, tip, _ = v3.sword_geometry(cimg, box)
            f = ref.shrink(cclean, box, (sx, sy))
            # 발 가운데를 Idle 발 가운데에, 발끝 줄을 FOOT_ROW 에
            tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            _, fb = ref.back_foot_x(f)
            tmp.paste(f, (0, ref.FOOT_ROW - fb), f)
            ox = round(target - v3.feet_center(tmp))
            oy = ref.FOOT_ROW - fb
            c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            c.paste(f, (ox, oy), f)
            cell = cimg
            mask = Image.new('L', cell.size, 0)
            mask.putdata([255 if v3.is_blue(q) else 0 for q in cell.getdata()])
            blue = Image.new('L', (W, H), 0)
            blue.paste(mask.resize(f.size, Image.BOX), (ox, oy))
            to_game = lambda pt: ((pt[0] - box[0]) * sx + ox, (pt[1] - box[1]) * sy + oy)
            g, t = to_game(guard), to_game(tip)
            ln = math.hypot(t[0] - g[0], t[1] - g[1])
            ux, uy = (t[0] - g[0]) / ln, (t[1] - g[1]) / ln
            ratio = ln / SWORD_REACH  # 아래에서 시트의 가장 긴 칼 기준으로 다시 나눈다
            back = v3.HAND_BEHIND_GUARD * ratio
            hand = (g[0] - ux * back, g[1] - uy * back)
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
            body = ref.with_idle_head(pre)
            keep_largest(body)  # 머리를 바꾸며 끊어진 망토 조각(머리 위로 펄럭이던 부분) 제거
            if hand[1] < hoy + 18:
                v3.restore_arm(body, pre, hand, (hox + SHOULDER[0], hoy + SHOULDER[1]))
            entry = (int(hand[0]), int(hand[1]), round(deg), False, round(ratio, 2))
            hl = v3.front_layer(body, blue, entry[:4])
            hand_c = (entry[0] + 0.5, entry[1] + 0.5)
            if not v3.near_hand(hl, hand_c):
                print('no hand pixels -> glove', hit + 1, len(frames) + 1)
                hl.alpha_composite(v3.glove(hand_c))
            row_t.append(entry)
            frames.append(body)
            hframes.append(hl)
        row_t.append(RECOVER_SWORD)
        frames.append(recover)
        hframes.append(v3.glove((RECOVER_SWORD[0] + 0.5, RECOVER_SWORD[1] + 0.5)))
        table.append(row_t)
        sheets.append(frames)
        hand_sheets.append(hframes)
    # 칼 길이 비율은 시트 안에서 가장 긴 칼(원근 없이 옆으로 누운 칼)을 1.0 으로 다시 맞춘다
    longest = max(e[4] for row_t in table for e in row_t[:-1])
    table = [[e[:4] + (round(min(1.0, e[4] / longest), 2),) for e in row_t[:-1]] + [row_t[-1]] for row_t in table]
    # 잔상: 몸 아래에 깐다 (칼 길이 비율을 반영한 칼끝 거리)
    for hit in range(3):
        swords = [{'hand': [e[0] + 0.5, e[1] + 0.5], 'angle': e[2],
                   'blade': (v2.GRIP + v2.BLADE) * e[4] - v2.GRIP} for e in table[hit]]
        for i in range(5):
            kind = SMEARS.get((hit, i))
            if not kind:
                continue
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            if kind == 'thrust':
                draw_thrust(img, swords[i])
            else:
                v2.draw_arc(img, swords[i - kind[1]], swords[i], kind[0])
            img.alpha_composite(sheets[hit][i])
            sheets[hit][i] = img
    os.makedirs(OUT_DIR, exist_ok=True)
    for n in range(3):
        for suffix, frames in (('', sheets[n]), ('_hand', hand_sheets[n])):
            s = Image.new('RGBA', (W * 5, H), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                s.alpha_composite(f, (W * i, 0))
            s.save(os.path.join(OUT_DIR, f'{VIEW}_{n + 1}{suffix}.png'))
    text = f'PLAYER_ATTACK_SWORD_{VIEW.upper()} = (\n'
    for row_t in table:
        text += '    (' + ', '.join(str(e) for e in row_t) + '),\n'
    text += ')\n'
    with open(os.path.join(OUT_DIR, 'sword_table.txt'), 'w', encoding='utf-8') as fp:
        fp.write(text)
    # 확인용: 몸 → 칼(길이 비율 적용) → 칼 앞 레이어
    sword_img = v2.sword_image()
    bg = (24, 20, 32, 255)
    view = Image.new('RGBA', (W * 5, H * 3), bg)
    for r in range(3):
        for i in range(5):
            hx, hy, deg, behind, ratio = table[r][i]
            sw = sword_img.resize((max(1, round(sword_img.width * ratio)), sword_img.height), Image.NEAREST)
            full = v2.with_sword(sheets[r][i], sw, (hx, hy, deg, behind))
            full.alpha_composite(hand_sheets[r][i])
            view.alpha_composite(full, (W * i, H * r))
    view.resize((view.width * 3, view.height * 3), Image.NEAREST).save(os.path.join(OUT_DIR, 'sheet_x3.png'))
    print(text)


def draw_thrust(img, sword):
    """찌르기 속도선: 칼과 나란한 선 3줄 (칼 양옆, 칼끝 앞)."""
    p = img.load()
    hx, hy = sword['hand']
    a = math.radians(sword['angle'])
    ux, uy = math.cos(a), -math.sin(a)
    px_, py_ = -uy, ux  # 칼에 수직
    reach = v2.GRIP + sword['blade']
    for off, t0, t1, col in ((-3, 4, reach - 1, v2.SMEAR), (3, 6, reach - 3, v2.SMEAR),
                             (0, reach + 1, reach + 6, v2.SMEAR_HI)):
        for k in range(int(t0 * 2), int(t1 * 2)):
            t = k / 2
            x, y = int(hx + ux * t + px_ * off), int(hy + uy * t + py_ * off)
            if 0 <= x < W and 0 <= y < H:
                p[x, y] = col


def v3_body_height(im, box):
    px = im.load()
    ys = [y for y in range(box[1], box[3]) for x in range(box[0], box[2], 2)
          if not ref.is_bg(px[x, y]) and not v3.is_blue(px[x, y])]
    return max(ys) - min(ys)


if __name__ == '__main__':
    main()
