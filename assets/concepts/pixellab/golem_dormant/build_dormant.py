"""골렘 휴면·깨어남 그림과 어그로 ! 아이콘 내보내기 (2026-11-20 사용자 요청: 몬스터 어그로 시스템).

휴면: 코어가 꺼지고 깊게 웅크려 머리를 어깨 사이에 묻은 모습 (PixelLab edit_image, 4방향 한 번에) + 회색빛 (여기서 색을 빼고 어둡게).
깨어남: 휴면 → 평소 서 있는 그림으로 코어가 켜지며 고개를 드는 9장 (PixelLab animate_image, 시작·끝 지정, 방향마다).
  회색빛은 장마다 조금씩 빠져 마지막 장은 평소 색. 후면은 PixelLab 이 몸 둘레에 빛 테두리를 그려 몸 윤곽 밖 픽셀은 지운다.
! 아이콘: 붉은 느낌표 (픽셀로 직접 그림, 진한 테두리·밝은 하이라이트).
출력: assets/images/golem/dormant_<방향>.png (96×96), wake_<방향>.png (96×96 × 9), assets/images/effects/aggro_mark.png
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
# 2차 (같은 날 사용자: 휴면이 서 있는 모습과 거의 같음 → 깊게 웅크린 자세). 1차는 이 폴더 바로 아래 파일들.
# 서쪽 휴면은 PixelLab 이 반대쪽을 보게 그려 동쪽을 좌우로 뒤집어 씀 (dormant_west_pixellab.png 는 버린 것).
SRC = os.path.join(HERE, 'v2')
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
GOLEM = os.path.join(ROOT, 'assets', 'images', 'golem')
EFFECTS = os.path.join(ROOT, 'assets', 'images', 'effects')
VIEWS = ('south', 'east', 'north', 'west')
FRAMES = 9  # f0 = 휴면, f8 = 평소 서 있는 그림
GREY = 0.6  # 휴면 회색빛: 색을 이만큼 빼고
DIM = 0.82  # 이만큼 어둡게


def greyed(im, amount):
    """amount 0 = 원래 색, 1 = 휴면 회색빛."""
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            k = GREY * amount
            f = 1 - (1 - DIM) * amount
            px[x, y] = tuple(min(255, round((c + (lum - c) * k) * f)) for c in (r, g, b)) + (a,)
    return out


def body_mask(*images):
    xs = set()
    for im in images:
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y][3]:
                    xs.add((x, y))
    return xs


def keep_inside(im, mask, idle):
    """몸 윤곽 밖 픽셀은 지우고, 윤곽 안의 밝은 빛 테두리 픽셀은 평소 그림 픽셀로 바꾼다."""
    out = im.copy()
    px, ipx = out.load(), idle.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if not c[3]:
                continue
            if (x, y) not in mask:
                px[x, y] = (0, 0, 0, 0)
            elif 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] > 150:
                px[x, y] = ipx[x, y] if ipx[x, y][3] else (0, 0, 0, 0)
    return out


def exclamation():
    """붉은 ! (7×16): 진한 테두리, 붉은 몸, 밝은 하이라이트."""
    rows = [
        '.ooooo.',
        'oRRRRRo',
        'oRhRRRo',
        'oRhRRRo',
        'oRRRRRo',
        '.oRRRo.',
        '.oRRRo.',
        '.oRRRo.',
        '..oRo..',
        '..oRo..',
        '..ooo..',
        '.......',
        '..ooo..',
        '.oRRRo.',
        '.oRRRo.',
        '..ooo..',
    ]
    colors = {'o': (60, 8, 10, 255), 'R': (226, 44, 40, 255), 'h': (255, 170, 150, 255)}
    im = Image.new('RGBA', (7, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors:
                im.putpixel((x, y), colors[ch])
    return im


def main():
    for view in VIEWS:
        idle = Image.open(os.path.join(GOLEM, f'{view}.png')).convert('RGBA')
        dormant = Image.open(os.path.join(SRC, f'dormant_{view}.png')).convert('RGBA')
        greyed(dormant, 1.0).save(os.path.join(GOLEM, f'dormant_{view}.png'))
        frames = [Image.open(os.path.join(SRC, f'wake_{view}', f'f{i}.png')).convert('RGBA') for i in range(FRAMES)]
        if view == 'north':  # 몸 둘레 빛 테두리 지우기
            mask = body_mask(idle, dormant)
            frames = [keep_inside(f, mask, idle) for f in frames]
        sheet = Image.new('RGBA', (96 * FRAMES, 96), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.alpha_composite(greyed(f, 1 - i / (FRAMES - 1)), (i * 96, 0))
        sheet.save(os.path.join(GOLEM, f'wake_{view}.png'))
    mark = exclamation()
    mark.save(os.path.join(EFFECTS, 'aggro_mark.png'))
    white = Image.new('RGBA', mark.size, (0, 0, 0, 0))  # 번쩍임용 흰 실루엣
    for y in range(mark.height):
        for x in range(mark.width):
            if mark.getpixel((x, y))[3]:
                white.putpixel((x, y), (255, 255, 255, 255))
    white.save(os.path.join(EFFECTS, 'aggro_mark_white.png'))
    print('ok')


if __name__ == '__main__':
    main()
