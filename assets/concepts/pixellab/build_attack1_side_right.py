"""B(PixelLab) 프레임의 몸 움직임에 게임 원본 후드를 입히고 원본 팔레트로 맞춘다.

공격 1타 오른쪽 그림(attack1_side_right_v4.png) 제작 스크립트. Pillow 필요(게임 실행에는 필요 없음).
사용: 이 폴더(assets/concepts/pixellab)에서 `python build_attack1_side_right.py <출력 폴더>`
     → <출력 폴더>/hyb_strip.png (5프레임 시트), hyb.png (4배 확대 확인용)
"""
import sys
from PIL import Image, ImageFilter
SP = sys.argv[1]
idle = Image.open('../../images/player/idle/side.png').convert('RGBA').crop((0, 0, 32, 48))
ref = Image.open('kit/ref_side_right_sword_64.png').convert('RGBA')
PAL = sorted({p[:3] for p in ref.getdata() if p[3]})
HEAD = idle.crop((0, 0, 32, 21))
# (B 파일, 원본 머리를 놓을 위치)
PLAN = [('frame_2.png', (10, 9)), ('frame_3_fixed.png', (17, 11)),
        ('frame_4_fixed.png', (23, 19)), ('frame_6.png', (24, 18))]


def snap(p):
    r, g, b = p[:3]
    return min(PAL, key=lambda c: (c[0] - r) ** 2 * 2 + (c[1] - g) ** 2 * 4 + (c[2] - b) ** 2 * 3)


def build(fname, pos):
    b = Image.open('attack1_side_right_B/' + fname).convert('RGBA')
    bp = b.load()
    orig = b.copy().load()
    head = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    head.paste(HEAD, pos, HEAD)
    # 원본 머리 실루엣을 넓혀 B 후드를 지울 영역으로 사용
    mask = head.split()[3].point(lambda a: 255 if a else 0).filter(ImageFilter.MaxFilter(5))
    mp = mask.load()
    face_bottom = pos[1] + 20
    blade = {(x, y) for x in range(64) for y in range(64) if bp[x, y][3] and bp[x, y][0] > 180}
    for y in range(64):
        for x in range(64):
            if mp[x, y] and y <= face_bottom and (x, y) not in blade:
                bp[x, y] = (0, 0, 0, 0)
    hp_ = head.load()
    # 망토 자락이 후드 뒤에 이어지도록, 후드 뒤쪽 아래 영역의 B 픽셀은 되살림
    for y in range(pos[1] + 9, face_bottom + 1):
        for x in range(0, pos[0] + 9):
            if orig[x, y][3] and not hp_[x, y][3]:
                bp[x, y] = orig[x, y]
    # 앞으로 숙인 프레임: 원본 후드 앞쪽에 남은 B 후드 지우기
    if pos[1] >= 18:
        for y in range(0, face_bottom - 1):
            for x in range(pos[0] + 23, 64):
                if (x, y) not in blade:
                    bp[x, y] = (0, 0, 0, 0)
    out = b.copy()
    out.alpha_composite(head)
    op = out.load()
    # 후드 앞을 지나는 칼날은 다시 위로
    for x, y in blade:
        if head.load()[x, y][3]:
            op[x, y] = bp[x, y]
    for y in range(64):
        for x in range(64):
            if op[x, y][3] and not head.load()[x, y][3]:
                op[x, y] = snap(op[x, y]) + (255,)
    return out


CAPE = [(0x12, 0x0C, 0x11), (0x4A, 0x31, 0x33), (0x5C, 0x37, 0x36), (0x62, 0x3D, 0x3B), (0x66, 0x40, 0x3D), (0x6C, 0x43, 0x3F)]


def recolor_cape(img, x_max, y0, y1):
    """검은 망토를 원본 갈색 망토 색으로: 가장자리는 외곽선, 안쪽은 밝기 순서대로."""
    p = img.load()
    for y in range(y0, y1 + 1):
        for x in range(0, x_max + 1):
            c = p[x, y]
            if not c[3]:
                continue
            edge = any(not p[x + dx, y + dy][3] for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            lum = sum(c[:3])
            if edge and x < x_max - 2:
                p[x, y] = CAPE[0] + (255,)
            elif lum < 200:
                idx = 1 + min(4, lum * 5 // 200)
                p[x, y] = CAPE[idx] + (255,)


frames = [build(f, p) for f, p in PLAN]
recolor_cape(frames[0], 19, 27, 44)
recolor_cape(frames[1], 25, 26, 38)
fp = frames[0].load()
for y in range(29, 35):
    for x in range(29, 40):
        if fp[x, y][3] and fp[x, y][0] > 140:
            fp[x, y] = (0x24, 0x17, 0x1D, 255)
OUTL = (0x12, 0x0C, 0x11, 255)
LEATHER = (0x3C, 0x25, 0x2B, 255)


def thicken_legs(img, y0, x0, x1):
    """다리 영역을 좌우로 1픽셀씩 넓힌다: 새 가장자리는 외곽선, 옛 외곽선은 안쪽 색."""
    src = img.copy().load()
    p = img.load()
    opaque = lambda x, y: 0 <= x < 64 and src[x, y][3] > 0
    dark = lambda c: sum(c[:3]) < 100
    light = {(x, y) for x in range(64) for y in range(y0 - 2, 64) if src[x, y][3] and src[x, y][0] > 150}
    blade = {(x + dx, y + dy) for x, y in light for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for y in range(y0, 64):
        for x in range(x0, x1):
            if opaque(x, y) and (x, y) not in blade:
                for d in (-1, 1):
                    if not opaque(x + d, y) and (x + d, y) not in blade:
                        inner = src[x - d, y] if opaque(x - d, y) else LEATHER
                        if dark(src[x, y]):
                            p[x, y] = LEATHER if dark(inner) else inner
                        p[x + d, y] = OUTL
            
            
thicken_legs(frames[0], 44, 8, 44)
thicken_legs(frames[1], 40, 8, 48)
thicken_legs(frames[2], 44, 8, 50)
thicken_legs(frames[3], 44, 8, 50)
frames.append(ref.copy())
strip = Image.new('RGBA', (320, 64), (0, 0, 0, 0))
for i, f in enumerate(frames):
    strip.alpha_composite(f, (64 * i, 0))
strip.save(SP + '/hyb_strip.png')
sheet = Image.new('RGBA', (260 * 5, 256), (90, 110, 90, 255))
for i, f in enumerate(frames):
    sheet.alpha_composite(f.resize((256, 256), Image.NEAREST), (260 * i, 0))
sheet.save(SP + '/hyb.png')
