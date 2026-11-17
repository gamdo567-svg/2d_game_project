"""ChatGPT 공격 참고 시트 → 게임 공격 그림 v2: 몸 시트(칼 없음) + 무기 그림(각도별 칼) + 잔상.

build_attack_from_reference.py 의 가공(배경 제거, 축소, 팔레트, Idle 머리)을 그대로 쓰고 다음을 더한다.
1. 세 타 모두 같은 배율, 가로 0.88 × 세로 0.95 보정 (원본 캐릭터가 Idle 보다 통통함, 2026-11-16 사용자 선택 C).
2. 칼 분리: 참고 그림의 칼을 지운 몸 시트(sword_attack/side_N.png)를 만든다. 칼 그림 한 장(weapons/old_sword.png,
   칼끝 오른쪽, 손이 한가운데)은 weapons/build_old_sword.py 가 따로 만든다. 게임은 game/config.py 의 PLAYER_ATTACK_SWORD(손 위치·각도)대로
   칼 그림을 옮기고 돌려서 몸 위에 겹쳐 그린다.
3. 잔상: 칼끝이 지나간 호(1타 ③, 2타 ②③), 찌르기 속도선(3타 ③). 몸 시트에서 몸 아래에 깐다.
Pillow 필요(게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/build_attack_v2.py <참고 시트> <출력 폴더>`
     → side_1~3.png, old_sword.png, sheet_x3.png(칼까지 합친 확인용), combo_preview.gif
"""
import math
import os
import sys

os.environ.setdefault('ATTACK_SCALE_X', '0.88')
os.environ.setdefault('ATTACK_SCALE_Y', '0.95')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_attack_from_reference as ref  # noqa: E402  (sys.argv 의 시트·출력 폴더를 같이 씀)
from PIL import Image  # noqa: E402

sys.path.insert(0, ref.ROOT)
from game import config  # noqa: E402

W, H = ref.W, ref.H
SRC, OUT = ref.SRC, ref.OUT

# 칼 색 (원본 낡은 검 kit/ref_side_right_sword_96x64.png)
S_OUT = (0x16, 0x0F, 0x14, 255)
S_LIGHT = (0xDA, 0xCA, 0xBE, 255)
S_MID = (0xC3, 0xAF, 0xA7, 255)
S_RUST = (0xAD, 0x88, 0x70, 255)
S_GUARD = (0x69, 0x53, 0x5A, 255)
S_GRIP = (0x2A, 0x24, 0x2D, 255)
GLOVE = (0x30, 0x1E, 0x25, 255)
SMEAR_HI = (0xEC, 0xE2, 0xD6, 255)
SMEAR = (0xC3, 0xAF, 0xA7, 255)
GRIP = 3  # 손에서 칼날 시작(가드 끝)까지 거리
BLADE = 20  # 칼날 길이: 손에서 칼끝까지 GRIP + BLADE = 23 (낡은 검 그림과 같게, 잔상 반지름에 씀)
REF_BLADE = 13  # 참고 그림의 칼을 지울 때 쓰는 칼날 길이 (참고 그림 기준)

# 칼 위치는 게임 설정(PLAYER_ATTACK_SWORD)을 그대로 쓴다. 참고 시트의 칼 위치를 보고 정했고,
# 3타 ①② 는 요청대로 칼끝이 앞(0도)을 향하게 고쳤다 (참고 시트는 뒤를 향함).
SWORDS = config.PLAYER_ATTACK_SWORD
SW, SH = config.PLAYER_SWORD_SPRITE_WIDTH, config.PLAYER_SWORD_SPRITE_HEIGHT
# 프레임별 몸 가로 보정(픽셀, 앞 +). 뒷발이 망토에 가려 잘못 맞춰진 프레임을 바로잡는다.
# 2타 ①: 1타 ④ 에서 바로 이어지므로 1타 ④ 와 발 위치(46~71)가 같도록 5픽셀 뒤로 (칼 손 위치도 config 에서 같이 옮김)
# 모든 공격 프레임(복귀 제외)을 한꺼번에 뒤로 옮기는 양. 참고 그림은 뒷발 기준이라 몸이 칸보다 평균 8픽셀 앞에 있어
# 공격이 끝나면 Idle 자리로 튀어 돌아왔다 → 발 가운데가 Idle(49.5)과 비슷해지도록 (제자리 공격, 2026-11-16)
GLOBAL_DX = -8
BODY_DX = {(1, 0): -5, (1, 1): 4, (1, 2): 8, (1, 3): 2, (2, 0): 3}
# 상체 보정 (앞 +, 아래 +): 허리(CUT 줄) 위를 머리 쪽으로 갈수록 더 옮겨 기울기를 바꾸고(dx), 위쪽 전체를 내린다(dy).
# 2타는 참고 그림에서 머리가 한 프레임마다 11픽셀씩 뒤·위로 튀어서, 머리가 부드럽게 올라가도록 줄였다.
UPPER = {(1, 1): (3, 0), (1, 2): (4, 3)}
CUT = 39


def adjust(img, key):
    """상체 보정: 허리 위 줄을 위로 갈수록 dx 까지 옮기고(기울기), 위쪽 전체를 dy 만큼 내린다."""
    dx, dy = UPPER.get(key, (0, 0))
    if not dx and not dy:
        return img
    src = img.load()
    rows = [y for y in range(H) if any(src[x, y][3] for x in range(W))]
    top = rows[0]
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.alpha_composite(img.crop((0, CUT, W, H)), (0, CUT))
    p = out.load()
    for y in range(CUT - 1, top - 1, -1):  # 아래부터 그려서 위쪽(머리)이 덮게
        sx = round(dx * (CUT - y) / (CUT - top))
        for x in range(W):
            if src[x, y][3] and 0 <= x + sx < W and 0 <= y + dy < H:
                p[x + sx, y + dy] = src[x, y]
    return out


def moved_hand(key, hand):
    """상체 보정 뒤 손 위치 (칼 위치표를 고칠 때 확인용)."""
    dx, dy = UPPER.get(key, (0, 0))
    x, y = hand
    if y < CUT and (dx or dy):
        return x + dx, y + dy  # 손은 머리 높이 근처라 dx 전부를 쓴다 (근사)
    return x, y
# 잔상: (타, 프레임) → (호의 회전 방향 +1 반시계 / -1 시계, 꼬리 각도(None 이면 이전 프레임 칼 각도)) 또는 'line'(찌르기)
SMEARS = {(0, 2): (-1, None), (1, 1): (+1, None), (1, 2): (+1, -20), (2, 2): 'line'}


def find_sword(img):
    """참고 그림의 칼날 픽셀로 직선을 맞춰 칼 자리(손 위치, 각도)를 구한다. 칼을 지울 때만 쓴다. 없으면 None."""
    p = img.load()
    pts = [(x + 0.5, y + 0.5) for y in range(H) for x in range(W) if p[x, y][3] and ref.is_blade(p[x, y])]
    if len(pts) < 5:
        return None
    mx = sum(x for x, _ in pts) / len(pts)
    my = sum(y for _, y in pts) / len(pts)
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    syy = sum((y - my) ** 2 for _, y in pts)
    sxy = sum((x - mx) * (y - my) for x, y in pts)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    dx, dy = math.cos(ang), math.sin(ang)
    ts = [(x - mx) * dx + (y - my) * dy for x, y in pts]
    ends = [(mx + min(ts) * dx, my + min(ts) * dy), (mx + max(ts) * dx, my + max(ts) * dy)]
    # 손 쪽 끝 = 몸 중심(칼날 제외 픽셀의 평균)에 더 가까운 끝
    body = [(x, y) for y in range(H) for x in range(W) if p[x, y][3] and not ref.is_blade(p[x, y])]
    bx = sum(x for x, _ in body) / len(body)
    by = sum(y for _, y in body) / len(body)
    ends.sort(key=lambda e: math.hypot(e[0] - bx, e[1] - by))
    base, tip = ends
    length = math.hypot(tip[0] - base[0], tip[1] - base[1]) or 1
    ux, uy = (tip[0] - base[0]) / length, (tip[1] - base[1]) / length
    hand = (tip[0] - ux * (GRIP + REF_BLADE), tip[1] - uy * (GRIP + REF_BLADE))
    return {'hand': list(hand), 'angle': math.degrees(math.atan2(-uy, ux)), 'blade': REF_BLADE}


def axis(x, y, sword):
    """픽셀 (x, y)의 칼 축 좌표: t = 손에서 칼끝 방향 거리, s = 축에서 떨어진 거리(부호)."""
    hx, hy = sword['hand']
    a = math.radians(sword['angle'])
    dx, dy = math.cos(a), -math.sin(a)
    vx, vy = x + 0.5 - hx, y + 0.5 - hy
    return vx * dx + vy * dy, vx * -dy + vy * dx


def sword_pixels(sword, w, h):
    """원본 낡은 검 모양: 손잡이를 쥔 주먹 → 가드 → 칼날(끝으로 갈수록 가늘어짐). {(x, y): 색}."""
    blade = sword['blade']
    out = {}
    for y in range(h):
        for x in range(w):
            t, s = axis(x, y, sword)
            a = abs(s)
            c = None
            if -2.0 <= t < GRIP - 1.3 and a < 1.4:
                c = S_GRIP if a < 0.7 else S_OUT
            elif GRIP - 1.3 <= t < GRIP and a < 2.6:
                c = S_GUARD if a < 1.9 and t < GRIP - 0.4 else S_OUT
            elif GRIP <= t < GRIP + blade + 1.0:
                width = 1.15 if t < GRIP + blade - 2 else max(0.3, 1.15 * (GRIP + blade + 0.3 - t) / 2.3)
                if a < width:
                    c = S_LIGHT if s < 0 else (S_MID if t < GRIP + blade * 0.6 else S_RUST)
                elif a < width + 0.8:
                    c = S_OUT
            if c:
                out[(x, y)] = c
    hx, hy = math.floor(sword['hand'][0] - 0.5), math.floor(sword['hand'][1] - 0.5)
    for q in ((hx, hy), (hx + 1, hy), (hx, hy + 1), (hx + 1, hy + 1)):  # 손잡이를 쥔 주먹 (손 둘레 2×2)
        out[q] = GLOVE
    return out


def sword_image():
    """칼 그림 한 장 (weapons/<무기>.png, 칼끝 오른쪽, 손이 한가운데). 무기 그림은 weapons/build_old_sword.py 가 만든다."""
    return Image.open(os.path.join(ref.ROOT, 'assets/images/player/weapons', f'{config.PLAYER_WEAPON}.png')).convert('RGBA')


def remove_sword(img, sword):
    """칼날 색 픽셀과 칼 자리(가드·칼날 외곽선)를 지운다. 손잡이를 쥔 주먹 자리는 남긴다."""
    p = img.load()
    for y in range(H):
        for x in range(W):
            if not p[x, y][3]:
                continue
            if ref.is_blade(p[x, y]) or p[x, y][:3] in ref.BLADE_PAL:  # 칼날 색은 몸에 남기지 않는다
                p[x, y] = (0, 0, 0, 0)
                continue
            t, s = axis(x, y, sword)
            if GRIP - 1.5 <= t < GRIP + sword['blade'] + 2:
                if abs(s) < 1.5 or (abs(s) < 2.6 and sum(p[x, y][:3]) < ref.DARK_SUM):
                    p[x, y] = (0, 0, 0, 0)


def prune_hilt(img, sword, hand, steps=8):
    """원래 칼 손잡이·가드가 남긴 1픽셀 굵기 선을 지운다: 칼 자리 근처에서 이웃이 2개 이하인 픽셀을 여러 번 깎는다."""
    p = img.load()
    hx, hy = hand

    def near(x, y):
        t, s_ = axis(x, y, sword)
        return (abs(s_) < 3.5 and -6 <= t <= GRIP + sword['blade'] + 3) or math.hypot(x - hx, y - hy) < 9

    for _ in range(steps):
        kill = []
        for y in range(H):
            for x in range(W):
                if not p[x, y][3] or not near(x, y):
                    continue
                n = sum(1 for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and 0 <= x + a < W and 0 <= y + b < H
                        and p[x + a, y + b][3])
                if n <= 2:
                    kill.append((x, y))
        if not kill:
            break
        for q in kill:
            p[q] = (0, 0, 0, 0)


# 칼을 쥔 팔을 직접 그리는 프레임: (타, 프레임) → (어깨 위치 보정 dx, dy, 머리 앞에 그리기).
# 참고 그림의 팔이 Idle 머리에 가려졌거나(1타 ②) 칼과 함께 지워진(3타) 프레임.
# 머리 앞이 아니면 머리보다 먼저 그려 머리 뒤로 들어간다. 1타 ② 는 머리 위로 든 팔이 후드 옆을 지나 앞에 보인다.
ARMS = {(0, 1): (0, 0, True), (2, 0): (-2, 1, False), (2, 1): (-2, 1, False), (2, 2): (0, 0, False),
        (2, 3): (0, 0, False)}
# 소매 색: 어두운 몸통에 묻히지 않도록 Idle 팔레트의 중간 갈색(위쪽은 밝은 갈색)
SLEEVE = (0x5C, 0x37, 0x36, 255)
SLEEVE_HI = (0x76, 0x49, 0x43, 255)
OUTLINE = (0x12, 0x0C, 0x11, 255)


def draw_arm(img, shoulder, hand):
    """어깨에서 손까지 소매(외곽선 포함)와 장갑 낀 손."""
    p = img.load()
    (sx, sy), (hx, hy) = shoulder, hand
    lx, ly = hx - sx, hy - sy
    ln2 = lx * lx + ly * ly or 1
    cells = {}
    for y in range(H):
        for x in range(W):
            cx, cy = x + 0.5, y + 0.5
            k = max(0.0, min(1.0, ((cx - sx) * lx + (cy - sy) * ly) / ln2))
            d = math.hypot(cx - (sx + k * lx), cy - (sy + k * ly))
            dh = math.hypot(cx - hx, cy - hy)
            if dh < 1.2:
                cells[(x, y)] = GLOVE
            elif d < 1.1:
                # 팔의 위쪽 가장자리를 밝게 (빛이 위에서 옴)
                side = (cx - sx) * ly - (cy - sy) * lx
                cells[(x, y)] = SLEEVE_HI if (side > 0) == (lx >= 0) else SLEEVE
            elif d < 1.9 or dh < 2.0:
                cells.setdefault((x, y), OUTLINE)
    for (x, y), c in cells.items():
        p[x, y] = c


def tip_of(sword):
    hx, hy = sword['hand']
    a = math.radians(sword['angle'])
    r = GRIP + sword['blade']
    return hx + r * math.cos(a), hy - r * math.sin(a)


def draw_arc(img, prev, cur, turn):
    """칼끝이 prev 각도에서 cur 각도로 손을 중심으로 돈 호. 칼 쪽은 두껍고 꼬리는 가늘다."""
    p = img.load()
    cx, cy = cur['hand']
    r_out = GRIP + cur['blade'] + 0.5
    a0, a1 = prev['angle'], cur['angle']
    if turn > 0:
        while a1 <= a0:
            a1 += 360
    else:
        while a1 >= a0:
            a1 -= 360
    lo, hi = min(a0, a1), max(a0, a1)
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            r = math.hypot(dx, dy)
            if r > r_out or r < r_out - 7:
                continue
            a = math.degrees(math.atan2(dy, dx))
            for cand in (a - 720, a - 360, a, a + 360, a + 720):
                if lo <= cand <= hi:
                    a = cand
                    break
            else:
                continue
            k = (a - a0) / (a1 - a0)  # 0 꼬리 → 1 칼
            if r >= r_out - (1.5 + 5.0 * k):
                p[x, y] = SMEAR_HI if r > r_out - 1.6 else SMEAR


def draw_lines(img, cur):
    """찌르기 속도선: 칼 위아래로 칼과 나란한 선, 칼끝 앞으로 짧은 선."""
    p = img.load()
    tx, ty = tip_of(cur)
    hx, _ = cur['hand']
    for dy, x0, x1, col in ((-3, hx + 4, tx - 1, SMEAR), (3, hx + 6, tx - 3, SMEAR),
                            (-2, hx - 8, hx + 2, SMEAR_HI), (2, hx - 6, hx + 3, SMEAR_HI),
                            (0, tx + 1, tx + 5, SMEAR_HI)):
        y = int(ty) + dy
        for x in range(int(x0), int(x1)):
            if 0 <= x < W and 0 <= y < H:
                p[x, y] = col


def with_sword(body, sword_img, sword):
    """확인용: 게임처럼 칼 그림 중심을 손 픽셀 가운데에 두고 각도만큼 돌려 겹친다 (nearest)."""
    hx, hy, deg, behind = sword
    rot = sword_img.rotate(deg, resample=Image.NEAREST, expand=True)
    big = Image.new('RGBA', (W + 2 * SW, H + 2 * SW), (0, 0, 0, 0))
    pos = (round(SW + hx + 0.5 - rot.width / 2), round(SW + hy + 0.5 - rot.height / 2))
    if behind:
        big.alpha_composite(rot, pos)
    big.alpha_composite(body, (SW, SW))
    if not behind:
        big.alpha_composite(rot, pos)
    return big.crop((SW, SW, SW + W, SW + H))


def main():
    swords_img = sword_image()
    im = Image.open(SRC).convert('RGB')
    rows = ref.find_cells(im)
    assert len(rows) == 3 and all(len(r) == 5 for r in rows), [len(r) for r in rows]
    base = sum(ref.IDLE_HEIGHT / (r[-1][3] - r[-1][1]) for r in rows) / len(rows)
    scale = (base * ref.SCALE_X, base * ref.SCALE_Y)
    # 복귀(마지막) 프레임 몸: Idle 측면 첫 프레임 그대로 (Idle 로 돌아갈 때 튀지 않게)
    idle = Image.open(os.path.join(ref.ROOT, 'assets/images/player/idle/side.png')).convert('RGBA')
    recover = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    recover.alpha_composite(idle.crop((0, 0, 32, 48)), (32, 8))
    sheets = []
    for hit, row in enumerate(rows):
        bodies = []
        for f in [ref.shrink(im, box, scale) for box in row[:-1]]:
            fx, fb = ref.back_foot_x(f)
            c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            c.paste(f, (ref.STAND_BACK_FOOT_X - fx + GLOBAL_DX + BODY_DX.get((hit, len(bodies)), 0), ref.FOOT_ROW - fb), f)
            c = ref.clean_body(c)
            found = find_sword(c)
            if found:
                remove_sword(c, found)
            key = (hit, len(bodies))
            arm = None
            if key in ARMS:
                # 어깨: Idle 머리를 붙일 자리 기준 (Idle 측면 앞쪽 어깨 ≈ 머리 왼쪽 위에서 (17, 23))
                ox, oy = ref.fit_head(c)
                adx, ady, front = ARMS[key]
                hx, hy, _, _ = SWORDS[hit][len(bodies)]
                arm = ((ox + 17 + adx, oy + 23 + ady), (hx + 0.5, hy + 0.5), front)
                if not front:
                    draw_arm(c, arm[0], arm[1])
            body = ref.with_idle_head(c)
            if arm and arm[2]:
                draw_arm(body, arm[0], arm[1])
            bodies.append(adjust(body, key))
        bodies.append(recover)
        swords = [{'hand': [hx + 0.5, hy + 0.5], 'angle': deg, 'blade': BLADE} for hx, hy, deg, _ in SWORDS[hit]]
        out = []
        for i, body in enumerate(bodies):
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            kind = SMEARS.get((hit, i))
            if kind == 'line':
                draw_lines(img, swords[i])
            elif kind:
                prev = dict(swords[i - 1], angle=kind[1]) if kind[1] is not None else swords[i - 1]
                draw_arc(img, prev, swords[i], kind[0])
            img.alpha_composite(body)  # 잔상은 몸 아래
            out.append(img)
        sheets.append(out)
    os.makedirs(OUT, exist_ok=True)
    for n, frames in enumerate(sheets, start=1):
        s = Image.new('RGBA', (W * 5, H), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            s.alpha_composite(f, (W * i, 0))
        s.save(os.path.join(OUT, f'side_{n}.png'))
    # 확인용: 칼까지 합친 모습 (게임 배경색, 3배)과 콤보 GIF (1·2타는 복귀 프레임을 건너뛰고 이어짐)
    bg = (24, 20, 32, 255)
    view = Image.new('RGBA', (W * 5, H * 3), bg)
    gif, durs = [], []
    for r, frames in enumerate(sheets):
        prev_end = 0.0
        for i, f in enumerate(frames):
            full = with_sword(f, swords_img, SWORDS[r][i])
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


if __name__ == '__main__':
    main()
