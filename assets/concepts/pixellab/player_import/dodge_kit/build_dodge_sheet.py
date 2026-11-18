"""회피 시트 만들기 (2026-11-18): 핵심 자세(ChatGPT, build_dodge_keys.py) 사이를 PixelLab(animate_image, 시작·끝 지정)이 채운
pl_out2/<view>_<a|b>_<0..4>.png 에서 고른 프레임을 정리해 이어 붙인다.
  a = 웅크림 → 돌진, b = 돌진 → 미끄러져 멈춤, c = 멈춤 → 서기 (0 = 시작 자세, 4 = 끝 자세)
정리: 게임 주인공 색에서 먼 픽셀(PixelLab 이 그린 흰 섬광·빛줄기)은 지우고 나머지는 가장 가까운 게임 색으로,
몸과 떨어진 작은 덩어리는 지우고, 발(아래 4줄) 가운데·발 밑을 핵심 자세와 같은 자리에 맞춘다.
출력: dodge_<view>_64x48.png (가로 한 줄), 미리보기 dodge_preview_slow.gif / dodge_preview_realtime.gif
실행: python build_dodge_sheet.py
"""
import sys
from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_parry_front as pf  # noqa: E402

# 2차(2026-11-18 사용자 지적: 망토 이상·화질 뭉개짐): 또렷하게 줄인 핵심 자세로 사이를 다시 채운 pl_out2/ 를 쓴다.
# 일어서는 구간은 몸이 늘어나 빼고, 끝나면 바로 서 있는 그림으로 돌아간다.
OUT_DIR = 'pl_out2'
# 3차(2026-11-18 사용자: 더 다듬기): 정면 b1·b2 는 망토가 날개처럼 양옆으로 뻗어 빼고, 후면은 같은 장 두 번을 없앤다.
# 후면 b1~b3 은 PixelLab 이 머리 위에 흰 연기를 덮어 지우면 후드가 깨져 앞 구간만 쓴다.
PICK = {
    'front': ['a0', 'a1', 'a3', 'a4', 'b3', 'b4'],
    'side': ['a0', 'a2', 'a4', 'b1', 'b3', 'b4'],
    'back': ['a0', 'a1', 'a2', 'a3', 'a4', 'b4'],
}
FAR = 70  # 게임 색과 이보다 멀면 지움 (RGB 거리)
MIN_PART = 40  # 몸(가장 큰 덩어리)과 떨어진 이보다 작은 덩어리는 지움 (흰 섬광이 색 맞춤으로 남은 조각)


def clean(im, palette):
    im = im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3] < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            p = min(palette, key=lambda q: sum((q[i] - c[i]) ** 2 for i in range(3)))
            d = sum((p[i] - c[i]) ** 2 for i in range(3)) ** 0.5
            px[x, y] = (0, 0, 0, 0) if d > FAR else p + (255,)
    # 덩어리 나누기: 가장 큰 덩어리(몸)와 붙지 않은 작은 덩어리는 지운다
    seen, parts = set(), []
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] and (x, y) not in seen:
                part, q = [], deque([(x, y)])
                seen.add((x, y))
                while q:
                    a, b = q.popleft()
                    part.append((a, b))
                    for na in (a - 1, a, a + 1):
                        for nb in (b - 1, b, b + 1):
                            if 0 <= na < im.width and 0 <= nb < im.height and (na, nb) not in seen and px[na, nb][3]:
                                seen.add((na, nb))
                                q.append((na, nb))
                parts.append(part)
    body = max(parts, key=len)  # noqa: (아래에서 외톨이 픽셀·테두리 정리)
    bx0, bx1 = min(a for a, _ in body) - 2, max(a for a, _ in body) + 2
    by0, by1 = min(b for _, b in body) - 2, max(b for _, b in body) + 2
    for part in parts:
        if part is body:
            continue
        inside = any(bx0 <= a <= bx1 and by0 <= b <= by1 for a, b in part)
        if len(part) < MIN_PART or not inside:  # 작거나 몸 둘레 밖에 떨어진 조각 (섬광·빛줄기가 남은 것)
            for a, b in part:
                px[a, b] = (0, 0, 0, 0)
    return outline(im, palette)


def outline(im, palette):
    """외톨이 픽셀(이웃이 1개 이하)을 지우고, 실루엣 가장자리(투명과 맞닿은 픽셀)를 게임 그림처럼 가장 어두운 색 한 줄로.
    PixelLab 사이 동작의 끊긴 테두리·흩어진 점을 원본(GPT 핵심 자세·게임 그림)처럼 깔끔하게 (2026-11-18 사용자: 다듬기)."""
    ink = min(palette, key=lambda c: sum(c)) + (255,)
    px = im.load()
    w, h = im.size
    solid = lambda x, y: 0 <= x < w and 0 <= y < h and px[x, y][3] > 0  # noqa: E731
    for y in range(h):
        for x in range(w):
            if solid(x, y) and sum(solid(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)) - 1 <= 1:
                px[x, y] = (0, 0, 0, 0)
    edge = [(x, y) for y in range(h) for x in range(w) if solid(x, y)
            and not all(solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        px[x, y] = ink
    return im


def feet(im):
    px = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3]]
    bottom = max(y for _, y in pts)
    xs = [x for x, y in pts if y >= bottom - 3]
    return (min(xs) + max(xs)) / 2, bottom


def build(view, palette):
    key = Image.open(HERE / 'pl_in' / f'{view}_crouch.png').convert('RGBA')
    kfx, kfy = feet(key)
    frames = []
    for name in PICK[view]:
        im = clean(Image.open(HERE / OUT_DIR / f'{view}_{name[0]}_{name[1]}.png'), palette)
        fx, fy = feet(im)
        c = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        c.alpha_composite(im, (round(kfx - fx), round(kfy - fy)))
        frames.append(c.crop((0, 12, 64, 60)))  # 64×48: 핵심 자세를 놓은 자리 (pl_in 은 64×48 을 y 12 에 둠)
    sheet = Image.new('RGBA', (64 * len(frames), 48), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * 64, 0))
    sheet.save(HERE / f'dodge_{view}_64x48.png')
    return frames


def main():
    palette = pf.game_palette()
    allf = {v: build(v, palette) for v in ('front', 'side', 'back')}
    n = len(PICK['front'])
    idle = {v: Image.open(HERE.parents[4] / f'assets/images/player/idle/{v}.png').convert('RGBA').crop((0, 0, 32, 48))
            for v in allf}

    def strip(get):
        im = Image.new('RGBA', (64 * 3 + 40, 48), (40, 40, 48, 255))
        for i, v in enumerate(('front', 'side', 'back')):
            im.alpha_composite(get(v), (i * 84, 0))
        return im.resize((im.width * 4, im.height * 4), Image.NEAREST)

    def idle_cell(v):
        c = Image.new('RGBA', (64, 48), (0, 0, 0, 0))
        c.alpha_composite(idle[v], (16, 0))
        return c

    seq = [strip(idle_cell)] + [strip(lambda v, k=k: allf[v][k]) for k in range(n)] + [strip(idle_cell)]
    seq[0].save(HERE / 'dodge_preview_slow.gif', save_all=True, append_images=seq[1:],
                duration=[400] + [160] * n + [500], loop=0)
    seq[0].save(HERE / 'dodge_preview_realtime.gif', save_all=True, append_images=seq[1:],
                duration=[400] + [36] * n + [500], loop=0)
    contact = Image.new('RGBA', (64 * n, 48 * 3), (128, 128, 128, 255))
    for r, v in enumerate(('front', 'side', 'back')):
        for k in range(n):
            contact.alpha_composite(allf[v][k], (k * 64, r * 48))
    contact.resize((contact.width * 3, contact.height * 3), Image.NEAREST).save(HERE / 'dodge_contact_x3.png')
    print('ok', n)


if __name__ == '__main__':
    main()
