"""후면 공격(1·2·3타) 시트 만들기 (2026-11-18).

PixelLab 은 후면을 제대로 못 그려, 사용자가 ChatGPT 로 타마다 8자세(2줄 × 4)를 받았다
(attack_back_kit/README.txt, result_hit<N>.png: 회색 배경, 칼과 잔상은 파란 단색).
1. 회색 배경을 바깥에서 채워 지우고, 두 줄 × 네 자세를 잘라 8자세로 (왼쪽 위부터).
2. 첫 자세(서기)의 키를 게임 뒷모습 키에 맞춰 같은 배율로 줄인다. 픽셀 덩어리 가운데 색을 집는다(NEAREST, 뭉개지지 않게).
3. 파란 픽셀은 파란색 하나로, 나머지는 게임 주인공 색 중 가장 가까운 색으로.
4. 발 밑 가운데를 게임 뒷모습과 같은 자리에 맞춰 64×64 에 놓는다.
5. 칸 0 = 게임 뒷모습, 1~8 = 8자세. 타마다 한 줄 (1타 0행, 2타 1행, 3타 2행).
출력: remake_raw/attack_back_gpt_68.png. export_to_game.py 가 읽는다 (VIEW_ATTACKS['back']).
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_parry_back as pb  # noqa: E402  (배경 지우기·색 맞춤·발 위치)
import build_parry_front as pf  # noqa: E402  (게임 팔레트)

RAW = os.path.join(HERE, 'remake_raw')
KIT = os.path.join(HERE, 'attack_back_kit')


def split_rows(im):
    """가로 줄(위아래로 떨어진 두 줄)로 나눈다."""
    a = im.getchannel('A').load()
    rows = [any(a[x, y] for x in range(im.width)) for y in range(im.height)]
    runs, start = [], None
    for y, r in enumerate(rows + [False]):
        if r and start is None:
            start = y
        elif not r and start is not None:
            runs.append((start, y))
            start = None
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:2])
    return [im.crop((0, y0, im.width, y1)) for y0, y1 in runs]


def poses(hit):
    im = pb.remove_bg(Image.open(os.path.join(KIT, f'result_hit{hit}.png')))
    out = []
    for row in split_rows(im):
        out += pb.split4(row)
    return out


def main():
    ref = Image.open(os.path.join(HERE, '..', 'kit', 'ref_back_nosword_64.png')).convert('RGBA')
    palette = pf.game_palette()
    rfx, rfy = pb.feet(ref)
    x0, y0, x1, y1 = ref.getchannel('A').getbbox()
    cx, foot = (x0 + x1) // 2, y1 - 1
    sheet = Image.new('RGBA', (68 * 9, 68 * 3), (0, 0, 0, 0))
    for r, hit in enumerate((1, 2, 3)):
        ps = poses(hit)
        assert len(ps) == 8, (hit, len(ps))
        scale = (y1 - y0) / pb.body_height(ps[0])
        cells = [ref]
        for p in ps:
            small = pb.snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.NEAREST),
                            palette)
            fx, fy = pb.feet(small)
            c = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            c.alpha_composite(small, (round(rfx - fx), round(rfy - fy)))
            cells.append(c)
        for k, f in enumerate(cells):
            big = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
            big.alpha_composite(f, (40, 40))
            sheet.alpha_composite(big.crop((40 + cx - 34, 40 + foot - 58, 40 + cx + 34, 40 + foot + 10)),
                                  (k * 68, r * 68))
        print('hit', hit, 'scale', round(scale, 3))
    sheet.save(os.path.join(RAW, 'attack_back_gpt_68.png'))
    prev = Image.new('RGBA', sheet.size, (128, 128, 128, 255))
    prev.alpha_composite(sheet)
    prev.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(KIT, 'attack_back_sheet_x3.png'))


if __name__ == '__main__':
    main()
