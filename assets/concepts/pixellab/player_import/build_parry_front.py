"""정면 패링 시트 만들기 (2026-11-18 사용자 결정: 측면 패링을 기준으로 다시 그린 C안).

입력: remake_raw/parry_front_ready_CD_sheet_64.png 1행(C안) = 당긴 자세(칼을 세움) → 쳐올림 → 막기 ×3.
측면과 같은 순서로 고른다: 당김, 쳐올림, 막기, 막기, 당김. 막기는 PixelLab 이 불꽃 점을 넣지 않은 마지막 장.
색: PixelLab 이 몸을 조금 다른 갈색·검정으로 칠해 측면보다 어둡게 보여서(사용자 지적), 파란 칼을 뺀 몸 픽셀을
지금 게임 주인공 그림(측면 패링·정면 공격 시트)에 있는 색 중 가장 가까운 색으로 바꾼다. 모양은 그대로.
출력: remake_raw/parry_front_sheet_68.png (칸 0 = 서 있는 정면, 1~5 = 위 순서). export_to_game.py 가 읽는다.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_remake_preview as b  # noqa: E402

RAW = os.path.join(HERE, 'remake_raw')
ROOT = b.ROOT
PICK = [0, 1, 4, 4, 0]


def game_palette():
    colors = set()
    for path in ('assets/images/player/parry/side.png', 'assets/images/player/sword_attack/front_1.png',
                 'assets/images/player/sword_attack/front_2.png'):
        im = Image.open(os.path.join(ROOT, path)).convert('RGBA')
        colors |= {p[:3] for p in im.getdata() if p[3] == 255}
    return sorted(colors)


def snap(frame, palette):
    out = frame.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if not c[3] or b.is_blue(c):
                continue
            near = min(palette, key=lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2)
            px[x, y] = near + (255,)
    return out


def main():
    src = Image.open(os.path.join(RAW, 'parry_front_ready_CD_sheet_64.png')).convert('RGBA')
    idle = Image.open(os.path.join(HERE, '..', 'kit', 'ref_front_nosword_64.png')).convert('RGBA')
    palette = game_palette()
    frames = [idle] + [snap(src.crop((i * 64, 0, i * 64 + 64, 64)), palette) for i in PICK]
    x0, y0, x1, y1 = idle.getchannel('A').getbbox()
    cx, foot = (x0 + x1) // 2, y1 - 1
    sheet = Image.new('RGBA', (68 * len(frames), 68), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        big = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
        big.alpha_composite(f, (40, 40))
        sheet.alpha_composite(big.crop((40 + cx - 34, 40 + foot - 58, 40 + cx + 34, 40 + foot + 10)), (k * 68, 0))
    sheet.save(os.path.join(RAW, 'parry_front_sheet_68.png'))
    print('palette', len(palette), 'saved', sheet.size)


if __name__ == '__main__':
    main()
