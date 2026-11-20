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


# 옆모습 (같은 날 사용자 지적: 깨어나는 옆모습에 등이 비정상적으로 튀어나옴). PixelLab 은 옆으로 웅크리면 등 뒤에 없는 돌덩이를
# 덧붙여서, 골렘이 돌덩이를 이어 붙인 몸이라는 점을 살려 원래 그림의 덩어리를 직접 옮겨 웅크린다 (몸 크기·모양 그대로).
# 동쪽(오른쪽을 봄) 기준 덩어리 (원본 좌표): 머리 y<24 또는 (y<31, x≥50), 팔(어깨·팔뚝·주먹) x<46 이고 24≤y<80, 다리 y≥66 이고 x≥44 또는 y≥80, 나머지 몸통.
# k=1 (휴면)일 때 옮김 (앞쪽 +, 아래 +): 몸통 (2, 6), 팔 (3, 8), 머리 (6, 12). 그리는 순서: 다리 → 몸통 → 머리 → 팔.
SIDE_SHIFT = {'torso': (2, 6), 'arm': (3, 8), 'head': (6, 12)}
SIDE_WAKE = ((1.0, 'off'), (1.0, 'off'), (1.0, 'on'), (1.0, 'off'), (0.9, 'on'), (0.7, 'on'), (0.42, 'on'), (0.15, 'on'),
             (0.0, 'on'))  # 장마다 (웅크림 정도, 코어): 코어가 깜빡이며 켜진 뒤 덩어리가 일어섬


def side_part(x, y, mirror):
    xe = 95 - x if mirror else x  # 서쪽은 좌우를 뒤집은 좌표로 판정
    if y < 24 or (y < 31 and xe >= 50):  # 머리 (그 아래 왼쪽은 어깨 돌덩이 꼭대기라 팔로)
        return 'head'
    if y >= 80 or (y >= 66 and xe >= 44):
        return 'legs'
    if xe < 46 and 24 <= y < 80:
        return 'arm'
    return 'torso'


def fill_holes(im):
    """덩어리를 옮기며 몸 안에 생긴 투명 틈(바깥과 이어지지 않은 빈 픽셀)을 둘레의 가장 어두운 색으로 메운다
    (같은 날 사용자: 웅크린 옆모습의 머리·어깨 사이 작은 틈). 돌 사이 이음매처럼 보이게."""
    out = im.copy()
    px = out.load()
    w, h = out.size
    edge = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    stack = [p for p in edge if px[p][3] == 0]
    outside = set(stack)
    while stack:
        x, y = stack.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= n[0] < w and 0 <= n[1] < h and n not in outside and px[n][3] == 0:
                outside.add(n)
                stack.append(n)
    holes = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 0 and (x, y) not in outside]
    for _ in range(4):  # 넓은 틈은 바깥쪽부터 몇 번에 걸쳐 메움
        rest = []
        for x, y in holes:
            near = [px[n] for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                    if 0 <= n[0] < w and 0 <= n[1] < h and px[n][3]]
            if near:
                px[x, y] = min(near, key=lambda c: c[0] + c[1] + c[2])
            else:
                rest.append((x, y))
        holes = rest
    return out


def crouch_side(base, k, mirror):
    """옆모습 덩어리를 k(0~1)만큼 웅크린 자세로 옮겨 다시 쌓는다."""
    layers = {n: Image.new('RGBA', base.size, (0, 0, 0, 0)) for n in ('legs', 'torso', 'head', 'arm')}
    src = base.load()
    for y in range(base.height):
        for x in range(base.width):
            if src[x, y][3]:
                layers[side_part(x, y, mirror)].putpixel((x, y), src[x, y])
    out = Image.new('RGBA', base.size, (0, 0, 0, 0))
    for name in ('legs', 'torso', 'head', 'arm'):
        dx, dy = SIDE_SHIFT.get(name, (0, 0))
        dx = round(dx * k) * (-1 if mirror else 1)
        out.alpha_composite(layers[name], (dx, round(dy * k)))
    return fill_holes(out)


def side_frames(view):
    """옆모습 휴면 1장 + 깨어남 9장. 코어 꺼진 그림 = 1차 휴면(서 있는 자세에 코어만 꺼짐), 켜진 그림 = 서 있는 그림."""
    mirror = view == 'west'
    off = Image.open(os.path.join(HERE, f'dormant_{view}.png')).convert('RGBA')
    on = Image.open(os.path.join(GOLEM, f'{view}.png')).convert('RGBA')
    dormant = crouch_side(off, 1.0, mirror)
    wake = [crouch_side(on if core == 'on' else off, k, mirror) for k, core in SIDE_WAKE]
    return dormant, wake


def main():
    for view in VIEWS:
        if view in ('east', 'west'):
            dormant, frames = side_frames(view)
            greyed(dormant, 1.0).save(os.path.join(GOLEM, f'dormant_{view}.png'))
            sheet = Image.new('RGBA', (96 * FRAMES, 96), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                sheet.alpha_composite(greyed(f, 1 - i / (FRAMES - 1)), (i * 96, 0))
            sheet.save(os.path.join(GOLEM, f'wake_{view}.png'))
            continue
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
