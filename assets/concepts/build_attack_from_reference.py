"""ChatGPT 공격 참고 시트(3행 × 5열, 초록 배경)를 게임용 공격 시트(96×64 × 5프레임 × 3타)로 바꾼다.

Idle·Walk v3 와 같은 방식: 원본 그림을 칸별로 잘라 초록 배경을 지우고, 게임 크기로 줄인 뒤 Idle·Walk 팔레트로 맞춘다.
- 크기: 각 행의 마지막(복귀, 서 있는) 칸의 키를 Idle 키(46줄)에 맞춘 배율을 그 행 전체에 쓴다.
- 위치: 발끝은 FOOT_ROW 줄, 가로는 뒷발(가장 왼쪽 부츠) 위치를 복귀 칸 기준으로 맞춘다 → 몸이 앞으로 나가는 움직임이 남는다.
Pillow 필요(게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/build_attack_from_reference.py <참고 시트> <출력 폴더>`
     → <출력 폴더>/side_1.png ~ side_3.png, cells_x4.png(확인용)
"""
import os
import sys

from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
W, H = 96, 64
FOOT_ROW = 55
IDLE_HEIGHT = 46  # Idle 측면: 후드 꼭대기(2행) ~ 발끝(47행)
STAND_BACK_FOOT_X = 32 + 13  # Idle 측면 뒷발(가장 왼쪽 부츠) x, 96 캔버스 기준


def is_bg(p):
    r, g, b = p[:3]
    return g > 150 and g > r + 50 and g > b + 50


def colors_of(*paths):
    cols = set()
    for path in paths:
        for p in Image.open(os.path.join(ROOT, path)).convert('RGBA').getdata():
            if p[3]:
                cols.add(p[:3])
    return cols


# 몸: Idle·Walk 공용 28색만. 칼날: 기준 검의 밝은 회색 계열만 추가
BODY_PAL = sorted(colors_of('assets/images/player/idle/side.png', 'assets/images/player/walk/side.png'))
BLADE_PAL = sorted(c for c in colors_of('assets/concepts/pixellab/kit/ref_side_right_sword_64.png')
                   if c not in BODY_PAL and sum(c) > 330)
# 색 보정 (Idle·Walk 가공과 같은 목적): ChatGPT 원본은 Idle 보다 밝아서, 몸 색의 밝기를 Idle 에 맞춘다.
# 갈색 밝기 Idle 0.408 / 보정 전 공격 약 0.468 → 팔레트 맞춤까지 고려해 0.82 배 (보정 후 전체 밝기가 Idle 과 비슷)
BODY_VALUE_SCALE = float(os.environ.get('ATTACK_VALUE_SCALE', 0.9))
# 키 기준 배율에 곱하는 가로·세로 보정. 1.0 이면 키만 Idle 에 맞춤 (원본이 Idle 보다 통통해 굵어 보임)
SCALE_X = float(os.environ.get('ATTACK_SCALE_X', 1.0))
SCALE_Y = float(os.environ.get('ATTACK_SCALE_Y', 1.0))


def is_blade(c):
    r, g, b = c[:3]
    return min(r, g, b) > 120 and max(r, g, b) - min(r, g, b) < 60  # 밝고 채도가 낮은 금속색


def snap(c):
    r, g, b = c
    if is_blade(c):
        pal = BLADE_PAL + BODY_PAL
    else:
        r, g, b = (v * BODY_VALUE_SCALE for v in (r, g, b))
        pal = BODY_PAL
    return min(pal, key=lambda q: (q[0] - r) ** 2 * 2 + (q[1] - g) ** 2 * 4 + (q[2] - b) ** 2 * 3)


def find_cells(im):
    """초록이 아닌 픽셀의 연결 요소(큰 것)를 행·열 순서로."""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    comps = []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if seen[y * w + x] or is_bg(px[x, y]):
                continue
            stack = [(x, y)]
            seen[y * w + x] = 1
            x0 = x1 = x
            y0 = y1 = y
            n = 0
            while stack:
                cx, cy = stack.pop()
                n += 1
                x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and not is_bg(px[nx, ny]):
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            if n > 500:
                comps.append((x0, y0, x1 + 1, y1 + 1))
    rows = {}
    for c in comps:
        rows.setdefault(round(c[3] / (h / 3)), []).append(c)
    return [sorted(r, key=lambda c: c[0]) for _, r in sorted(rows.items())]


def shrink(im, box, scale):
    """칸을 잘라 줄인다 (scale 은 숫자 하나 또는 (가로, 세로) 배율): 칸마다 배경이 아닌 픽셀이 절반 이상이면 칠한다."""
    sx, sy = scale if isinstance(scale, tuple) else (scale, scale)
    cell = im.crop(box)
    cw, ch = cell.size
    tw, th = max(1, round(cw * sx)), max(1, round(ch * sy))
    out = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    cp, op = cell.load(), out.load()
    for ty in range(th):
        for tx in range(tw):
            x0, x1 = int(tx / sx), max(int(tx / sx) + 1, int((tx + 1) / sx))
            y0, y1 = int(ty / sy), max(int(ty / sy) + 1, int((ty + 1) / sy))
            fg = [cp[x, y] for y in range(y0, min(y1, ch)) for x in range(x0, min(x1, cw)) if not is_bg(cp[x, y])]
            total = (min(x1, cw) - x0) * (min(y1, ch) - y0)
            if fg and len(fg) * 2 >= total:
                dark = [c for c in fg if sum(c[:3]) < DARK_SUM]
                if len(dark) >= len(fg) * OUTLINE_SHARE:
                    # 외곽선 가중: 원본의 얇은 외곽선이 줄이면서 사라지지 않게, 어두운 픽셀이 일정 비율이면 외곽선 색
                    mean = tuple(sum(c[i] for c in dark) // len(dark) for i in range(3))
                    op[tx, ty] = snap(mean) + (255,)
                    continue
                # 나머지는 가장 흔한 팔레트 색 (평균을 내면 색이 뭉개짐)
                counts = {}
                for c in fg:
                    s = snap(c[:3])
                    counts[s] = counts.get(s, 0) + 1
                op[tx, ty] = max(counts, key=counts.get) + (255,)
    return out


DARK_SUM = 110        # 이보다 어두우면 원본의 외곽선·그림자 픽셀
OUTLINE_SHARE = float(os.environ.get('ATTACK_OUTLINE_SHARE', 0.6))  # 줄이는 칸에서 외곽선 픽셀이 이 비율 이상이면 외곽선으로 칠함
BORDER_OUTLINE = os.environ.get('ATTACK_BORDER_OUTLINE', '0') == '1'  # 실루엣 둘레를 모두 외곽선 색으로
OUTLINE_COLOR = (0x12, 0x0C, 0x11, 255)  # Idle 외곽선 색


def clean_body(img):
    """Idle 처럼 보이게 다듬는다: 실루엣 둘레를 외곽선으로 잇고, 주변과 다른 외톨이 픽셀을 주변 색으로 바꾼다. 칼날 제외."""
    src = img.copy().load()
    p = img.load()
    on = lambda x, y: 0 <= x < W and 0 <= y < H and src[x, y][3]
    for y in range(H):
        for x in range(W):
            c = src[x, y]
            if not c[3] or is_blade(c):
                continue
            nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if any(not on(*q) for q in nb):
                if BORDER_OUTLINE and sum(c[:3]) >= DARK_SUM:
                    p[x, y] = OUTLINE_COLOR
                continue
            cols = [src[q] for q in nb]
            if all(q != c for q in cols):
                best = max(set(cols), key=cols.count)
                if cols.count(best) >= 3 and not is_blade(best):
                    p[x, y] = best
    return img


def back_foot_x(img):
    """가장 아래 부츠 줄과 뒷발(가장 왼쪽 부츠) x. 칼날(밝은 색)은 발로 치지 않는다."""
    p = img.load()
    boot = lambda c: c[3] and sum(c[:3]) < 400
    bottom = max(y for y in range(img.height) for x in range(img.width) if boot(p[x, y]))
    xs = [x for y in range(bottom - 2, bottom + 1) for x in range(img.width) if boot(p[x, y])]
    return min(xs), bottom


IDLE_HEAD = Image.open(os.path.join(ROOT, 'assets/images/player/idle/side.png')).convert('RGBA').crop((0, 0, 32, 21))
HEAD_PTS = [(x, y) for y in range(21) for x in range(32) if IDLE_HEAD.getpixel((x, y))[3]]


def fit_head(frame):
    """Idle 머리(후드·얼굴)를 놓을 위치: 머리 실루엣이 프레임의 몸(칼날 제외)과 가장 많이 겹치는 곳."""
    p = frame.load()
    body = lambda x, y: 0 <= x < W and 0 <= y < H and p[x, y][3] and not is_blade(p[x, y])
    top = min(y for y in range(H) for x in range(W) if body(x, y))
    best = None
    # 머리 꼭대기(HEAD_PTS 는 2줄부터)를 몸 꼭대기 근처에 둔다. 너무 아래에 놓이면 원래 후드 윗부분이 남는다
    for oy in range(max(0, top - 5), top + 1):
        for ox in range(0, W - 31):
            s = sum(1 if body(ox + x, oy + y) else -2 for x, y in HEAD_PTS)
            if best is None or s > best[0]:
                best = (s, ox, oy)
    return best[1], best[2]


def with_idle_head(frame):
    """프레임의 머리를 Idle 머리로 바꾼다: 머리 자리(조금 넓게)의 원래 픽셀을 지우고 Idle 머리를 붙인다. 칼날은 위에 남긴다."""
    ox, oy = fit_head(frame)
    out = frame.copy()
    p = out.load()
    src = frame.load()
    face_bottom = oy + 20
    near = {(ox + x + dx, oy + y + dy) for x, y in HEAD_PTS for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)}
    # 칼날과 그 가까이(손잡이·주먹)는 지우지 않는다. 단 머리 그림이 덮는 자리는 예외
    blade = [(x, y) for x in range(W) for y in range(H) if src[x, y][3] and is_blade(src[x, y])]
    keep = {(x + dx, y + dy) for x, y in blade for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)}
    head_cover = {(ox + x, oy + y) for x, y in HEAD_PTS}
    for x, y in near:
        if 0 <= x < W and 0 <= y < H and y <= face_bottom and ((x, y) not in keep or (x, y) in head_cover):
            p[x, y] = (0, 0, 0, 0)
    out.alpha_composite(IDLE_HEAD, (ox, oy))
    for x, y in near:  # 머리 앞을 지나는 칼날은 위로
        if 0 <= x < W and 0 <= y < H and src[x, y][3] and is_blade(src[x, y]):
            p[x, y] = src[x, y]
    remove_specks(out)
    return out


def remove_specks(img, max_size=60):
    """몸에서 떨어진 조각(원래 후드가 조금 더 커서 남은 가장자리 등)을 지운다.

    가장 큰 덩어리(몸)와 칼날이 들어 있는 덩어리는 남기고, 나머지 max_size 픽셀 미만 조각은 지운다.
    """
    p = img.load()
    seen = set()
    groups = []
    for sy in range(H):
        for sx in range(W):
            if (sx, sy) in seen or not p[sx, sy][3]:
                continue
            group, stack = [], [(sx, sy)]
            seen.add((sx, sy))
            while stack:
                x, y = stack.pop()
                group.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (x + dx, y + dy)
                        if 0 <= q[0] < W and 0 <= q[1] < H and q not in seen and p[q][3]:
                            seen.add(q)
                            stack.append(q)
            groups.append(group)
    if not groups:
        return
    body = max(groups, key=len)
    for group in groups:
        if group is body or len(group) >= max_size or any(is_blade(p[q]) for q in group):
            continue
        for q in group:
            p[q] = (0, 0, 0, 0)


def build():
    im = Image.open(SRC).convert('RGB')
    rows = find_cells(im)
    assert len(rows) == 3 and all(len(r) == 5 for r in rows), [len(r) for r in rows]
    sheets = []
    # 세 행 모두 같은 배율: 행마다 따로 맞추면 원본의 작은 크기 차이 때문에 타마다 몸 굵기가 달라진다.
    # 원본(ChatGPT) 캐릭터는 Idle 보다 통통해서, 키 기준 배율에 가로·세로 보정(SCALE_X, SCALE_Y)을 곱한다.
    base = sum(IDLE_HEIGHT / (r[-1][3] - r[-1][1]) for r in rows) / len(rows)
    scale = (base * SCALE_X, base * SCALE_Y)
    for row in rows:
        frames = [shrink(im, box, scale) for box in row]
        frames_out = []
        for f in frames[:-1]:
            fx, fb = back_foot_x(f)
            ox = STAND_BACK_FOOT_X - fx
            oy = FOOT_ROW - fb
            c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            c.alpha_composite(f, (max(0, ox), max(0, oy))) if ox >= 0 and oy >= 0 else c.paste(f, (ox, oy), f)
            # Idle·Walk 처럼 모든 프레임이 같은 머리 그림을 쓰도록 Idle 머리로 바꾼다
            frames_out.append(with_idle_head(clean_body(c)))
        # 복귀(마지막) 프레임은 Idle 로 돌아갈 때 튀지 않도록 게임 기준 그림(Idle 측면 + 원본 검)을 그대로 쓴다
        recover = Image.open(os.path.join(ROOT, 'assets/concepts/pixellab/kit/ref_side_right_sword_96x64.png')).convert('RGBA')
        frames_out.append(recover)
        sheets.append(frames_out)
    os.makedirs(OUT, exist_ok=True)
    for n, frames in enumerate(sheets, start=1):
        s = Image.new('RGBA', (W * 5, H), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            s.alpha_composite(f, (W * i, 0))
        s.save(os.path.join(OUT, f'side_{n}.png'))
    idle = Image.open(os.path.join(ROOT, 'assets/images/player/idle/side.png')).convert('RGBA').crop((0, 0, 32, 48))
    view = Image.new('RGBA', ((W + 4) * 6, (H + 4) * 3), (90, 110, 90, 255))
    for r, frames in enumerate(sheets):
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        c.alpha_composite(idle, (32, 8))
        view.alpha_composite(c, (0, r * (H + 4)))
        for i, f in enumerate(frames):
            view.alpha_composite(f, ((i + 1) * (W + 4), r * (H + 4)))
    view.resize((view.width * 3, view.height * 3), Image.NEAREST).save(os.path.join(OUT, 'cells_x3.png'))


if __name__ == '__main__':
    build()
