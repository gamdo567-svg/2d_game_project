"""정면(아래를 볼 때) 공격 자세 안내 그림: ChatGPT 에 "이 안내대로 캐릭터를 입혀 줘"라고 보낼 그림.

3행 × 5열, 초록 배경. 칸마다 막대 인형(몸 방향·발 위치)과 파란 칼(위치·각도)을 그린다.
탑다운 게임의 아래 방향 공격: 칼이 몸 앞(화면 아래쪽 칸)을 가로로 휩쓸고, 3타는 아래로 찌른다.
정면이므로 캐릭터의 오른손·오른쪽 어깨는 보는 사람 기준 왼쪽에 있다.
사용: 저장소 루트에서 `python assets/concepts/front_pose_guide.py` → assets/concepts/attack_front_pose_guide.png
"""
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'concepts', 'attack_front_pose_guide.png')
CW, CH = 280, 380  # 칸 크기
DY = 40  # 칸 위쪽 여백 (머리 위로 든 칼이 들어갈 자리)
FOOT_Y = 250  # 발바닥 높이 (칸 안). 아래 칸을 찌르는 칼이 들어갈 자리를 남긴다
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BODY = (70, 45, 40)
HEAD = (110, 70, 60)
BLADE_LEN, GRIP_LEN, GUARD = 125, 30, 18

# 칸별 자세: (머리 x, 머리 y, 엉덩이 y, 왼발 x(보는 사람 기준), 오른발 x, 손 x, 손 y, 칼 각도(도, 오른쪽 0 / 위 90))
# 손 = 캐릭터 오른손(가드 바로 아래), 왼손은 손잡이 뒤쪽에 자동으로 붙인다.
POSES = [
    [  # 1타: 몸 앞(아래 칸)을 보는 사람 기준 왼쪽 → 오른쪽으로 가로질러 휩쓸기
        (128, 72, 178, 70, 190, 72, 140, 115),    # ① 칼을 캐릭터 오른쪽 어깨 위로, 상체를 오른쪽으로 비틂
        (122, 80, 186, 55, 200, 52, 130, 165),    # ② 더 크게 당김: 칼이 거의 수평으로 뒤, 다리를 넓게
        (140, 92, 196, 60, 210, 128, 205, -100),  # ③ 휩쓸기 한가운데: 몸을 낮추며 칼이 발 앞을 지남
        (150, 88, 192, 75, 220, 200, 188, -20),   # ④ 마무리: 칼이 보는 사람 기준 오른쪽으로 끝까지, 상체가 오른쪽으로 비틀림
        (130, 70, 176, 100, 160, 92, 168, -100),  # ⑤ 복귀: 바로 서서 칼을 오른쪽 옆에 내림
    ],
    [  # 2타: 반대로 오른쪽 아래 → 앞 → 왼쪽 위로 올려 휩쓸기
        (140, 92, 198, 60, 215, 195, 205, -45),   # ① 낮게 웅크리고 칼을 보는 사람 기준 오른쪽 아래로
        (132, 86, 192, 60, 205, 130, 210, -130),  # ② 휩쓸기 한가운데: 칼이 발 앞을 지나 왼쪽으로
        (120, 72, 180, 70, 195, 70, 125, 140),    # ③ 몸을 펴며 칼을 왼쪽 위로 크게 올려침
        (118, 66, 176, 85, 180, 90, 100, 115),    # ④ 발끝으로 서서 칼을 머리 왼쪽 위로 높이
        (130, 70, 176, 100, 160, 92, 168, -100),  # ⑤ 복귀
    ],
    [  # 3타: 허리로 당겼다가 화면 아래쪽(아래 칸)으로 길게 찌르기
        (122, 68, 176, 80, 175, 85, 150, -95),    # ① 칼을 오른쪽 허리 옆으로 당기고 상체를 뒤로 젖힘
        (120, 86, 194, 70, 190, 82, 172, -95),    # ② 더 낮게 웅크려 힘을 모음
        (132, 96, 200, 80, 190, 128, 200, -90),   # ③ 한 발 앞으로 내딛고 상체를 숙이며 두 팔을 아래로 쭉 뻗어 찌름
        (134, 104, 204, 75, 195, 130, 208, -90),  # ④ 더 깊게 숙여 앞으로 쏠림
        (130, 70, 176, 100, 160, 92, 168, -100),  # ⑤ 복귀
    ],
]


def line(d, a, b, w, col):
    d.line([a, b], fill=col, width=w)
    r = w / 2
    for p in (a, b):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def sword(d, hx, hy, deg):
    a = math.radians(deg)
    ux, uy = math.cos(a), -math.sin(a)
    px, py = -uy, ux
    tip = (hx + ux * (BLADE_LEN + 8), hy + uy * (BLADE_LEN + 8))
    guard = (hx + ux * 8, hy + uy * 8)
    pommel = (hx - ux * GRIP_LEN, hy - uy * GRIP_LEN)
    line(d, pommel, guard, 9, BLUE)  # 손잡이
    line(d, (guard[0] - px * GUARD, guard[1] - py * GUARD), (guard[0] + px * GUARD, guard[1] + py * GUARD), 9, BLUE)
    blade_w = 7
    d.polygon([(guard[0] + px * blade_w, guard[1] + py * blade_w), (guard[0] - px * blade_w, guard[1] - py * blade_w),
               (tip[0] - ux * 14 - px * blade_w, tip[1] - uy * 14 - py * blade_w), tip,
               (tip[0] - ux * 14 + px * blade_w, tip[1] - uy * 14 + py * blade_w)], fill=BLUE)
    return pommel


def figure(d, ox, oy, pose):
    hx, hy, hip_y, lfx, rfx, gx, gy, deg = pose
    neck = (hx, hy + 42)
    hip = (hx, hip_y)
    # 다리·발 (보는 사람 기준 왼발, 오른발)
    for fx in (lfx, rfx):
        knee = ((hip[0] + fx) / 2, (hip_y + FOOT_Y) / 2 - 6)
        line(d, (ox + hip[0], oy + hip[1]), (ox + knee[0], oy + knee[1]), 16, BODY)
        line(d, (ox + knee[0], oy + knee[1]), (ox + fx, oy + FOOT_Y - 6), 16, BODY)
        d.rectangle([ox + fx - 14, oy + FOOT_Y - 12, ox + fx + 14, oy + FOOT_Y], fill=BODY)
    # 몸통·망토 (어깨 넓이)
    shoulder_r = (neck[0] - 30, neck[1] + 10)  # 캐릭터 오른쪽 어깨 = 보는 사람 기준 왼쪽
    shoulder_l = (neck[0] + 30, neck[1] + 10)
    d.polygon([(ox + shoulder_r[0] - 8, oy + shoulder_r[1]), (ox + shoulder_l[0] + 8, oy + shoulder_l[1]),
               (ox + hip[0] + 26, oy + hip[1]), (ox + hip[0] - 26, oy + hip[1])], fill=BODY)
    # 칼 (손 = 오른손, 가드 바로 아래)과 팔
    a = math.radians(deg)
    ux, uy = math.cos(a), -math.sin(a)
    right_hand = (gx, gy)
    left_hand = (gx - ux * 20, gy - uy * 20)
    line(d, (ox + shoulder_l[0], oy + shoulder_l[1]), (ox + left_hand[0], oy + left_hand[1]), 13, BODY)
    sword(d, ox + gx, oy + gy, deg)
    line(d, (ox + shoulder_r[0], oy + shoulder_r[1]), (ox + right_hand[0], oy + right_hand[1]), 13, BODY)
    for p in (left_hand, right_hand):
        d.ellipse([ox + p[0] - 9, oy + p[1] - 9, ox + p[0] + 9, oy + p[1] + 9], fill=(60, 35, 30))
    # 머리(후드)는 맨 위에, 크고 둥글게 (SD 비율)
    d.ellipse([ox + hx - 46, oy + hy - 46, ox + hx + 46, oy + hy + 46], fill=HEAD)
    d.ellipse([ox + hx - 26, oy + hy - 10, ox + hx + 26, oy + hy + 30], fill=(20, 12, 14))  # 얼굴 그림자


def main():
    img = Image.new('RGB', (CW * 5, CH * 3), GREEN)
    d = ImageDraw.Draw(img)
    for r, row in enumerate(POSES):
        for c, pose in enumerate(row):
            figure(d, c * CW, r * CH + DY, pose)
    img.save(OUT)
    print(OUT, img.size)


if __name__ == '__main__':
    main()
