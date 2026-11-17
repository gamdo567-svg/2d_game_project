"""후면 2타 합성 미리보기 (2026-11-17, 사용자 결정: PixelLab 이 후면에서 칼을 휘두르면 몸을 돌려서
몸은 PixelLab 후면 그림, 칼은 게임처럼 칼 그림 한 장을 손 위치·각도대로 그린다).

- 칼 궤적: 정면 2타(v7)에서 읽은 손 위치·각도를 좌우로 뒤집는다 (뒤에서 보면 좌우가 반대).
- 몸: 후면 점프(v14) 의 웅크림·도약 그림과 서 있는 후면 그림 (모두 등을 보임).
- 칼이 몸 앞쪽 아래에 있을 때는 몸 뒤에, 어깨 위로 넘어온 뒤에는 몸 위에 그린다.
사용: 저장소 루트에서 `python assets/concepts/pixellab/player_import/build_back2_composite.py`
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_remake_preview as b  # noqa: E402

CELL = 68
# 정면 v7 2타 칼 (68 칸 기준, 발 아래 가운데 = (34, 66)). 4·5번은 잔상에 묻혀 사이 값.
# 4·5번(잔상에 묻힌 순간)은 뒤에서 볼 때 칼이 몸 앞을 지나 위로 올라가도록 (뒤집기 전 값으로) 오른쪽 → 위를 거친다.
FRONT_SWORD = [
    (23, 49, -146), (23, 50, -148), (25, 50, -147),
    (28, 46, 160), (32, 38, 90),
    (43, 41, 47), (43, 41, 47), (43, 41, 47),
]
BEHIND = [True, True, True, True, True, False, False, False]
# 몸 그림: (시트, 행, 칸)
JUMP_BACK = ('jump_v14_side_back_sheet_68.png', 1)
IDLE_BACK = ('attack_front_back_sheet_68.png', 4, 0)
# 다리는 거의 움직이지 않게 (2026-11-17 사용자): 살짝 웅크렸다가 일어선다
BODY = [
    JUMP_BACK + (1,), JUMP_BACK + (1,), JUMP_BACK + (1,),
    IDLE_BACK, IDLE_BACK,
    IDLE_BACK, IDLE_BACK, IDLE_BACK,
]


def cell(sheet, row, col):
    im = Image.open(os.path.join(b.RAW, sheet)).convert('RGBA')
    return im.crop((col * CELL, row * CELL, (col + 1) * CELL, (row + 1) * CELL))


def foot_row(frame):
    return frame.getchannel('A').getbbox()[3] - 1


def frames():
    idle = cell(*IDLE_BACK)
    ground = foot_row(idle)  # 서 있는 후면 그림의 발 줄
    dy = ground - 66  # 정면 칼 좌표(발 = 66) → 후면 그림 좌표
    out = []
    for i, ((hx, hy, angle), behind, body_src) in enumerate(zip(FRONT_SWORD, BEHIND, BODY)):
        body = cell(*body_src)
        # 몸이 땅에 붙게 (도약 그림은 발끝만 살짝 든 까치발처럼 보이도록 그대로)
        x = CELL - hx  # 좌우 뒤집기
        y = hy + dy
        a = 180 - angle
        canvas = Image.new('RGBA', (CELL + 2 * b.PAD, CELL), (0, 0, 0, 0))
        if behind:
            b.paste_sword(canvas, x + b.PAD, y, a)
        canvas.alpha_composite(body, (b.PAD, 0))
        if not behind:
            b.paste_sword(canvas, x + b.PAD, y, a)
        out.append(canvas)
    return out


def main():
    bg = (32, 30, 40, 255)
    S = 3
    fr = frames()
    idle = Image.new('RGBA', fr[0].size, (0, 0, 0, 0))
    idle.alpha_composite(cell(*IDLE_BACK), (b.PAD, 0))
    seq = [idle, idle] + fr + [idle, idle]
    gif = []
    for f in seq:
        g = Image.new('RGBA', f.size, bg)
        g.alpha_composite(f)
        gif.append(g.resize((f.width * S, f.height * S), Image.NEAREST).convert('RGB')
                   .quantize(colors=256, dither=Image.Dither.NONE))
    out = os.path.join(b.OUT, 'attack2_back_composite')
    gif[0].save(out + '_slow.gif', save_all=True, append_images=gif[1:], duration=250, loop=0)
    gif[0].save(out + '.gif', save_all=True, append_images=gif[1:], duration=84, loop=0)
    sheet = Image.new('RGBA', (fr[0].width * S * 8, CELL * S), bg)
    for i, f in enumerate(fr):
        g = Image.new('RGBA', f.size, bg)
        g.alpha_composite(f)
        sheet.paste(g.resize((f.width * S, f.height * S), Image.NEAREST), (i * f.width * S, 0))
    sheet.save(out + '_sheet.png')
    print('ok')


if __name__ == '__main__':
    main()
