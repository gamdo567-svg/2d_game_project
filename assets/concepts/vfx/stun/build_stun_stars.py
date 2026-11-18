"""기절 공용 이펙트: 머리 위에서 별이 원을 그리며 돈다 (2026-11-18 사용자 요청, 주인공·적 공용).

64×40 칸 16장 가로 한 줄, 반복 재생. 가운데 (32, 20) 이 링 가운데 (머리 꼭대기 조금 위에 놓는다).
- 납작한 타원 링(위에서 내려다본 원): 옅은 노랑 점선, 앞쪽(아래쪽 반)이 더 밝다.
- 노란 별 3개가 링을 따라 돈다. 뒤쪽(위쪽 반)을 지날 때는 작고 어둡게, 앞쪽은 크고 밝게 (원근감).
- 별 사이에 작은 반짝이가 깜빡인다.
그리는 크기는 쓰는 쪽이 정한다 (골렘은 크게, 주인공은 작게).

출력: assets/images/effects/stun_stars.png, 이 폴더 stun_stars_preview.gif
실행: python build_stun_stars.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent
GAME = OUT.parents[2] / "images" / "effects"
W, H = 64, 40
FRAMES = 16
CX, CY = W / 2, H / 2
RX, RY = 24, 8

K = (40, 26, 8, 255)       # 별 외곽선 (어두운 갈색)
Y1 = (255, 244, 150, 255)  # 별 밝은 노랑
Y2 = (255, 214, 64, 255)   # 별 노랑
Y3 = (214, 150, 30, 255)   # 별 그늘 (주황)
R_FRONT = (255, 240, 170, 255)
R_BACK = (190, 160, 90, 255)
SPARK = (255, 255, 235, 255)

BIG = ["..K..",
       ".KYK.",
       "KYWYK",
       ".KYK.",
       "K.K.K"]
STAR9 = ["....K....",
         "...KYK...",
         "...KWK...",
         "KKKYWYKKK",
         ".KYWWWYK.",
         "..KYYYK..",
         "..KYKYK..",
         ".KYK.KYK.",
         ".KK...KK."]
STAR7 = ["...K...",
         "..KWK..",
         "KKYWYKK",
         ".KYYYK.",
         "..YYY..",
         ".KY.YK.",
         ".K...K."]
SMALL = [".K.",
         "KYK",
         ".K."]


def put(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), c)


def stamp(img, pattern, x, y, front: bool):
    h, w = len(pattern), len(pattern[0])
    colors = {"K": K, "W": Y1 if front else Y2, "Y": Y2 if front else Y3}
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch in colors:
                put(img, x - w // 2 + i, y - h // 2 + j, colors[ch])


def frame(f: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t = f / FRAMES
    # 링: 점선, 시간에 따라 점이 돌아간다
    for k in range(64):
        a = 2 * math.pi * k / 64
        if (k + f) % 4 == 3:
            continue
        x, y = CX + RX * math.cos(a), CY + RY * math.sin(a)
        put(img, x, y, R_FRONT if math.sin(a) > 0 else R_BACK)
    # 별 3개: 뒤쪽 먼저, 앞쪽 나중에 그린다
    stars = []
    for s in range(3):
        a = 2 * math.pi * (t + s / 3)
        stars.append((math.sin(a), a))
    for depth, a in sorted(stars):
        x, y = CX + RX * math.cos(a), CY + RY * math.sin(a) - 2
        if depth > 0.35:
            stamp(img, STAR9, x, y, True)
        elif depth > -0.35:
            stamp(img, STAR7, x, y, depth > 0)
        else:
            stamp(img, BIG, x, y, False)
    # 반짝이: 링 위 두 자리에서 번갈아 깜빡
    for k, a0 in enumerate((0.9, 3.6)):
        if (f // 2 + k) % 3 == 0:
            x, y = CX + (RX + 2) * math.cos(a0 + t * 2), CY + (RY + 2) * math.sin(a0 + t * 2) - 3
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                put(img, x + dx, y + dy, SPARK if (dx, dy) == (0, 0) else Y1)
    return img


def main() -> None:
    frames = [frame(f) for f in range(FRAMES)]
    sheet = Image.new("RGBA", (W * FRAMES, H), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        sheet.alpha_composite(fr, (i * W, 0))
    GAME.mkdir(parents=True, exist_ok=True)
    sheet.save(GAME / "stun_stars.png")
    golem = Image.open(OUT.parents[2] / "images" / "golem" / "south.png").convert("RGBA")
    seq = []
    for fr in frames:
        im = Image.new("RGBA", (120, 120), (40, 40, 50, 255))
        im.alpha_composite(golem, (12, 26))
        im.alpha_composite(fr, (28, 6))
        seq.append(im.resize((360, 360), Image.NEAREST))
    seq[0].save(OUT / "stun_stars_preview.gif", save_all=True, append_images=seq[1:], duration=70, loop=0, disposal=2)
    print("ok", sheet.size)


if __name__ == "__main__":
    main()
