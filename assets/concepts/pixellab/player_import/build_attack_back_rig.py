"""후면 1타 시험판: 다시 그리지 않고 게임 뒷모습 서기 그림을 움직여 만든다 (2026-11-19 사용자 요청).

AI 가 장마다 새로 그리면 픽셀이 장마다 달라 꿈틀거리고(보일링) 장 사이가 튀어 버벅거렸다.
뒷모습은 망토가 몸을 덮어 동작 대부분을 칼·잔상이 보여 주므로, 몸은 서기 그림(idle/back.png 첫 장)의 픽셀을
그대로 두고 몇 픽셀만 옮긴다: 기울이기(윗몸 줄을 조금씩 옆으로), 낮추기·높이기(다리·허리 줄을 빼거나 한 번 더),
망토 밑단 흔들기. 칼은 게임처럼 따로 그리며 16장으로 이어 돌리고, 칼을 든 두 팔·장갑만 몇 픽셀 그린다.

출력 (시험판, 아직 게임에 넣지 않음): attack_back_kit/rig/back_1_rig.png (96×64 16장), back_1_rig_hand.png,
비교 미리보기 rig_vs_now.gif / rig_vs_now_slow.gif / rig_frames_x4.png, 칼 표는 RIG 에서 바로 읽는다.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from game import config  # noqa: E402

PLAYER = os.path.join(ROOT, 'assets', 'images', 'player')
OUT = os.path.join(HERE, 'attack_back_kit', 'rig')
W, H = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT  # 96 × 64
BODY_X, BODY_Y = (W - 32) // 2, H - config.PLAYER_ATTACK_FOOT_MARGIN - 48  # 서기 그림(32×48)을 놓는 자리
SHOULDER_R, SHOULDER_L = (54, 30), (42, 30)  # 캔버스 좌표 (화면 오른쪽 = 몸의 오른쪽, 뒤에서 봄)
OUTLINE, SLEEVE, GLOVE = (20, 14, 20), (60, 37, 43), (36, 23, 29)

# 장마다: (끝 진행도, 손 x, 손 y, 칼 각도, 칼이 몸 뒤, 칼 길이, 기울기, 높이(+ 위), 밑단, 팔 보임)
# 오른쪽 어깨에서 칼을 꺼내 → 오른쪽 위 → 머리 위 → 왼쪽 위(멈칫) → 0.5 에 왼쪽 위에서 오른쪽 아래로 벰 → 낮게 마무리
RIG = [
    (0.06, 56, 24, 118, False, 1.0, 0, 0, 0, False),   # 등의 칼을 오른손으로 잡음
    (0.12, 58, 20, 104, False, 1.0, 1, 0, 0, True),    # 뽑아 올림
    (0.18, 59, 16, 90, False, 1.0, 1, 0, -1, True),
    (0.24, 57, 12, 78, False, 1.0, 1, 1, -1, True),    # 오른쪽 위
    (0.30, 52, 9, 84, True, 1.0, 0, 1, 0, True),       # 머리 위로 넘김
    (0.36, 45, 9, 102, True, 1.0, -1, 1, 1, True),
    (0.42, 39, 12, 122, True, 1.0, -1, 1, 1, True),    # 왼쪽 위
    (0.50, 38, 13, 130, True, 1.0, -2, 1, 1, True),    # 멈칫 (힘 모음)
    (0.60, 48, 30, -40, True, 0.0, 2, -2, -2, False),  # 벰: 잔상, 칼은 몸 너머
    (0.66, 58, 40, -34, True, 1.0, 2, -2, -2, False),  # 오른쪽 아래로 빠져나옴
    (0.72, 58, 41, -32, True, 1.0, 2, -2, -1, False),
    (0.78, 58, 41, -31, True, 1.0, 1, -2, -1, False),
    (0.84, 57, 41, -30, True, 1.0, 1, -1, 0, False),
    (0.90, 57, 41, -30, True, 1.0, 1, -1, 0, False),
    (0.95, 57, 40, -30, True, 1.0, 0, -1, 0, False),
    (1.00, 57, 40, -30, True, 1.0, 0, 0, 0, False),
]
CUT = 8  # 잔상 장 (0 부터)


def lean(cell, k):
    """윗몸 기울이기: 다리(37줄 아래)는 그대로, 위로 갈수록 k 픽셀까지 옆으로."""
    out = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    for y in range(cell.height):
        s = 0 if y >= 37 else round(k * (37 - y) / 35)
        out.alpha_composite(cell.crop((0, y, cell.width, y + 1)), (s, y))
    return out


def height(cell, n):
    """n > 0: 허리(30줄)를 n 줄 늘려 몸을 높임, n < 0: 무릎(42줄) 줄을 빼 낮춤. 발은 제자리."""
    out = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    rows = [cell.crop((0, y, cell.width, y + 1)) for y in range(cell.height)]
    if n > 0:
        rows = rows[:30] + [rows[30]] * n + rows[30:]
    elif n < 0:
        rows = rows[:42 + n] + rows[42:]
    top = cell.height - len(rows)
    for i, r in enumerate(rows):
        if 0 <= top + i < cell.height:
            out.alpha_composite(r, (0, top + i))
    return out


def hem(cell, k):
    """망토 밑단(31~38줄) 흔들기: 아래로 갈수록 k 픽셀까지 옆으로."""
    out = cell.copy()
    out.paste((0, 0, 0, 0), (0, 31, cell.width, 39))
    for y in range(31, 39):
        out.alpha_composite(cell.crop((0, y, cell.width, y + 1)), (round(k * (y - 30) / 8), y))
    return out


def body_frame(idle, tilt, up, flap):
    cell = height(idle, up)
    cell = hem(lean(cell, tilt), flap)
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(cell, (BODY_X, BODY_Y))
    return canvas


def arms(hx, hy, angle):
    """칼을 쥔 두 팔: 어깨에서 손까지 굵기 3 의 소매(테두리 + 안), 끝에 장갑. 왼손은 손잡이 끝 쪽(손 뒤 3픽셀)."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ux, uy = math.cos(math.radians(angle)), -math.sin(math.radians(angle))
    left_hand = (hx - 3 * ux, hy - 3 * uy)
    for shoulder, hand in ((SHOULDER_L, left_hand), (SHOULDER_R, (hx, hy))):
        d.line([shoulder, hand], fill=OUTLINE + (255,), width=4)
        d.line([shoulder, hand], fill=SLEEVE + (255,), width=2)
    for hand in (left_hand, (hx, hy)):
        x, y = round(hand[0]), round(hand[1])
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=OUTLINE + (255,))
        layer.putpixel((x, y), GLOVE + (255,))
    return layer


def swoosh_layer():
    """벨 때 잔상: 왼쪽 위에서 오른쪽 아래로 (몸 뒤, 흰 반투명). 가운데가 가장 두껍다."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = layer.load()
    # 확인받은 1타 잔상과 같은 초승달 (68 칸 중심 (22,20) 반지름 36, -20~112°, 좌우 뒤집음) 을 캔버스 좌표로
    cx, cy, r, a0, a1, thick = 67 - 22 + 14, 20 - 3, 36, 180 - 112, 180 + 20, 8
    for i in range(301):
        t = i / 300
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * math.sin(math.pi * t) ** 0.7
        for k in range(int(w * 4) + 1):
            rr = r - k / 4
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            if 0 <= x < W and 0 <= y < H:
                px[int(x), int(y)] = (235, 242, 255, 200)
    return layer


def build():
    idle = Image.open(os.path.join(PLAYER, 'idle', 'back.png')).convert('RGBA').crop((0, 0, 32, 48))
    n = len(RIG)
    body = Image.new('RGBA', (W * n, H), (0, 0, 0, 0))
    hand = Image.new('RGBA', (W * n, H), (0, 0, 0, 0))
    for i, (_, hx, hy, ang, behind, length, tilt, up, flap, show_arms) in enumerate(RIG):
        frame = body_frame(idle, tilt, up, flap)
        if show_arms:
            under = arms(hx, hy, ang)  # 팔은 몸 뒤: 후드·망토 밖으로 나온 부분(장갑·팔뚝)만 보인다
            under.alpha_composite(frame)
            frame = under
        if i == CUT:
            arc = swoosh_layer()
            arc.alpha_composite(frame)
            frame = arc
        body.alpha_composite(frame, (i * W, 0))
    os.makedirs(OUT, exist_ok=True)
    body.save(os.path.join(OUT, 'back_1_rig.png'))
    hand.save(os.path.join(OUT, 'back_1_rig_hand.png'))
    return body, hand


# --- 미리보기: 게임 그리기와 같은 순서(칼이 몸 뒤면 칼 → 몸 → 손, 앞이면 몸 → 칼 → 손), 2배 ---
SWORD = Image.open(os.path.join(PLAYER, 'weapons', f'{config.PLAYER_WEAPON}.png')).convert('RGBA')
S = config.RENDER_SCALE


def draw_sword(canvas, hx, hy, angle, length):
    if length <= 0:
        return
    sw = SWORD.resize((round(SWORD.width * length) * S, SWORD.height * S), Image.NEAREST)
    rot = sw.rotate(angle, resample=Image.NEAREST, expand=True)
    cx, cy = (hx + 0.5) * S, (hy + 0.5) * S
    canvas.alpha_composite(rot, (round(cx - rot.width / 2), round(cy - rot.height / 2)))


PAD = 24  # 미리보기 위쪽 여백 (원본 픽셀)


def compose(body, hand, frame, sword):
    hx, hy, angle, behind, *rest = sword
    length = rest[0] if rest else 1.0
    b = body.crop((frame * W, 0, (frame + 1) * W, H)).resize((W * S, H * S), Image.NEAREST)
    hd = hand.crop((frame * W, 0, (frame + 1) * W, H)).resize((W * S, H * S), Image.NEAREST)
    out = Image.new('RGBA', (W * S, (H + PAD) * S), (0, 0, 0, 0))
    o = (0, PAD * S)
    if not behind:
        out.alpha_composite(b, o)
    draw_sword(out, hx, hy + PAD, angle, length)
    if behind:
        out.alpha_composite(b, o)
    out.alpha_composite(hd, o)
    return out


def frame_at(progress, ends):
    for i, e in enumerate(ends):
        if progress < e:
            return i
    return len(ends) - 1


def preview(body, hand):
    now_body = Image.open(os.path.join(PLAYER, 'sword_attack', 'back_1.png')).convert('RGBA')
    now_hand = Image.open(os.path.join(PLAYER, 'sword_attack', 'back_1_hand.png')).convert('RGBA')
    now_ends = config.PLAYER_ATTACK_FRAME_ENDS_BACK[0]
    now_table = config.PLAYER_ATTACK_SWORD_BACK[0]
    rig_ends = [r[0] for r in RIG]
    rig_table = [r[1:6] for r in RIG]
    dur = config.PLAYER_ATTACK_DURATIONS[0]
    frames = []
    steps = round(dur * 60)
    for k in range(steps + 20):  # 끝에서 잠깐 멈춤
        p = min(k / steps, 0.999)
        img = Image.new('RGBA', (W * S * 2 + 20, (H + PAD) * S + 24), (40, 38, 52, 255))
        d = ImageDraw.Draw(img)
        d.text((8, 4), 'now', fill=(220, 220, 220))
        d.text((W * S + 28, 4), 'rig (new)', fill=(220, 220, 220))
        f = frame_at(p, now_ends)
        img.alpha_composite(compose(now_body, now_hand, f, now_table[f]), (0, 24))
        f = frame_at(p, rig_ends)
        img.alpha_composite(compose(body, hand, f, rig_table[f]), (W * S + 20, 24))
        frames.append(img.convert('P', palette=Image.ADAPTIVE))
    frames[0].save(os.path.join(OUT, 'rig_vs_now.gif'), save_all=True, append_images=frames[1:], duration=17, loop=0)
    frames[0].save(os.path.join(OUT, 'rig_vs_now_slow.gif'), save_all=True, append_images=frames[1:], duration=70,
                   loop=0)
    strip = Image.new('RGBA', (W * S * 8, (H + PAD) * S * 2), (40, 38, 52, 255))
    for i in range(len(RIG)):
        strip.alpha_composite(compose(body, hand, i, rig_table[i]), ((i % 8) * W * S, (i // 8) * (H + PAD) * S))
    strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST).save(os.path.join(OUT, 'rig_frames_x4.png'))


if __name__ == '__main__':
    b, h = build()
    preview(b, h)
    print('ok', len(RIG))
