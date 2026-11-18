"""후면 두 손 내려찍기(slam_north) 다시 만들기 (2026-11-18 사용자 요청: 후면에서 내려찍고 팔이 먼저 돌아오는 문제).

- 들기 0~6: 지금 그림 그대로 (사용자: 들기는 괜찮음).
- 착지·일어섬 7~13: ChatGPT 핵심 자세(keys/north_slam, north_rise, process_results.py)와
  PixelLab v3 사이 동작(pixellab/rise_*: 내려찍기 → 일어서기, pixellab/stand_*: 일어서기 → 서기, 시작·끝 자세 지정).
  rise_* 에는 PixelLab 이 흰·하늘색 불꽃을 그려 넣어, 그 색(밝거나 푸른 픽셀)을 지우고 작은 점을 버린다.
  모두 게임 뒷모습 색으로 맞추고, 두 발(아래 6줄) 가운데·발 밑을 FOOT 에 맞춘다.
- 밝기 분포를 원본 뒷모습에 맞춘다 (match_tone, 7~12장).
- 7~12장 안을 원본 뒷모습 부위로 다시 짜 맞춘다 (parts/compose.py, 2026-11-18 사용자 요청: 질감 차이).
- 끝 장(13)은 지금 그림의 끝 장(서 있는 자세, 들기 첫 장과 같음)을 그대로 써서 서 있는 그림으로 이어진다.

순서: 7 내려찍기(키) / 8 rise_1 / 9 rise_2 / 10 일어서기(키) / 11 stand_1 / 12 stand_2 / 13 서기(지금 그림)
(stand_3·4 는 PixelLab 이 조금 크게 그려 끝 장과 크기가 튀어 쓰지 않는다)
출력: ../aligned/slam_north.png (게임: assets/images/golem/slam_north.png 로 복사), slam_north_new_preview.gif
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE))
from process_results import CANVAS, FOOT, feet_center, palette_of, snap  # noqa: E402

GAME = ROOT / "assets/images/golem/slam_north.png"
MIN_SPECK = 60


def frames_of(sheet: Image.Image) -> list[Image.Image]:
    w, h = CANVAS
    return [sheet.crop((i * w, 0, i * w + w, h)) for i in range(sheet.width // w)]


def strip_flame(im: Image.Image) -> Image.Image:
    im = im.copy()
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and (max(r, g, b) > 185 or b - r > 40):
                px[x, y] = (0, 0, 0, 0)
    return im


def drop_specks(im: Image.Image) -> Image.Image:
    """MIN_SPECK 픽셀보다 작은 떨어진 덩어리를 지운다 (불꽃을 지우고 남은 부스러기)."""
    im = im.copy()
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    for sy in range(h):
        for sx in range(w):
            if seen[sy * w + sx] or not px[sx, sy][3]:
                continue
            blob, q = [], deque([(sx, sy)])
            seen[sy * w + sx] = 1
            while q:
                x, y = q.popleft()
                blob.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny][3]:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            if len(blob) < MIN_SPECK:
                for x, y in blob:
                    px[x, y] = (0, 0, 0, 0)
    return im


def luma(c) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def match_tone(im: Image.Image, ref: Image.Image) -> Image.Image:
    """밝기 순서를 그대로 두고, 밝기 분포를 게임 뒷모습 그림과 같게 바꾼다 (2026-11-18 사용자 지적: 원본과 질감 차이).

    프레임의 불투명 픽셀을 밝기 순으로 늘어놓고, 같은 비율 자리의 원본 픽셀 색으로 바꾼다.
    자세·모양은 그대로이고 어두운 외곽선·그늘·하이라이트의 비율이 원본과 같아진다.
    """
    ref_cols = sorted((p for p in ref.get_flattened_data() if p[3]), key=luma)
    im = im.copy()
    px = im.load()
    pts = sorted(((x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3]), key=lambda q: luma(px[q]))
    n = len(pts)
    new = [ref_cols[min(len(ref_cols) - 1, int(i / n * len(ref_cols)))] for i in range(n)]
    for q, c in zip(pts, new):
        px[q] = c
    return im


def place(im: Image.Image, pal) -> Image.Image:
    im = drop_specks(snap(im.convert("RGBA"), pal))
    fx, fy = feet_center(im)
    c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    c.alpha_composite(im, (round(FOOT[0] - fx), FOOT[1] - fy))
    return c


def main() -> None:
    old = frames_of(Image.open(GAME).convert("RGBA"))
    pal = palette_of(Image.open(ROOT / "assets/images/golem/north.png"))
    pl = lambda name: Image.open(HERE / "pixellab" / f"{name}.png").convert("RGBA")  # noqa: E731
    key = lambda name: Image.open(HERE / "keys" / f"north_{name}.png").convert("RGBA")  # noqa: E731
    recover = [
        key("slam"),
        place(strip_flame(pl("rise_1")), pal),
        place(strip_flame(pl("rise_2")), pal),
        key("rise"),
        place(pl("stand_1"), pal),
        place(pl("stand_2"), pal),
        old[13],
    ]
    ref = Image.open(ROOT / "assets/images/golem/north.png").convert("RGBA")
    recover = [match_tone(f, ref) for f in recover[:-1]] + recover[-1:]
    frames = old[:7] + recover
    sheet = Image.new("RGBA", (CANVAS[0] * len(frames), CANVAS[1]), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * CANVAS[0], 0))
    # 7~12장 안을 원본 뒷모습 부위(다리·어깨·머리·등)로 다시 짜 맞춘다 (실루엣은 그대로, parts/compose.py)
    sys.path.insert(0, str(HERE / "parts"))
    from compose import compose_sheet  # noqa: E402
    sheet = compose_sheet(sheet)
    frames = [sheet.crop((i * CANVAS[0], 0, (i + 1) * CANVAS[0], CANVAS[1])) for i in range(len(frames))]
    sheet.save(HERE.parent / "aligned" / "slam_north.png")
    bg = []
    for f in frames:
        b = Image.new("RGBA", CANVAS, (60, 60, 70, 255))
        b.alpha_composite(f)
        bg.append(b.resize((CANVAS[0] * 3, CANVAS[1] * 3), Image.NEAREST))
    bg[0].save(HERE / "slam_north_new_preview.gif", save_all=True, append_images=bg[1:],
               duration=[90] * 7 + [250, 110, 110, 110, 110, 110, 400], loop=0)
    print("ok", sheet.size)


if __name__ == "__main__":
    main()
