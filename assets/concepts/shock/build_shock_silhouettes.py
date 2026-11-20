"""감전 그림 (2026-11-20 사용자: 감전되면 만화처럼 검정색 됐다가 하얀색 됐다가 찌릿찌릿).

서 있는 그림의 모양(알파)만 살려 검은 그림자·흰 그림 두 벌을 만든다. 게임은 감전 동안 이 둘과 원래 그림을 번갈아 그린다.
- 골렘: golem/<방향>.png (96×96, 방향마다 따로 그림) → golem/shock_<방향>_black.png, _white.png
- 허수아비: dummy/stage<k>.png (망가진 단계 0~2) → dummy/stage<k>_black.png (흰 그림은 맞았을 때 쓰는 stage<k>_white.png 를 같이 씀)

카툰 뼈·전기 테두리 (같은 날 사용자: 흑백 전환은 좋은데 안쪽에 뼈 같은 게 보이면 재밌겠다, 감전을 더 확실하고 직관적으로):
- 뼈: 엑스레이처럼 몸 안에 해골·척추·갈비뼈·골반·팔다리 뼈. 방향마다 손으로 자리를 정하고 몸 모양 안쪽으로 자른다.
  검은 그림자 위에는 밝은 뼈(<이름>_bones_light.png), 흰 그림 위에는 진한 뼈(<이름>_bones_dark.png).
- 전기 테두리: 몸 바깥 1 픽셀 하늘색 + 그 밖 1 픽셀 파랑 (<이름>_rim.png). 감전 동안 깜빡이며 몸을 감쌈.
- 파란 몸 (<이름>_charge.png): 방전 직전 안의 전기가 모이며 몸이 파랗게 달아오를 때 겹쳐 그림 (불투명도로 세기).
"""
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.normpath(os.path.join(HERE, '..', '..', 'images'))
BLACK = (22, 20, 32)
WHITE = (244, 248, 255)
BONE_LIGHT = ((240, 246, 255), (164, 190, 228))  # (뼈, 뼈 그늘·이음매)
BONE_DARK = ((40, 44, 70), (96, 108, 150))
RIM = ((150, 232, 255), (70, 120, 255))  # (안쪽 테두리, 바깥 테두리)
CHARGE = (96, 180, 255)  # 방전 직전 몸이 파랗게 달아오르는 그림 (같은 날 사용자: 안의 전기가 방출되는 느낌)


def silhouette(src: str, dst: str, colour) -> None:
    im = Image.open(src).convert('RGBA')
    out = Image.new('RGBA', im.size, colour + (0,))
    px, a = out.load(), im.getchannel('A').load()
    for y in range(out.height):
        for x in range(out.width):
            px[x, y] = colour + (a[x, y],)
    out.save(dst)


# ----- 뼈 그리기 (원본 픽셀 좌표, 캔버스 왼쪽 위 기준) -----
class Bones:
    def __init__(self, size):
        self.im = Image.new('L', size, 0)  # 1 = 뼈, 2 = 그늘·이음매, 3 = 구멍(눈·코)
        self.d = ImageDraw.Draw(self.im)

    def bone(self, p, q, w=2):
        self.d.line([p, q], fill=1, width=w)
        for x, y in (p, q):  # 마디: 끝을 둥글게 불룩
            self.d.ellipse([x - w / 2 - 0.5, y - w / 2 - 0.5, x + w / 2 + 0.5, y + w / 2 + 0.5], fill=1)

    def skull(self, cx, cy, rx, ry, face=True, side=0):
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=1)
        self.d.rectangle([cx - rx * 0.55, cy + ry * 0.55, cx + rx * 0.55, cy + ry + 2], fill=1)  # 턱
        if not face:
            self.d.line([(cx, cy - ry + 2), (cx, cy + ry - 1)], fill=2)  # 뒤통수 이음매
            return
        if side:  # 옆모습: 눈 하나, 코, 이빨
            ex = cx + side * rx * 0.35
            self.d.ellipse([ex - 2, cy - 2, ex + 2, cy + 2], fill=3)
            self.d.point([(cx + side * rx * 0.8, cy + ry * 0.35)], fill=3)
        else:
            for ex in (cx - rx * 0.42, cx + rx * 0.42):
                self.d.ellipse([ex - 2.4, cy - 2.2, ex + 2.4, cy + 2.2], fill=3)
            self.d.polygon([(cx, cy + ry * 0.25), (cx - 1, cy + ry * 0.5), (cx + 1, cy + ry * 0.5)], fill=3)
        for k in range(-2, 3):  # 이빨 사이 금
            x = cx + k * rx * 0.2 + side * rx * 0.2
            self.d.line([(x, cy + ry * 0.62), (x, cy + ry + 1)], fill=2)

    def spine(self, x, y0, y1, side=0):
        for y in range(int(y0), int(y1), 3):
            self.d.rectangle([x - 1, y, x + 1, y + 1], fill=1)
            self.d.point([(x, y + 2)], fill=2)

    def ribs(self, cx, y0, y1, half, side=0):
        n = max(3, int((y1 - y0) / 4))
        for k in range(n):
            y = y0 + (y1 - y0) * k / (n - 1)
            h = half * (1 - 0.25 * abs(k - n * 0.4) / n)
            if side:  # 옆모습: 등뼈에서 앞으로 휘어 내려가는 짧은 갈비
                self.d.line([(cx, y), (cx + side * h * 0.8, y + 1), (cx + side * h * 1.3, y + 3)], fill=1, width=1)
                continue
            self.d.arc([cx - h, y - 3, cx + h, y + 5], 200, 340, fill=1, width=2)

    def pelvis(self, cx, y, half):
        self.d.ellipse([cx - half, y - half * 0.45, cx + half, y + half * 0.55], fill=1)
        self.d.ellipse([cx - half * 0.35, y - half * 0.1, cx + half * 0.35, y + half * 0.45], fill=3)

    def paint(self, mask_src, colours, dst):
        """몸 모양 안쪽(테두리 1 픽셀 안)만 남겨 색을 입힌다."""
        alpha = Image.open(mask_src).convert('RGBA').getchannel('A').load()
        w, h = self.im.size
        inside = lambda x, y: 0 <= x < w and 0 <= y < h and alpha[x, y] > 100  # noqa: E731
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        src, px = self.im.load(), out.load()
        bone, shade = colours
        for y in range(h):
            for x in range(w):
                v = src[x, y]
                if v in (0, 3) or not all(inside(x + dx, y + dy) for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                edge = any(src[x + dx, y + dy] in (0, 3) for dx, dy in ((1, 0), (0, 1))
                           if 0 <= x + dx < w and 0 <= y + dy < h)
                px[x, y] = (shade if v == 2 or edge else bone) + (255,)
        out.save(dst)


def golem_front(b: Bones, face: bool):
    b.skull(48, 20, 11, 10, face=face)
    b.spine(48, 33, 62)
    b.ribs(48, 36, 54, 14)
    b.pelvis(48, 64, 11)
    for s in (-1, 1):
        sx = 48 + s * 22
        b.bone((48 + s * 8, 34), (sx, 34), 2)  # 빗장뼈
        b.bone((sx, 36), (48 + s * 30, 56), 3)  # 위팔
        b.bone((48 + s * 30, 58), (48 + s * 33, 72), 3)  # 아래팔
        b.d.ellipse([48 + s * 33 - 4, 72, 48 + s * 33 + 4, 79], fill=1)  # 주먹 뼈
        b.bone((48 + s * 8, 68), (48 + s * 12, 78), 3)  # 넓적다리
        b.bone((48 + s * 12, 80), (48 + s * 13, 86), 3)  # 정강이


def golem_side(b: Bones, side: int):
    cx = 48 + side * 2
    b.skull(cx + side * 3, 18, 10, 9, side=side)
    b.spine(cx, 30, 62)
    b.ribs(cx, 34, 54, 9, side=side)
    b.pelvis(cx, 64, 7)
    b.bone((cx - side * 6, 34), (cx - side * 8, 52), 3)  # 위팔 (몸 앞쪽 팔)
    b.bone((cx - side * 8, 54), (cx - side * 6, 70), 3)
    b.d.ellipse([cx - side * 6 - 4, 69, cx - side * 6 + 4, 76], fill=1)
    b.bone((cx - 2, 68), (cx - 3, 85), 3)
    b.bone((cx + 4, 68), (cx + 5, 85), 3)


def dummy_bones(b: Bones):
    b.skull(24, 8, 5, 5)
    b.bone((9, 19), (39, 19), 2)  # 팔 (가로대)
    for x in (9, 39):
        b.d.ellipse([x - 2, 17, x + 2, 21], fill=1)
    b.spine(24, 14, 46)
    b.ribs(24, 22, 32, 7)


def rim(src: str, dst: str) -> None:
    alpha = Image.open(src).convert('RGBA').getchannel('A').load()
    im = Image.open(src)
    w, h = im.size
    body = {(x, y) for y in range(h) for x in range(w) if alpha[x, y] > 100}
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = out.load()
    near = lambda x, y, r: any((x + dx, y + dy) in body for dx in range(-r, r + 1) for dy in range(-r, r + 1)  # noqa: E731
                               if abs(dx) + abs(dy) <= r)
    for y in range(h):
        for x in range(w):
            if (x, y) in body:
                continue
            if near(x, y, 1):
                px[x, y] = RIM[0] + (255,)
            elif near(x, y, 2):
                px[x, y] = RIM[1] + (220,)
    out.save(dst)


def main():
    for view in ('south', 'north', 'east', 'west'):
        src = os.path.join(IMAGES, 'golem', f'{view}.png')
        base = os.path.join(IMAGES, 'golem', f'shock_{view}')
        silhouette(src, base + '_black.png', BLACK)
        silhouette(src, base + '_white.png', WHITE)
        silhouette(src, base + '_charge.png', CHARGE)
        b = Bones((96, 96))
        if view in ('south', 'north'):
            golem_front(b, face=view == 'south')
        else:
            golem_side(b, 1 if view == 'east' else -1)
        b.paint(src, BONE_LIGHT, base + '_bones_light.png')
        b.paint(src, BONE_DARK, base + '_bones_dark.png')
        rim(src, base + '_rim.png')
    for k in range(3):
        src = os.path.join(IMAGES, 'dummy', f'stage{k}.png')
        base = os.path.join(IMAGES, 'dummy', f'stage{k}')
        silhouette(src, base + '_black.png', BLACK)
        silhouette(src, base + '_charge.png', CHARGE)
        b = Bones(Image.open(src).size)
        dummy_bones(b)
        b.paint(src, BONE_LIGHT, base + '_bones_light.png')
        b.paint(src, BONE_DARK, base + '_bones_dark.png')
        rim(src, base + '_rim.png')
    print('shock silhouettes, bones, rims')


if __name__ == '__main__':
    main()
