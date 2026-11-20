"""PixelLab 으로 새로 만든 주인공 공격 그림에서 파란 칼을 떼어 내고, 칼 그림 한 장을 손에 끼워 미리보기를 만든다.

- 파란 픽셀(b - r > 30)을 칼 후보로 본다. 연결된 덩어리 중 가늘고 긴 것이 칼, 나머지(넓은 것)는 휘두른 잔상이다.
- 칼의 축(주성분)을 구하고, 몸 쪽 끝 근처에서 가장 넓은 곳을 가드로 본다. 손은 가드에서 손잡이 쪽으로 2픽셀.
  각도는 칼끝 방향 (오른쪽 0도, 반시계 +), 게임의 PLAYER_ATTACK_SWORD 와 같은 규칙.
- 칼이 잔상에 묻혀 찾지 못한 프레임은 앞뒤 프레임 값으로 이어 준다.
- 몸: 파란 픽셀을 지우고 몸 안쪽 구멍은 주변 색으로 메운다. 손 둘레 픽셀은 칼 위에 다시 그려 칼을 쥔 모습으로.
- 잔상: 흰색 반투명으로 바꾼다.
Pillow 필요 (게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/pixellab/player_import/build_remake_preview.py`
"""
import json
import math
import os
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
RAW = os.path.join(HERE, 'remake_raw')
OUT = os.path.join(HERE, 'remake_preview')
CELL = 68
SWORD = Image.open(os.path.join(ROOT, 'assets/images/player/weapons/old_sword.png')).convert('RGBA')
BG = (32, 30, 40, 255)
HAND_RADIUS = 3

# (시트 파일, 행) : 고른 조합 = 1타 첫 시도, 2타, 3타 v2
ATTACKS = [
    ('attack1', 'attack_side_sheet_68.png', 0),  # 1타 첫 시도 (3·4번만 v3 로 바꿔 끼움, FRAME_SOURCE)
    ('attack2', 'attack_side_sheet_68.png', 1),
    ('attack3', 'attack3_side_v2_sheet_68.png', 0),
]
# 한 타 시간: 지금 게임 값(0.45, 0.45, 0.6)의 1.5배 (2026-11-17 사용자 요청: 1.75배는 너무 느려 1.5배로).
# 3타는 그보다 1.2배 빠르게 0.9 → 0.75초 (2026-11-17 사용자 요청: 3타가 너무 느림)
DURATIONS = {'attack1': 0.675, 'attack2': 0.675, 'attack3': 0.75}
PAD = 16  # 칼끝이 68 칸 밖으로 나가도 잘리지 않게 좌우 여백

# 칼이 잔상에 묻히거나 머리 뒤로 가려져 자동으로 찾지 못하는 프레임: 원본을 확대해 직접 읽은 값.
# (공격, 프레임 1~8) : (손 x, 손 y, 각도, 몸 뒤에 그리기). 좌표는 68×68 칸 기준, y 는 아래로.
OVERRIDES = {
    ('attack1', 5): (55, 48, -40, False),  # 몸을 7번 그림으로 쓰므로 손도 7번 자리 (각도만 더 숙임)
    ('attack1', 6): (55, 48, -33, False),
    # 정면·후면 (2026-11-17): 칼이 잔상에 묻히거나 보는 사람 쪽으로 향해 자동으로 못 찾은 프레임
    ('front1', 3): (47, 34, 117, True), ('front1', 5): (50, 40, -40, False),
    ('front1', 6): (36, 43, -146, False), ('front1', 7): (25, 45, -138, False),
    # 정면 2타 = v9 (시작·끝 자세 지정, 2026-11-17 사용자 확정)
    ('front2', 4): (25, 46, -132, False), ('front2', 5): (44, 29, 62, False),
    ('front2', 6): (47, 28, 140, True), ('front2', 7): (49, 29, 142, True), ('front2', 8): (47, 29, 139, True),
    # 정면 3타 = 찌르기 끝 자세 지정 (2026-11-17 사용자 확정). 칼이 보는 사람 쪽으로 기울어 자동으로 못 찾음
    ('front3', 1): (25, 41, -129, False), ('front3', 2): (24, 37, -52, False),
    ('front3', 3): (24, 36, -55, False), ('front3', 4): (25, 36, -59, False),
    ('front3', 5): (26, 36, -61, False), ('front3', 6): (34, 35, -90, False),
    ('front3', 7): (34, 35, -90, False), ('front3', 8): (34, 35, -90, False),
    # 패링 측면 (2026-11-17): 1·5번째는 칼을 세워 머리 뒤로(칼끝만 후드 위로 보임), 2번째는 쳐올리는 잔상 속 칼
    ('parry_side', 1): (43, 31, 108, True), ('parry_side', 2): (46, 41, 60, False),
    ('parry_side', 5): (43, 31, 108, True),
    # 패링 정면 (2026-11-18, C안): 2번째는 쳐올리는 잔상 속 칼 (오른쪽 위로)
    ('parry_front', 2): (37, 41, 60, False),
    # 패링 후면 (2026-11-18, ChatGPT 핵심 자세): 두 손이 몸 앞이라 칼은 늘 몸 뒤(가려짐), 보이는 칼날 방향으로 맞춤.
    # 1·5 당김 = 칼을 세워 오른쪽 어깨 위로, 2 쳐올림 = 잔상 속 칼, 3·4 막기 = 왼쪽 위로 비스듬히
    ('parry_back', 1): (42, 39, 90, True), ('parry_back', 2): (36, 38, 105, True),
    ('parry_back', 3): (32, 38, 126, True), ('parry_back', 4): (32, 38, 126, True),
    ('parry_back', 5): (42, 39, 90, True),
    # 후면 공격 (2026-11-18, ChatGPT 8자세 attack_back_gpt_68.png): 칼은 늘 몸 뒤(가려짐). 보이는 칼날 끝에서 칼 길이(24)만큼
    # 몸 쪽이 손 (estimate_back_swords.py 로 어림 후 눈으로 맞춤). 칼이 안 보이는 장은 다섯째 값(칼 길이 비율) 0 = 그리지 않음.
    # 후면 1타 2차 (2026-11-18, PixelLab 이 GPT 자세 사이를 다시 그림 attack_back_pl_68.png). 4번째 = 잔상 장 (칼은 잔상 속).
    # 4차: PixelLab 이 1타 전체를 한 번에 이어 그림 (왼쪽 아래 → 왼쪽 위로 휘돌려 → 오른쪽 어깨 위 → 5번째 잔상 → 왼쪽 아래).
    # 7차: 앞 네 장은 칼을 왼쪽에 세운 자세에서 머리 위를 지나 오른쪽 위로 옮김 (정면처럼)
    ('backpl1', 1): (21, 36, 109, True), ('backpl1', 2): (24, 36, 109, True), ('backpl1', 3): (36, 36, 94, True),
    ('backpl1', 4): (47, 36, 75, True), ('backpl1', 5): (34, 30, -90, True, 0), ('backpl1', 6): (31, 40, -176, True),
    ('backpl1', 7): (29, 42, -163, True), ('backpl1', 8): (30, 43, -159, True),
    # 후면 1타 3차 (2026-11-18, ChatGPT 가 정면 8장을 뒤에서 본 모습으로 그림 attack_back_v2_68.png). 5번째 = 판정 잔상 장.
    # 3번째는 칼이 몸 앞으로 향해 오른쪽 허리에 짧게만 보여 칼 길이 0.4.
    # 좌우로 뒤집음 (사용자: 왼쪽으로 옮긴 뒤 왼쪽에서 오른쪽으로 벰): x → 67 - x, 각도 → 180 - 각도
    # 9차 (사용자: 예전처럼 오른쪽에서 꺼낸 다음 왼쪽으로 옮겨 벰): 1·2 오른쪽 어깨에서 꺼내 듦(뒤집지 않은 값),
    # 3·4 머리 위로 넘김(PixelLab 사이 장), 5 왼쪽 위, 6 판정 잔상, 7·8 오른쪽 아래 마무리
    ('backv2_1', 1): (41, 42, 42, True), ('backv2_1', 2): (41, 36, 63, True), ('backv2_1', 3): (40, 32, 79, True),
    ('backv2_1', 4): (31, 32, 86, True), ('backv2_1', 5): (24, 31, 111, True), ('backv2_1', 6): (33, 30, -90, True, 0),
    ('backv2_1', 7): (42, 46, -29, True), ('backv2_1', 8): (40, 46, -29, True),
    ('backgpt1', 1): (34, 30, -90, True, 0), ('backgpt1', 2): (28, 41, 41, True), ('backgpt1', 3): (32, 34, 50, True),
    ('backgpt1', 4): (34, 30, -90, True, 0), ('backgpt1', 5): (36, 43, -157, True), ('backgpt1', 6): (38, 37, -147, True),
    ('backgpt1', 7): (36, 28, -129, True), ('backgpt1', 8): (34, 30, -90, True, 0),
    ('backgpt2', 1): (34, 30, -90, True, 0), ('backgpt2', 2): (36, 39, -143, True), ('backgpt2', 3): (29, 46, -152, True),
    ('backgpt2', 4): (42, 34, 60, True), ('backgpt2', 5): (35, 27, 88, True), ('backgpt2', 6): (33, 31, 64, True),
    ('backgpt2', 7): (36, 37, 77, True), ('backgpt2', 8): (34, 30, -90, True, 0),
    ('backgpt3', 1): (34, 30, -90, True, 0), ('backgpt3', 2): (40, 40, 90, True), ('backgpt3', 3): (40, 40, 90, True),
    ('backgpt3', 4): (37, 30, 87, True), ('backgpt3', 5): (35, 26, 90, True), ('backgpt3', 6): (35, 26, 90, True),
    ('backgpt3', 7): (35, 32, 92, True), ('backgpt3', 8): (34, 30, -90, True, 0),
    # 후면 2·3타 2차 (2026-11-18, ChatGPT 가 좌우 뒤집은 정면 8장을 뒤에서 본 모습으로 그림 → 8장 함께 화풍 입힘,
    # attack_back_v3_68.png). 보이는 파란 칼날의 끝에서 칼 길이(24)만큼 몸 쪽이 손. 칼은 늘 몸 뒤.
    # 2타: 1~4 오른쪽 아래로 늘어뜨림 → 5 쳐올리는 잔상(칼 안 그림) → 6~8 왼쪽 어깨 위
    ('backv3_2', 1): (40, 42, -53, True), ('backv3_2', 2): (39, 44, -48, True), ('backv3_2', 3): (39, 46, -46, True),
    ('backv3_2', 4): (40, 44, -47, True), ('backv3_2', 5): (24, 32, 116, True, 0), ('backv3_2', 6): (25, 26, 135, True),
    ('backv3_2', 7): (24, 24, 138, True), ('backv3_2', 8): (25, 25, 136, True),
    # 3타: 1~5 오른쪽 허리로 당김 (칼끝만 보임) → 6~8 찌른 칼날이 후드 위로 곧게
    # 다시 (같은 날 사용자: 2타 6~8 칼 각도, 3타 당김·찌르기 자세가 이상함): 2타 6~8 은 쳐올린 칼이 왼쪽 어깨 위에서 왼쪽 위를 향함,
    # 3타 1~5 는 칼날이 몸 밖으로 나오는 자리 조금 안쪽을 손으로 잡아 칼을 온 길이로(손잡이는 몸 속), 6~8 은 찌른 칼날이 후드 위로 길게.
    # 3차 (2026-11-20 사용자: 측면·정면과 일관성) 정면 8장과 장마다 같은 그림으로 바꾸고 칼 자리를 다시 어림 (estimate_back_swords).
    ('backv3_3', 1): (35, 36, -51, True), ('backv3_3', 2): (33, 29, -59, True), ('backv3_3', 3): (36, 27, -70, True),
    ('backv3_3', 4): (35, 28, -68, True), ('backv3_3', 5): (36, 29, -67, True), ('backv3_3', 6): (33, 27, 90, True),
    ('backv3_3', 7): (33, 27, 90, True), ('backv3_3', 8): (33, 27, 90, True),
    # 후면은 두 손이 몸 앞(보는 사람 반대쪽)이라 칼이 몸에 가려진다: 머리 위로 든 때만 몸 위에 그린다
    ('back1', 1): (45, 43, 0, True), ('back1', 2): (44, 38, 54, True),
    ('back1', 3): (42, 28, 134, False), ('back1', 4): (36, 25, 60, False),
    ('back1', 5): (27, 37, -133, True), ('back1', 6): (27, 43, -142, True),
    ('back1', 7): (29, 44, -142, True), ('back1', 8): (29, 44, -142, True),
    ('back3', 7): (42, 28, 90, False), ('back3', 8): (34, 26, 90, False),
    ('attack2', 3): (56, 40, -65, False),
    ('attack2', 4): (40, 24, 110, True),
    ('attack2', 5): (37, 18, 155, True),  # 손잡이 끝이 얼굴 앞으로 삐져나와 눈처럼 보여 손을 머리 뒤로
    ('attack2', 6): (37, 19, 155, True),
    ('attack2', 7): (37, 21, 135, True),
    ('attack3', 5): (50, 38, 0, False),
    ('attack3', 6): (50, 38, 0, False),
    ('attack3', 7): (50, 38, 0, False),
}
# 쓰는 원본 프레임 (1~8). 2타 8번은 자세가 어정쩡해 7번을 한 번 더 쓴다 (2026-11-17 사용자 지적).
FRAME_PICK = {
    'parry_side': [1, 2, 3, 4, 5],
    'parry_front': [1, 2, 3, 4, 5],  # 패링: 당김, 쳐올림, 막기, 막기, 당김(복귀)
    'parry_back': [1, 2, 3, 4, 5],
    'backgpt1': [1, 2, 3, 4, 5, 6, 7, 8],
    'backv2_1': [1, 2, 3, 4, 5, 6, 7, 8],
    'backgpt2': [1, 2, 3, 4, 5, 6, 7, 8],
    'backgpt3': [1, 2, 3, 4, 5, 6, 7, 8],
    'backv3_2': [1, 2, 3, 4, 5, 6, 7, 8],
    'backv3_3': [1, 2, 3, 4, 5, 6, 7, 8],
    'attack1': [1, 2, 3, 4, 5, 6, 7, 8],
    'attack2': [1, 2, 3, 4, 5, 6, 7, 7],
    'attack3': [1, 2, 3, 4, 5, 6, 7, 8],
}
# 파란 덩어리를 모두 휘두른 잔상으로 보는 프레임 (칼은 몸에 가려 안 보이고 잔상만 있음, 2026-11-18 후면 1·2타)
FORCE_SMEAR = {('backgpt1', 4), ('backgpt2', 4), ('backpl1', 5), ('backpl1', 6), ('backv2_1', 6), ('backv3_2', 5)}
# 잔상을 몸 위에 겹쳐 그리는 프레임 (반투명): 후면 1타 내려베는 순간 — 몸 뒤면 가운데가 가려져 한 번에 베는 느낌이 안 남 (2026-11-18)
# 직접 그린 잔상이라 원본 칼 자리로 지우지 않는 칸
KEEP_WHOLE_SMEAR = {('backv2_1', 6), ('backv3_2', 5)}
SMEAR_ON_TOP = {('backpl1', 5)}  # backv2_1 5 는 몸 뒤 (2026-11-18 사용자 지적)
# 칼·잔상이 몸과 얼굴을 가로질러 지운 자리가 지저분하게 남는 프레임은 깨끗한 프레임의 그림을 빌려 쓴다
# (2026-11-17 사용자 지적: 얼굴 그림자가 프레임마다 다르고 픽셀이 묻어 있음).
# 1타 5·6번은 몸 자세가 7번과 거의 같아 몸 전체를 7번으로 (칼 각도와 잔상은 그 프레임 것).
BODY_DONOR = {('attack1', 5): 7, ('attack1', 6): 7}
# 2타 5·6번은 망토 자세가 달라 머리(후드+얼굴)만 7번에서 위치를 맞춰 옮긴다. (빌려 올 프레임, 7번 그림의 머리 칸 x0,y0,x1,y1)
HEAD_DONOR = {('attack2', c): (7, (24, 13, 47, 29)) for c in (4, 5, 6)}
# 다른 원본에서 가져오는 프레임: (공격, 프레임 1~8) -> (시트, 행, 칸).
# 1타 첫 시도의 3·4번은 몸이 정면으로 돌아가 얼굴이 2·3타와 달라, 같은 순간(칼을 머리 위로 치켜듦)의
# 1타 v3 측면 그림으로 바꾼다 (2026-11-17 사용자 요청: 첫 시도 동작 유지).
FRAME_SOURCE = {
    ('attack1', 3): ('attack1_side_v3_sheet_68.png', 0, 3),
    ('attack1', 4): ('attack1_side_v3_sheet_68.png', 0, 4),
}
# 잔상을 그리지 않는 공격: 정면 3타 찌르기는 원근으로 크게 그린 원본 칼날이 칼 아래로 삐져나와 보여서
NO_SMEAR = {'front3', 'backv3_2', 'backv3_3'}  # 후면 2·3타: 파란 칼은 잔상이 아님 (2타 5번째 잔상 장은 FORCE_SMEAR 라 남김)
BODY_MIN = 15  # 몸에서 떨어진 이보다 작은 조각은 찌꺼기로 보고 지운다
SMEAR_MIN = 25  # 이보다 작은 파란 조각은 잔상이 아니라 칼 조각으로 보고 지운다


def is_blue(c):
    return c[3] > 0 and c[2] - c[0] > 30


def cells(path, row, count=9):
    im = Image.open(os.path.join(RAW, path)).convert('RGBA')
    return [im.crop((c * CELL, row * CELL, c * CELL + CELL, row * CELL + CELL)) for c in range(count)]


def components(points):
    left = set(points)
    out = []
    while left:
        stack = [left.pop()]
        comp = []
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    p = (x + dx, y + dy)
                    if p in left:
                        left.remove(p)
                        stack.append(p)
        out.append(comp)
    return out


def axis(comp):
    """주성분: (평균, 단위 방향, 긴 축 표준편차, 짧은 축 표준편차)."""
    n = len(comp)
    mx = sum(p[0] for p in comp) / n
    my = sum(p[1] for p in comp) / n
    sxx = sum((p[0] - mx) ** 2 for p in comp) / n
    syy = sum((p[1] - my) ** 2 for p in comp) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in comp) / n
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    l1 = tr / 2 + math.sqrt(max(0.0, tr * tr / 4 - det))
    l2 = max(0.0, tr - l1)
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return (mx, my), (math.cos(theta), math.sin(theta)), math.sqrt(l1), math.sqrt(l2)


def find_sword(comp, body_center):
    """가늘고 긴 덩어리면 (손 x, 손 y, 각도) 를, 아니면 None."""
    if len(comp) < 8:
        return None
    (mx, my), (ux, uy), major, minor = axis(comp)
    if minor > 1.6 or major < 4:
        return None
    proj = {}
    for x, y in comp:
        t = round((x - mx) * ux + (y - my) * uy)
        s = (x - mx) * -uy + (y - my) * ux
        lo, hi = proj.get(t, (s, s))
        proj[t] = (min(lo, s), max(hi, s))
    t_min, t_max = min(proj), max(proj)
    end_a = (mx + ux * t_min, my + uy * t_min)
    end_b = (mx + ux * t_max, my + uy * t_max)
    da = math.dist(end_a, body_center)
    db = math.dist(end_b, body_center)
    sign = 1 if da <= db else -1  # 손잡이 → 칼끝 방향 (t 가 늘어나는 쪽이면 +1)
    hilt_t = t_min if sign == 1 else t_max
    tip_t = t_max if sign == 1 else t_min
    # 손잡이 쪽 절반에서 가장 넓은 곳 = 가드
    half = [t for t in proj if (t - hilt_t) * sign <= abs(tip_t - hilt_t) / 2]
    widths = {t: proj[t][1] - proj[t][0] for t in half}
    guard_t = max(widths, key=lambda t: (widths[t], -abs(t - hilt_t)))
    if widths[guard_t] < 2:
        guard_t = hilt_t + 2 * sign
    hand_t = guard_t - 2 * sign
    hx, hy = mx + ux * hand_t, my + uy * hand_t
    angle = math.degrees(math.atan2(-uy * sign, ux * sign))  # 화면 위가 + (y 반전)
    return hx, hy, angle


def analyse(frame):
    px = frame.load()
    blue = [(x, y) for y in range(CELL) for x in range(CELL) if is_blue(px[x, y])]
    body = [(x, y) for y in range(CELL) for x in range(CELL) if px[x, y][3] and not is_blue(px[x, y])]
    cx = sum(p[0] for p in body) / len(body)
    cy = sum(p[1] for p in body) / len(body)
    best, smear = None, []
    comps = sorted(components(blue), key=len, reverse=True)
    for comp in comps:
        found = None if best else find_sword(comp, (cx, cy))
        if found:
            best = found
        else:
            smear.extend(comp)
    return best, set(smear), set(blue)


# PixelLab 이 그린 칼을 그대로 떼어 '찌르기용 칼 그림'(무기 레이어)으로 쓰는 프레임 (2026-11-17 사용자 결정: 정면 3타 찌르는 순간).
# 보는 사람 쪽으로 튀어나오는 칼은 옆모습 칼 한 장을 돌려서는 그릴 수 없어서, 칼마다 이 그림을 따로 둔다.
KEEP_BLADE = {('front3', 6), ('front3', 7), ('front3', 8)}
# 게임 칼(old_sword.png)의 칼날 색, 어두운 것부터
STEEL = [(113, 83, 89, 255), (178, 154, 149, 255), (219, 204, 197, 255), (233, 220, 210, 255)]


def is_blade(c):
    """PixelLab 칼 픽셀: 파랑 또는 칼날의 흰 하이라이트."""
    return c[3] > 0 and (is_blue(c) or min(c[:3]) > 240)


def split_blade(frame):
    """(칼을 뺀 몸, 게임 칼 색으로 바꾼 칼만) 로 나눈다. 둘을 겹치면 원래 그림과 같다."""
    body, blade = frame.copy(), Image.new('RGBA', frame.size, (0, 0, 0, 0))
    src, bpx, apx = frame.load(), body.load(), blade.load()
    for y in range(frame.height):
        for x in range(frame.width):
            c = src[x, y]
            if is_blade(c):
                bpx[x, y] = (0, 0, 0, 0)
                light = sum(c[:3]) / 3
                level = 0 if light < 90 else 1 if light < 150 else 2 if light < 210 else 3
                apx[x, y] = STEEL[level]
    # 칼날을 둘러싼 검은 테두리도 칼 쪽으로 옮긴다 (다른 칼로 바꿨을 때 몸에 칼 테두리가 남지 않게)
    edge = [(x, y) for y in range(frame.height) for x in range(frame.width)
            if bpx[x, y][3] and max(bpx[x, y][:3]) < 45
            and any(0 <= x + dx < frame.width and 0 <= y + dy < frame.height and is_blade(src[x + dx, y + dy])
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        apx[x, y] = bpx[x, y]
        bpx[x, y] = (0, 0, 0, 0)
    return body, blade


def steel_blade(frame):
    """파란 칼과 흰 하이라이트를 밝기에 따라 게임 칼 색으로 바꾼다 (미리보기용: 몸 + 칼을 한 장으로)."""
    body, blade = split_blade(frame)
    body.alpha_composite(blade)
    img = body
    return img


def white_to_blue(frame):
    """거의 흰 픽셀을 파랑으로 바꿔 칼로 처리되게 한다."""
    img = frame.copy()
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3] and min(px[x, y][:3]) > 240:
                px[x, y] = (40, 90, 230, 255)
    return img


def fill_body(frame, blue):
    """파란 픽셀을 지우고, 몸 안쪽 구멍은 이웃 색으로 메운다."""
    img = frame.copy()
    px = img.load()
    for p in blue:
        px[p] = (0, 0, 0, 0)
    holes = set(blue)
    # 구멍 가장자리부터 한 겹씩 메운다. 이웃이 하나만 있어도 메워야 몸통을 가로지른 굵은 잔상 자리
    # (3줄 두께, 3타 찌르기)도 위·아래 몸 색으로 차례로 채워진다 (2026-11-17 사용자 지적: 몸통이 잘려 보임).
    for _ in range(8):
        filled = {}
        for x, y in holes:
            # 좌우 또는 위아래 양쪽에 몸이 있어야 안쪽 구멍
            def solid(dx, dy):
                for k in range(1, 4):  # 3픽셀 안: 3줄 잔상 자리는 메우고, 잔상 테두리와 몸 사이의 넓은 틈은 두기
                    q = (x + dx * k, y + dy * k)
                    if not (0 <= q[0] < CELL and 0 <= q[1] < CELL):
                        return False
                    # 검은 외곽선만으로는 몸이라 보지 않는다 (칼날 양옆 외곽선 사이를 메우지 않게)
                    if px[q][3] and max(px[q][:3]) >= 45:
                        return True
                return False
            if not ((solid(1, 0) and solid(-1, 0)) or (solid(0, 1) and solid(0, -1))):
                continue
            near = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= x + dx < CELL and 0 <= y + dy < CELL and px[x + dx, y + dy][3]]
            if near:
                # 위쪽 이웃 색을 먼저 쓴다: 얼굴을 지나간 칼 자리는 후드 그림자로 채워져 눈·피부가 드러나지 않게
                above = px[x, y - 1] if y > 0 else (0, 0, 0, 0)
                filled[(x, y)] = above if above[3] else Counter(near).most_common(1)[0][0]
        for p, c in filled.items():
            px[p] = c
            holes.discard(p)
        if not filled:
            break
    return img


def paste_sword(canvas, hx, hy, angle, sword=None, grip=True):
    """칼 그림 한가운데(손)를 (hx, hy) 에 두고 angle 만큼 돌려 붙인다 (nearest).

    grip=False 면 손잡이(손 뒤쪽 절반)를 그리지 않는다. 머리 뒤로 넘긴 칼의 손잡이 끝이 얼굴 앞으로 삐져나오지 않게.
    """
    sword = sword or SWORD
    if not grip:
        sword = sword.copy()
        sword.paste((0, 0, 0, 0), (0, 0, sword.width // 2, sword.height))
    big = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
    big.paste(sword, (40 - sword.width // 2, 40 - sword.height // 2))
    rot = big.rotate(angle, resample=Image.NEAREST, center=(40, 40))
    canvas.alpha_composite(rot, (round(hx) - 40, round(hy) - 40))


def smear_layer(frame, smear):
    img = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    px, src = img.load(), frame.load()
    for p in smear:
        light = sum(src[p][:3]) / 3
        img.putpixel(p, (235, 242, 255, 120 + round(min(1.0, light / 200) * 110)))
    return img


def interpolate(values):
    """None 인 칸을 앞뒤 값으로 잇는다 (각도는 가까운 쪽으로 돌기)."""
    known = [i for i, v in enumerate(values) if v]
    out = list(values)
    for i, v in enumerate(values):
        if v:
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        if prev is None or nxt is None:
            out[i] = values[prev if prev is not None else nxt]
            continue
        t = (i - prev) / (nxt - prev)
        a, b = values[prev], values[nxt]
        d = (b[2] - a[2] + 180) % 360 - 180
        out[i] = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + d * t)
    return out


def near_sword(p, hx, hy, angle):
    """원본 칼(손잡이 뒤 8px ~ 칼끝 40px) 선에서 2px 안이면 True."""
    ux, uy = math.cos(math.radians(angle)), -math.sin(math.radians(angle))
    t = (p[0] - hx) * ux + (p[1] - hy) * uy
    s = abs((p[0] - hx) * -uy + (p[1] - hy) * ux)
    return -8 <= t <= 40 and s <= 3.0


def erase_sword_outline(body, blue):
    """원본 칼·잔상의 검은 테두리를 지운다.

    지운 파란 픽셀 중 몸 밖에 남은 자리(빈칸)에 바로 붙어 있고, 갈색(몸) 이웃이 없는 아주 어두운 픽셀만 지운다.
    전에는 칼 선 둘레(손 뒤 8픽셀까지)를 통째로 봐서 얼굴 그림자까지 지워졌다 (2026-11-17 사용자 지적).
    한 번만 지운다 (되풀이하면 그림자를 파먹는다).
    """
    px = body.load()

    def dark(c):
        return c[3] and max(c[:3]) < 45

    empty = {p for p in blue if not px[p][3]}
    for _ in range(2):  # 두 겹까지 (테두리가 2픽셀 두께인 곳). 갈색 이웃이 있는 그림자는 남는다
        gone = []
        for y in range(CELL):
            for x in range(CELL):
                if not dark(px[x, y]):
                    continue
                if not any((x + dx, y + dy) in empty for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    continue
                brown = any(0 <= x + dx < CELL and 0 <= y + dy < CELL and px[x + dx, y + dy][3]
                            and not dark(px[x + dx, y + dy])
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if not brown:
                    gone.append((x, y))
        for p in gone:
            px[p] = (0, 0, 0, 0)
        empty.update(gone)


SHADOW = (0x17, 0x11, 0x16, 255)  # 후드 그림자 색
SKIN = (0xba, 0x7b, 0x6a, 255)  # 턱 피부 보통 색
HIDE_EYES = set()  # 1타 v3 는 눈이 이미 가려져 있음  # 눈이 드러난 공격 (2026-11-17 사용자 요청: 2·3타처럼 후드 그림자로 가리고 턱만 보이게)


def is_skin(c):
    return c[3] and c[0] > 120 and c[0] > c[1] > c[2] and min(c[:3]) <= 140


def hide_eyes(body):
    """눈(머리 쪽 흰 픽셀)과 그 줄·바로 아래 줄의 피부를 그림자로 덮고, 남은 피부 사이의 입은 피부색으로 메운다."""
    px = body.load()
    eyes = [(x, y) for y in range(45) for x in range(CELL)
            if px[x, y][3] and min(px[x, y][:3]) > 220]  # 눈빛: 거의 흰색 (회색 쇠붙이·손은 제외)
    if not eyes:
        return
    eye_rows = {y for _, y in eyes}
    xs = [x for x, _ in eyes]
    x0, x1 = min(xs) - 6, max(xs) + 6  # 얼굴 가로 범위 (다른 쪽 눈까지)
    for x, y in eyes:
        px[x, y] = SHADOW
    for y in eye_rows | {y + 1 for y in eye_rows}:
        for x in range(max(0, x0), min(CELL, x1 + 1)):
            c = px[x, y]
            # 눈 줄: 피부와 회색 눈빛은 모두 그림자로 (갈색 후드는 그대로)
            if is_skin(c) or (y in eye_rows and c[3] and abs(c[0] - c[2]) < 25 and max(c[:3]) > 60):
                px[x, y] = SHADOW
    # 턱의 튀는 밝은 주황 픽셀(눈빛처럼 보임)은 보통 피부색으로
    for y in range(max(eye_rows) + 1, min(CELL, max(eye_rows) + 6)):
        for x in range(max(0, x0), min(CELL, x1 + 1)):
            c = px[x, y]
            if is_skin(c) and c[0] > 200:
                px[x, y] = SKIN
    # 입: 아래 줄들에서 좌우가 피부인 어두운 픽셀
    for y in range(max(eye_rows) + 2, min(CELL, max(eye_rows) + 6)):
        for x in range(max(1, x0), min(CELL - 1, x1 + 1)):
            c = px[x, y]
            if c[3] and not is_skin(c) and max(c[:3]) < 90:
                left = next((px[x - k, y] for k in (1, 2) if x - k >= 0 and is_skin(px[x - k, y])), None)
                right = any(x + k < CELL and is_skin(px[x + k, y]) for k in (1, 2))
                if left and right:
                    px[x, y] = left


def drop_fragments(body):
    """몸에서 떨어진 작은 조각(잔상 꼬리 등 찌꺼기)을 지운다."""
    px = body.load()
    solid = [(x, y) for y in range(CELL) for x in range(CELL) if px[x, y][3]]
    for comp in components(solid):
        if len(comp) < BODY_MIN:
            for p in comp:
                px[p] = (0, 0, 0, 0)


def process_body(name, frame):
    """한 프레임의 몸: 파란 칼·잔상을 지우고 구멍 메우기, 칼 테두리·찌꺼기 지우기, (필요하면) 눈 가리기."""
    blue = {(x, y) for y in range(CELL) for x in range(CELL) if is_blue(frame.getpixel((x, y)))}
    body = fill_body(frame, blue)
    erase_sword_outline(body, blue)
    drop_fragments(body)
    remove_grey_specks(body)
    if name in HIDE_EYES:
        hide_eyes(body)
    return body


def remove_grey_specks(body):
    """몸 위에 튀는 작은 회색 점 덩어리(4픽셀 이하, 원본 칼 조각 등)를 둘레의 회색 아닌 색으로 바꾼다."""
    px = body.load()

    def grey(c):
        return c[3] and max(c[:3]) >= 100 and max(c[:3]) - min(c[:3]) <= 25

    greys = [(x, y) for y in range(CELL) for x in range(CELL) if grey(px[x, y])]
    for comp in components(greys):
        if len(comp) > 4:
            continue
        for x, y in comp:
            near = [px[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if (dx or dy) and 0 <= x + dx < CELL and 0 <= y + dy < CELL
                    and px[x + dx, y + dy][3] and not grey(px[x + dx, y + dy])]
            if near:
                px[x, y] = Counter(near).most_common(1)[0][0]


def best_offset(target, donor, box, search=4):
    """donor 의 box 안 모양(투명/불투명)이 target 과 가장 잘 겹치는 (dx, dy)."""
    x0, y0, x1, y1 = box
    tp, dp = target.load(), donor.load()
    best, best_score = (0, 0), None
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            score = 0
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    tx, ty = x + dx, y + dy
                    t = tp[tx, ty][3] > 0 if 0 <= tx < CELL and 0 <= ty < CELL else False
                    score += t == (dp[x, y][3] > 0)
            if best_score is None or score > best_score or (score == best_score and abs(dx) + abs(dy) < abs(best[0]) + abs(best[1])):
                best, best_score = (dx, dy), score
    return best


def transplant_head(target, donor, box):
    """donor 의 머리(box 안)를 target 의 머리 자리에 옮겨 붙인다. target 의 그 자리는 먼저 비운다."""
    dx, dy = best_offset(target, donor, box)
    x0, y0, x1, y1 = box
    tp, dp = target.load(), donor.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            tx, ty = x + dx, y + dy
            if 0 <= tx < CELL and 0 <= ty < CELL:
                tp[tx, ty] = dp[x, y]


def build_layers(name, frames):
    """프레임 목록 → (프레임별 레이어 {body, hand, sword}, 칼 표, 분석 결과). 좌표는 68×68 칸 기준."""
    picks = FRAME_PICK.get(name, [1, 2, 3, 4, 5, 6, 7, 8])
    frames = list(frames)
    for (n, c), (sheet, row, col) in FRAME_SOURCE.items():
        if n == name:
            frames[c - 1] = cells(sheet, row)[col]
    originals = list(frames)
    if name in NO_SMEAR:
        # 원본 칼날의 흰 하이라이트 줄(파랑으로 잡히지 않음)도 칼과 함께 지운다. 주인공 그림에는 흰색이 없다.
        frames = [white_to_blue(f) for f in frames]
    raw_frames = frames
    frames = [frames[i - 1] for i in picks]
    infos = [analyse(f) for f in frames]
    raw = []
    for i, info in zip(picks, infos):
        if (name, i) in OVERRIDES:
            raw.append(OVERRIDES[(name, i)])
        elif info[0]:
            raw.append(info[0] + (False,))
        else:
            raw.append(None)
    swords = interpolate(raw)
    layers = []
    for col, frame, (found, smear, blue), sword in zip(picks, frames, infos, swords):
        hx, hy, angle = sword[:3]
        behind = sword[3] if len(sword) > 3 else False
        extra = tuple(sword[4:5])  # 칼 길이 비율 (0 = 그리지 않음)
        if (name, col) in FORCE_SMEAR:
            smear = set(blue)
        if (name, col) in BODY_DONOR:
            body = process_body(name, raw_frames[BODY_DONOR[(name, col)] - 1])
        else:
            body = process_body(name, frame)
        if (name, col) in HEAD_DONOR:
            donor_col, box = HEAD_DONOR[(name, col)]
            transplant_head(body, process_body(name, raw_frames[donor_col - 1]), box)
        # 원본 칼 둘레와 작은 조각은 지우고, 큰 덩어리만 잔상으로
        if (name, col) not in KEEP_WHOLE_SMEAR:  # 직접 그린 잔상은 칼 자리로 지우지 않음 (가운데가 끊겼음, 같은 날 사용자 지적)
            smear = {p for p in smear if not near_sword(p, hx, hy, angle)}
        # 작은 조각과 가는 줄(원본 칼의 가장자리)은 지우고, 넓은 덩어리만 잔상으로
        smear = {p for comp in components(smear)
                 if len(comp) >= SMEAR_MIN and (axis(comp)[3] > 1.6 or (name, col) in FORCE_SMEAR) for p in comp}
        if name in NO_SMEAR and (name, col) not in FORCE_SMEAR:
            smear = set()
        if behind and extra != (0,):
            # 칼이 몸 뒤: 칼이 지나가는 자리의 몸 쪽 검은 테두리(원본 칼 외곽선)를 지워 칼이 보이게 한다.
            blade = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
            paste_sword(blade, hx, hy, angle, grip=False)  # 칼날 자리만 (손잡이 자리는 얼굴 그림자라 두기)
            bl, bpx = blade.load(), body.load()
            for y in range(CELL):
                for x in range(CELL):
                    if bl[x, y][3] and bpx[x, y][3] and max(bpx[x, y][:3]) < 45:
                        bpx[x, y] = (0, 0, 0, 0)
        # 몸 레이어 = 잔상(뒤) + 몸 (SMEAR_ON_TOP 이면 몸 위에 잔상)
        if (name, col) in SMEAR_ON_TOP:
            sheet = body.copy()
            sheet.alpha_composite(smear_layer(frame, smear))
        else:
            sheet = smear_layer(frame, smear)
            sheet.alpha_composite(body)
        # 손 레이어: 칼 위에 다시 그리는 손 둘레 몸 픽셀 (칼이 앞에 있을 때만)
        hand = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        if not behind:
            bpx = body.load()
            for y in range(CELL):
                for x in range(CELL):
                    c = bpx[x, y]
                    # 아주 어두운 픽셀은 원본 칼 테두리일 수 있어 칼 위에 다시 그리지 않는다
                    if c[3] and max(c[:3]) >= 45 and math.dist((x, y), (hx, hy)) <= HAND_RADIUS:
                        hand.putpixel((x, y), c)
        art = None
        if (name, col) in KEEP_BLADE:
            # PixelLab 이 그린 칼을 떼어 무기 레이어(art)로, 나머지는 몸으로. 칼이 덮던 다리 자리는 칼이 그대로 덮는다.
            sheet, art = split_blade(originals[col - 1])
            hand = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
        layers.append({'body': sheet, 'hand': hand, 'sword': (hx, hy, angle, bool(behind)) + extra, 'art': art})
    return layers, swords, infos


def compose(layer, pad=PAD):
    """게임과 같은 순서로 합친다: 칼이 뒤면 칼 → 몸, 아니면 몸 → 칼 → 손."""
    hx, hy, angle, behind, *rest = layer['sword']
    hidden = bool(rest) and rest[0] <= 0
    out = Image.new('RGBA', (CELL + pad * 2, CELL), (0, 0, 0, 0))
    if behind and not hidden:
        paste_sword(out, hx + pad, hy, angle)
    out.alpha_composite(layer['body'], (pad, 0))
    if not behind and not hidden:
        paste_sword(out, hx + pad, hy, angle)
        out.alpha_composite(layer['hand'], (pad, 0))
    return out


def build(name, frames):
    """프레임 목록 → (합친 그림 목록, 칼 표, 자동으로 찾은 프레임)."""
    layers, swords, infos = build_layers(name, frames)
    table = [(round(s[0], 1), round(s[1], 1), round(s[2]), bool(s[3]) if len(s) > 3 else False) + tuple(s[4:5])
             for s in swords]
    return [compose(l) for l in layers], table, [i[0] is not None for i in infos]


def save_gif(frames, path, durations, scale=4):
    imgs = []
    for f in frames:
        g = Image.new('RGBA', f.size, BG)
        g.alpha_composite(f)
        big = g.resize((f.width * scale, f.height * scale), Image.NEAREST).convert('RGB')
        # 프레임마다 자기 팔레트, 디더링 없이. (RGBA 를 그대로 넘기면 모든 프레임이 첫 프레임 팔레트를 써서
        # 뒤 프레임 색이 17색 정도로 뭉개져 몸이 깨지고 비어 보였다. 2026-11-17 사용자 지적)
        imgs.append(big.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durations, loop=0, disposal=2,
                 optimize=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    combo, durs, tables = [], [], {}
    idle = cells(ATTACKS[0][1], ATTACKS[0][2])[0]
    for name, path, row in ATTACKS:
        frames = cells(path, row)[1:]  # 0번은 기준(서 있는) 그림
        built, table, detected = build(name, frames)
        tables[name] = {'sword': table, 'detected': detected}
        combo += built
        per = round(DURATIONS[name] * 1000 / len(built))
        durs += [per] * len(built)
        save_gif(built, os.path.join(OUT, f'{name}_side_sword.gif'), [per * 2] * len(built))
    idle_padded = Image.new('RGBA', (CELL + PAD * 2, CELL), (0, 0, 0, 0))
    idle_padded.alpha_composite(idle, (PAD, 0))
    combo.append(idle_padded)
    durs.append(500)
    save_gif(combo, os.path.join(OUT, 'combo_side_sword.gif'), durs)
    save_gif(combo, os.path.join(OUT, 'combo_side_sword_slow.gif'), [d * 3 for d in durs[:-1]] + [700])
    # 한 장 보기 (한 줄에 8장 = 한 타)
    w = CELL + PAD * 2
    grid = Image.new('RGBA', (w * 8 * 2, CELL * 2 * 4), BG)
    for i, f in enumerate(combo):
        g = Image.new('RGBA', f.size, BG)
        g.alpha_composite(f)
        grid.paste(g.resize((w * 2, CELL * 2), Image.NEAREST), ((i % 8) * w * 2, (i // 8) * CELL * 2))
    grid.save(os.path.join(OUT, 'combo_side_sword_grid.png'))
    with open(os.path.join(OUT, 'sword_table.json'), 'w', encoding='utf-8') as f:
        json.dump(tables, f, indent=1)
    # 점프 4방향 나란히
    jump = Image.open(os.path.join(RAW, 'jump_sheet_68.png')).convert('RGBA')
    jframes = []
    for c in list(range(9)) + [0, 0]:
        row = Image.new('RGBA', (CELL * 4, CELL), (0, 0, 0, 0))
        for r in range(4):
            row.alpha_composite(jump.crop((c * CELL, r * CELL, c * CELL + CELL, r * CELL + CELL)), (r * CELL, 0))
        jframes.append(row)
    save_gif(jframes, os.path.join(OUT, 'jump_4dir.gif'), [75] * len(jframes), scale=3)
    save_gif(jframes, os.path.join(OUT, 'jump_4dir_slow.gif'), [200] * len(jframes), scale=3)
    print(json.dumps({k: v['detected'] for k, v in tables.items()}))


if __name__ == '__main__':
    main()
