"""후면 공격 2차 (2026-11-18 사용자: GPT 그림은 픽셀이 깨지고 동작이 어설픔 → PixelLab 으로, 측면·정면만큼 베는 느낌 있게).

GPT 8자세(attack_back_gpt_68.png) 중 핵심 자세를 시작·끝으로 PixelLab animate_image 가 사이를 다시 그린 것
(attack_back_kit/pl_out/hit<N>_<a|b|c>_<0..4>.png, 68×68, 같은 칸 자리)에서 8장을 고른다.
- 색: 게임 주인공 색으로 맞추고 파란 칼은 파란색 하나로 (build_parry_back.snap).
- 휘두르는 장에는 GPT 그림의 파란 잔상(ARC 의 칸)을 겹친다 (PixelLab 은 잔상을 그리지 않음, 베는 느낌).
출력: remake_raw/attack_back_pl_68.png (타마다 한 줄, 칸 0 = 게임 뒷모습). export_to_game.py 가 읽는다.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_parry_back as pb  # noqa: E402
import build_parry_front as pf  # noqa: E402
import build_remake_preview as b  # noqa: E402

KIT = os.path.join(HERE, 'attack_back_kit')
# 타별 8장: (구간, 번호). a = 서기→들어 올림, b = 들어 올림→내려벤 끝, c = 끝→서기 (1타)
# 1타 3차 (2026-11-18 사용자: 측면·정면처럼 — 칼을 왼쪽 아래에서 꺼내 오른쪽 위로 옮긴 뒤 오른쪽 위에서 내려벰, 박자도 측면과 같게):
# d = 왼쪽 아래 → 오른쪽 어깨 위 (PixelLab 새로), b = 내려베기, c = 마무리. 8장 같은 간격, 5번째(판정)가 잔상 장.
# 4차 (같은 날 사용자: 억지로 빠르게 옮겨 베는 느낌): 구간을 이어 붙이지 않고 PixelLab 이 1타 전체를 한 번에 이어 그림
# (animate_image, 왼쪽 아래 자세에서 시작, 8장 = full_v3_1~8). 5번째(판정)는 칼이 몸 앞을 지나 안 보이는 장 → 잔상.
# 6차 (같은 날 사용자: 칼을 꺼내 옮기는 앞부분이 부자연스럽고 정면과 박자가 다름): 정면처럼 칼을 오른쪽 어깨 위로 든 자세에서
# 시작해 조금 더 들며 버티다가 5번째(0.5)에 내려벤다. 왼쪽 아래에서 꺼내 휘돌리는 1·2번째는 뺌.
PICK = {
    1: ['full_v3_3', 'full_v3_3', 'full_v3_4', 'full_v3_4', 'full_v3_5', 'full_v3_6', 'full_v3_7', 'full_v3_8'],
}
# 휘두르는 장에 겹칠 GPT 잔상: 타 → (8장 중 번호 0부터, GPT 시트 칸). 1타는 아래 SWOOSH 로 대신 (5차)
ARC = {}
# 5차 (같은 날 사용자: 정면은 위압감 있게 딱 베는데 후면은 베는 느낌이 없음): 칼이 지나간 길대로 큰 초승달 잔상을 계산해 그린다.
# 타 → [(8장 중 번호, 원 중심 x, y, 반지름, 시작 각도, 끝 각도, 가장 두꺼운 폭)]. 각도는 화면 기준(오른쪽 0, 아래 90).
# 1타: 오른쪽 어깨 위에서 오른쪽 아래로 크게 부풀며 왼쪽 아래까지 (몸 뒤라 몸 밖으로 나온 부분만 보임), 다음 장은 얇게 남음.
SWOOSH = {1: [(4, 22, 20, 36, -20, 112, 8), (5, 22, 20, 36, 30, 112, 4)]}
# 좌우로 뒤집는 타 (2026-11-18 사용자: 측면·정면 1타는 화면 왼쪽 위로 들어 오른쪽 아래로 벰. GPT·PixelLab 후면은 반대였음).
# 뒷모습은 거의 좌우 대칭이라 그림째 뒤집는다 (칼 위치는 build_remake_preview.OVERRIDES 'backpl1' 이 뒤집은 값).
MIRROR = set()  # 3차에서 되돌림: 측면·정면처럼 오른쪽 위에서 내려벤다 (사용자 설명)


def blue_only(cell):
    out = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    src, dst = cell.load(), out.load()
    for y in range(cell.height):
        for x in range(cell.width):
            if b.is_blue(src[x, y]):
                dst[x, y] = pb.BLUE
    return out


SWOOSH_ON_TOP = {(1, 4)}  # 1타 내려베는 순간 (8장 중 5번째)


def swoosh(size, cx, cy, r, a0, a1, thick):
    """초승달 잔상 (파란 단색 = 게임에서 잔상 색으로 바뀜): 가운데가 가장 두껍고 양 끝은 가늘게."""
    import math
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    px = out.load()
    steps = 240
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * math.sin(math.pi * t) ** 0.7  # 바깥쪽으로 두께
        for k in range(int(w * 4) + 1):
            rr = r - k / 4
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            if 0 <= x < size[0] and 0 <= y < size[1]:
                px[int(x), int(y)] = pb.BLUE
    return out


def main():
    palette = pf.game_palette()
    gpt_rows = {hit: b.cells('attack_back_gpt_68.png', hit - 1) for hit in (1, 2, 3)}
    sheet = Image.new('RGBA', (68 * 9, 68 * 3), (0, 0, 0, 0))
    for hit, names in PICK.items():
        cells = [gpt_rows[hit][0]]
        for k, n in enumerate(names):
            name = n if '_' in n else f'{n[0]}_{n[1]}'  # 'd0' → d_0, 'full_v3_1' 그대로
            f = pb.snap(Image.open(os.path.join(KIT, 'pl_out', f'hit{hit}_{name}.png')).convert('RGBA'), palette)
            if hit in ARC and ARC[hit][0] == k:
                arc = blue_only(gpt_rows[hit][ARC[hit][1]])
                arc.alpha_composite(f)  # 잔상은 몸 뒤
                f = arc
            for k2, cx, cy, r, a0, a1, th in SWOOSH.get(hit, []):
                if k2 == k:
                    arc = swoosh(f.size, cx, cy, r, a0, a1, th)
                    if (hit, k) in SWOOSH_ON_TOP:
                        f = f.copy()
                        f.alpha_composite(arc)  # 몸 위로도 이어지게 (게임은 build_remake_preview.SMEAR_ON_TOP 로 몸 위에 반투명하게)
                    else:
                        arc.alpha_composite(f)  # 잔상은 몸 뒤
                        f = arc
            if hit in MIRROR:
                f = f.transpose(Image.FLIP_LEFT_RIGHT)
            cells.append(f)
        for k, c in enumerate(cells):
            sheet.alpha_composite(c, (k * 68, (hit - 1) * 68))
    sheet.save(os.path.join(b.RAW, 'attack_back_pl_68.png'))
    print('ok')


if __name__ == '__main__':
    main()
