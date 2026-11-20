"""후면 2·3타 시트 (2026-11-18): 1타(build_attack_back_v2.py)와 같은 방법.

ChatGPT 가 정면 2·3타 8장(미리 좌우로 뒤집어 준 것)을 "뒤에서 본 같은 순간"으로 그린 그림
(attack_back_kit/hit2_v2/result_hit2_back.png, hit3_v2/result_hit3_back.png, 한 줄 8자세, 칼은 파란 단색)을
배경 제거 → 8자세 자르기 → 게임 뒷모습 키에 맞춰 NEAREST 로 줄임 → 발 맞춤.
8장은 한 번의 PixelLab transfer_outfit 으로 함께 화풍을 입힌 것(hitN_v2/restyle_out/r1~8)이 있으면 그것을 쓰고,
8장 함께 색감 맞춤 → 외톨이 점 정리. 2타는 쳐올리는 장에 초승달 잔상을 몸 뒤에 깐다.
망토 명암은 게임에 내보낼 때 back_shading.py 가 넣으므로 여기서는 명암 없는 서기 그림 색에 맞춘다.
출력: remake_raw/attack_back_v3_68.png (0행 = 2타, 1행 = 3타, 칸 0 = 게임 뒷모습), restyle 입력은 hitN_v2/restyle_in/f0~8.
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_attack_back_pl as bp  # noqa: E402  (초승달 잔상)
import build_attack_back_v2 as v2  # noqa: E402  (자르기·색감 맞춤·점 정리)
import build_parry_back as pb  # noqa: E402
import build_parry_front as pf  # noqa: E402
import build_remake_preview as b  # noqa: E402

KIT = os.path.join(HERE, 'attack_back_kit')
GAME = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'images', 'player'))
HITS = {
    2: {'dir': 'hit2_v3', 'src': 'result_hit2_back.png',  # 3차 (2026-11-20 사용자: 측면·정면과 일관성): 정면과 장마다 같은 그림
        # 쳐올리는 장(8장 중 번호)의 잔상: (원 중심 x, y, 반지름, 시작 각도, 끝 각도, 두께). 오른쪽 아래 → 왼쪽 위
        # 쳐올리는 장들의 잔상 [(장, 원 인자)], 'reuse': {장: 몸을 빌려 올 장}.
        # 2026-11-20 사용자 지적(후면 동작 순서가 이상함): 정면은 5 쳐올림(칼이 보임) → 6 머리 위로 계속(칼을 든 채 머리 위 잔상)
        # → 7·8 어깨에 멈춤인데, 후면은 6 에서 이미 멈춘 자세였다. 6 은 5 의 몸(칼을 쳐든)에 머리 위 잔상을 얹는다.
        # 잔상 모양 (같은 날 사용자: 2타 후면 잔상도 정면처럼): 계산한 호 대신 정면 같은 장(5·6번째)의 잔상을 좌우로 뒤집어 그대로 쓴다.
        # ('front', 정면 장 번호 0부터) = 정면 게임 그림의 잔상 픽셀을 뒷모습 몸 가운데 기준으로 뒤집어 옮김.
        'swoosh': [(5, ('front', 4)), (6, ('front', 5))], 'reuse': {6: 5},
        # 다리 (같은 날 사용자: 다리 위치가 이상함): ChatGPT 그림은 장마다 발 간격·다리 길이가 달라 꿈틀거렸다. 정면처럼
        # 1~4 는 같은 선 자세(1 의 다리), 5~8 은 오른발을 뒤로 든 자세(7 의 다리)로 맞춘다. {장: 다리를 빌려 올 장}
        'legs': {2: 1, 3: 1, 4: 1, 5: 7, 6: 7, 8: 7}},
    3: {'dir': 'hit3_v3', 'src': 'result_hit3_back_frontmatch.png', 'swoosh': None},  # 3차: 사용자가 받은 그림 중 정면과 장마다 같은 것
}
OUT = 'attack_back_v3_68.png'


def body_feet(im):
    """발 맞춤 기준: (후드 가로 가운데, 몸 가장 아래 줄).

    칼의 검은 테두리가 발 높이에서 몸 옆을 지나면 발 가운데가 칼 쪽으로 끌려 그림이 옆으로 밀렸다 (2타·3타 첫 장).
    가로는 칼이 닿지 않는 후드(몸 위 25%)의 가운데로, 세로는 갈색 픽셀(빨강이 파랑보다 확실히 큰)의 가장 아래로 잡는다.
    """
    px = im.load()
    body = [(x, y) for y in range(im.height) for x in range(im.width)
            if px[x, y][3] > 128 and not b.is_blue(px[x, y])]
    top = min(y for _, y in body)
    brown = [y for x, y in body if px[x, y][0] > px[x, y][2] + 5]
    bottom = max(brown)
    hood = [x for x, y in body if y <= top + (bottom - top) * 0.25]
    return (min(hood) + max(hood)) / 2, bottom


def no_blue(im):
    im = im.convert('RGBA').copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] and b.is_blue(px[x, y]):
                px[x, y] = (0, 0, 0, 0)
    return im


def body_h(im):
    """칼(파랑) 빼고 몸 키."""
    im = im.convert('RGBA')
    px = im.load()
    rows = [y for y in range(im.height) if any(px[x, y][3] > 128 and not b.is_blue(px[x, y]) for x in range(im.width))]
    return rows[-1] - rows[0] + 1


CELL_TO_GAME = (14, -3)  # 이 시트 칸(68) 좌표 + 이것 = 게임 공격 그림(96×64) 좌표


def is_smear(c):
    """게임 그림의 잔상 픽셀 (밝은 회청색)."""
    return c[3] > 100 and c[0] > 150 and abs(c[0] - c[2]) < 40


def hood_centre_x(im):
    px = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3] > 128 and not is_smear(px[x, y])]
    top = min(y for _, y in pts)
    xs = [x for x, y in pts if y <= top + 4]
    return (min(xs) + max(xs)) / 2


def front_smear(hit, k, size):
    """정면 hit 타 k 번째 장의 잔상을 좌우로 뒤집어 이 시트 칸 좌표의 파란 잔상으로 (몸 가운데끼리 맞춤)."""
    front = Image.open(os.path.join(GAME, 'sword_attack', f'front_{hit}.png')).convert('RGBA')
    fw = front.width // 8
    f = front.crop((k * fw, 0, (k + 1) * fw, front.height))
    first = front.crop((0, 0, fw, front.height))
    back = Image.open(os.path.join(GAME, 'sword_attack', f'back_{hit}.png')).convert('RGBA')
    cf, cb = hood_centre_x(first), hood_centre_x(back.crop((0, 0, back.width // 8, back.height)))
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    px, fpx = out.load(), f.load()
    for y in range(f.height):
        for x in range(f.width):
            if is_smear(fpx[x, y]):
                gx = math.floor(cb + cf - x)  # 몸 가운데를 축으로 뒤집음 (round 는 .5 를 짝수로 보내 한 줄씩 비었음)
                cx, cy = gx - CELL_TO_GAME[0], y - CELL_TO_GAME[1]
                if 0 <= cx < size[0] and 0 <= cy < size[1]:
                    px[cx, cy] = pb.BLUE
    return out


LEG_Y = 51  # 이 줄부터 아래(망토 자락 끝 ~ 발)를 다리로 본다


def swap_legs(cell, src):
    """cell 의 LEG_Y 아래를 src 의 다리로 바꾼다. 후드 가운데 차이만큼 옮겨 몸 아래에 붙이고, cell 의 파란 칼은 남긴다."""
    dx = round(body_feet(cell)[0] - body_feet(src)[0])
    out = cell.copy()
    px, spx = out.load(), src.load()
    w, h = out.size
    for y in range(LEG_Y, h):
        for x in range(w):
            if px[x, y][3] and b.is_blue(px[x, y]):
                continue
            sx = x - dx
            c = spx[sx, y] if 0 <= sx < w else (0, 0, 0, 0)
            px[x, y] = (0, 0, 0, 0) if c[3] and b.is_blue(c) else c
    return out


def v2_sheet():
    return 'attack_back_v2_68.png'  # 1타 시트 (build_attack_back_v2.py)


def hood_width(im):
    """후드 너비: 파랑(칼)을 뺀 몸 윗부분(맨 위에서 몸 키 30% 까지) 줄들 중 가장 넓은 너비."""
    im = im.convert('RGBA')
    px = im.load()
    rows = [y for y in range(im.height) if any(px[x, y][3] > 128 and not b.is_blue(px[x, y]) for x in range(im.width))]
    top, bottom = rows[0], rows[-1]
    best = 0
    for y in range(top, top + int((bottom - top) * 0.3) + 1):
        xs = [x for x in range(im.width) if px[x, y][3] > 128 and not b.is_blue(px[x, y])]
        if xs:
            best = max(best, xs[-1] - xs[0] + 1)
    return best


def build(hit, ref, palette):
    cfg = HITS[hit]
    folder = os.path.join(KIT, cfg['dir'])
    rfx, rfy = body_feet(ref)
    x0, y0, x1, y1 = ref.getchannel('A').getbbox()
    cx, foot = (x0 + x1) // 2, y1 - 1
    poses = v2.split_n(pb.remove_bg(Image.open(os.path.join(folder, cfg['src']))))
    assert len(poses) == 8, (hit, len(poses))
    # 크기 (같은 날 사용자: 1타와 약간 다름 → 재 보니 2타가 약 15%, 3타가 약 8% 작았다. 후드 너비로 맞추면 ChatGPT 가 후드를
    # 넓게 그려 작아짐): 같은 타 정면 그림의 장마다 키(칼 빼고)에 맞추는 배율들의 가운데값으로 맞춘다.
    front = Image.open(os.path.join(GAME, 'sword_attack', f'front_{hit}.png')).convert('RGBA')
    fw = front.width // 8
    ratios = sorted(body_h(front.crop((k * fw, 0, (k + 1) * fw, front.height))) / body_h(p) for k, p in enumerate(poses))
    scale = ratios[len(ratios) // 2]
    cells = [ref]
    for p in poses:
        small = pb.snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.NEAREST),
                        palette)
        fx, fy = body_feet(small)  # 발 찾기에서 칼은 뺀다 (줄인 칼 가장자리의 푸르스름한 점을 발로 잡아 옆으로 밀렸음)
        c = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        c.alpha_composite(small, (round(rfx - fx), round(rfy - fy)))
        cells.append(c)
    body = []
    for f in cells:
        big = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
        big.alpha_composite(f, (40, 40))
        body.append(big.crop((40 + cx - 34, 40 + foot - 58, 40 + cx + 34, 40 + foot + 10)))
    restyle_in = os.path.join(folder, 'restyle_in')
    os.makedirs(restyle_in, exist_ok=True)
    for k, cell in enumerate(body):
        cell.save(os.path.join(restyle_in, f'f{k}.png'))
    restyle_out = os.path.join(folder, 'restyle_out')
    if all(os.path.exists(os.path.join(restyle_out, f'r{k}.png')) for k in range(1, 9)):
        body[1:] = [pb.snap(Image.open(os.path.join(restyle_out, f'r{k}.png')).convert('RGBA'), palette)
                    for k in range(1, 9)]
    # 색감 기준 (같은 날 사용자: 2·3타 색감이 좀 다름): 서기 그림 한 장이 아니라 완성된 1타 8장 전체의 색 분포에 맞춘다
    tone_ref = Image.new('RGBA', (68 * 8, 68), (0, 0, 0, 0))
    for k, c in enumerate(b.cells(v2_sheet(), 0)[1:9]):
        tone_ref.alpha_composite(c, (k * 68, 0))
    body = [body[0]] + [v2.despeckle(c) for c in v2.match_tones(body[1:], tone_ref)]
    for k, src in cfg.get('reuse', {}).items():
        body[k] = body[src].copy()
    for k, src in cfg.get('legs', {}).items():
        body[k] = swap_legs(body[k], body[src])
    for k, arc_args in cfg['swoosh'] or []:
        if arc_args[0] == 'front':
            arc = front_smear(hit, arc_args[1], body[k].size)
        else:
            arc = bp.swoosh(body[k].size, *arc_args)  # 잔상은 몸 뒤 (뒷모습이라 칼은 몸 너머)
        arc.alpha_composite(no_blue(body[k]))  # 파란 칼날은 지우고 게임에서 칼을 따로 그림 (잔상만 파랑)
        body[k] = arc
    print(hit, 'scale', round(scale, 3))
    return body


def main():
    ref = Image.open(os.path.join(HERE, '..', 'kit', 'ref_back_nosword_64.png')).convert('RGBA')
    palette = pf.game_palette()
    sheet = Image.new('RGBA', (68 * 9, 68 * 2), (0, 0, 0, 0))
    for row, hit in enumerate((2, 3)):
        for k, cell in enumerate(build(hit, ref, palette)):
            sheet.alpha_composite(cell, (k * 68, row * 68))
    sheet.save(os.path.join(b.RAW, OUT))
    prev = Image.new('RGBA', sheet.size, (128, 128, 128, 255))
    prev.alpha_composite(sheet)
    prev.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(KIT, 'hit23_v2_sheet_x4.png'))


if __name__ == '__main__':
    main()
