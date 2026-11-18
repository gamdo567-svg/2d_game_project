"""후면 1타 3차 시트 (2026-11-18): ChatGPT 가 정면 1타 8장을 "뒤에서 본 같은 순간"으로 그린 그림
(attack_back_kit/hit1_v2/result_hit1_back.png, 한 줄 8자세, 칼은 파란 단색)을 게임 크기로.
build_attack_back.py 와 같은 방법: 배경 제거 → 8자세 자르기 → 첫 자세 키를 게임 뒷모습에 맞춰 NEAREST 로 줄임
→ 색 맞춤(파랑은 그대로) → 발 맞춤. 5번째(판정)에는 칼이 지나간 길대로 큰 초승달 잔상을 몸 위에 겹친다
(build_attack_back_pl.swoosh). 출력: remake_raw/attack_back_v2_68.png 0행 (칸 0 = 게임 뒷모습).
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_attack_back_pl as bp  # noqa: E402  (초승달 잔상)
import build_parry_back as pb  # noqa: E402
import build_parry_front as pf  # noqa: E402
import build_remake_preview as b  # noqa: E402

SRC = os.path.join(HERE, 'attack_back_kit', 'hit1_v2', 'result_hit1_back.png')
# 화풍 맞추기 (같은 날 사용자: GPT 픽셀 그림체가 게임과 다름): 줄인 8장(잔상 없이, restyle_in/f1~8)을 PixelLab transfer_outfit 에
# 게임 뒷모습(f0)을 참고로 넘겨 자세는 그대로 두고 게임 화풍으로 다시 그린 것(restyle_out/r1~8). 있으면 이것을 쓴다.
RESTYLE = os.path.join(HERE, 'attack_back_kit', 'hit1_v2', 'restyle_out')
# 판정 장(8장 중 번호)의 잔상: (원 중심 x, y, 반지름, 시작 각도, 끝 각도, 두께). 칼은 오른쪽 위 → 왼쪽 아래
SWOOSH = (4, (22, 20, 36, -20, 112, 8))


def match_tones(cells, ref):
    """색감 맞추기 (같은 날 사용자: 여전히 색감과 분위기가 다름): 8장 몸 색(파랑 제외)을 밝기 순서로 줄 세워, 게임 뒷모습
    서기 그림(ref) 색을 같은 비율 자리(분위수)에 대응시킨다. 쓰는 색과 명암 분포가 서기 그림과 같아진다."""
    def lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    def ramp(images):
        counts = {}
        for im in images:
            for p in im.get_flattened_data():
                if p[3] == 255 and not b.is_blue(p):
                    counts[p[:3]] = counts.get(p[:3], 0) + 1
        cols = sorted(counts, key=lum)
        total = sum(counts.values())
        out, acc = [], 0
        for c in cols:  # (색, 이 색이 차지하는 분위 구간의 가운데)
            out.append((c, (acc + counts[c] / 2) / total))
            acc += counts[c]
        return out

    src, dst = ramp(cells), ramp([ref])
    mapping = {}
    for c, q in src:
        mapping[c] = min(dst, key=lambda d: abs(d[1] - q))[0]
    out = []
    for im in cells:
        im = im.copy()
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                p = px[x, y]
                if p[3] == 255 and not b.is_blue(p):
                    px[x, y] = mapping[p[:3]] + (255,)
        out.append(im)
    return out


def split_n(im, n=8):
    w, h = im.size
    a = im.getchannel('A').load()
    cols = [sum(1 for y in range(h) if a[x, y]) > 1 for x in range(w)]
    runs, start = [], None
    for x, c in enumerate(cols + [False]):
        if c and start is None:
            start = x
        elif not c and start is not None:
            runs.append((start, x))
            start = None
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:n])
    out = []
    for x0, x1 in runs:
        c = im.crop((x0, 0, x1, h))
        out.append(c.crop(c.getbbox()))
    return out


def main():
    ref = Image.open(os.path.join(HERE, '..', 'kit', 'ref_back_nosword_64.png')).convert('RGBA')
    palette = pf.game_palette()
    rfx, rfy = pb.feet(ref)
    x0, y0, x1, y1 = ref.getchannel('A').getbbox()
    cx, foot = (x0 + x1) // 2, y1 - 1
    poses = split_n(pb.remove_bg(Image.open(SRC)))
    assert len(poses) == 8, len(poses)
    scale = (y1 - y0) / pb.body_height(poses[0])
    cells = [ref]
    for k, p in enumerate(poses):
        small = pb.snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.NEAREST),
                        palette)
        fx, fy = pb.feet(small)
        c = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        c.alpha_composite(small, (round(rfx - fx), round(rfy - fy)))
        cells.append(c)
    # 화풍 맞춘 그림(restyle_out)이 있으면 먼저 그것으로 바꾸고, 색감을 서기 그림에 맞춘다
    body = []
    for k, f in enumerate(cells):
        big = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
        big.alpha_composite(f, (40, 40))
        cell = big.crop((40 + cx - 34, 40 + foot - 58, 40 + cx + 34, 40 + foot + 10))
        restyled = os.path.join(RESTYLE, f'r{k}.png')
        if k > 0 and os.path.exists(restyled):
            cell = pb.snap(Image.open(restyled).convert('RGBA'), palette)  # 같은 68 칸 자리로 돌려받음
        body.append(cell)
    body = [body[0]] + match_tones(body[1:], body[0])
    sheet = Image.new('RGBA', (68 * 9, 68), (0, 0, 0, 0))
    for k, cell in enumerate(body):
        if k - 1 == SWOOSH[0]:
            cell.alpha_composite(bp.swoosh(cell.size, *SWOOSH[1]))  # 판정 장: 몸 위로 이어지는 잔상
        sheet.alpha_composite(cell, (k * 68, 0))
    sheet.save(os.path.join(b.RAW, 'attack_back_v2_68.png'))
    prev = Image.new('RGBA', sheet.size, (128, 128, 128, 255))
    prev.alpha_composite(sheet)
    prev.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(
        os.path.join(HERE, 'attack_back_kit', 'hit1_v2', 'sheet_x3.png'))
    print('scale', round(scale, 3))


if __name__ == '__main__':
    main()
