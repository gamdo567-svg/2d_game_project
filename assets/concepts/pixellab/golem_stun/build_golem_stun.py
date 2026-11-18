"""골렘 기절 동작 그림을 게임 시트로 만든다 (2026-11-18).

입력 (방향 south / east / north, 서쪽은 동쪽을 좌우 반전):
  pixellab/in_<dir>_0..4.png    서기 → 휘청 (PixelLab, ChatGPT 휘청 자세를 끝 자세로 지정)
  pixellab/drop_<dir>_0..4.png  휘청 → 한쪽 무릎 (0 은 휘청, 4 는 무릎)
  pixellab/out_<dir>_0..4.png   무릎 → 서기 (0 은 무릎)
처리:
  1. PixelLab 이 머리 위에 그려 넣은 기절 빙글 효과(하늘색·흰 고리)를 지운다. 게임은 별 이펙트를 따로 그린다.
     몸 = 효과 색(밝거나 채도 높은 색)을 뺀 가장 큰 덩어리, 그 실루엣 안(구멍 포함)의 픽셀만 남긴다
     → 코어·눈처럼 몸 안의 밝은 픽셀은 남고, 몸 밖의 효과는 지워진다.
  2. 발 밑(가장 아래 불투명 줄)의 가운데를 CANVAS 의 FOOT 에 맞춘다 (구간마다 캔버스 크기가 달라서).
출력: assets/images/golem/stun_<dir>.png (가로 한 줄 FRAMES 장), stun_4dir_preview.gif
  장 순서: 서기→휘청 0~2 / 휘청→무릎 3~6 / 무릎→서기 7~10 (무릎 = 6)
실행: python build_golem_stun.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = HERE / "pixellab"
OUT = ROOT / "assets" / "images" / "golem"
CANVAS = (144, 152)
FOOT = (72, 140)
# 서기→휘청의 1·2번째는 PixelLab 이 머리 위에 기절 소용돌이를 몸에 붙여 그렸거나(측면·후면) 머리가 떠 있어(정면)
# 지울 수 없어 뺀다. 네 방향 모두 같은 장을 써서 장 번호를 맞춘다.
ORDER = [("in", i) for i in (0, 3, 4)] + [("drop", i) for i in range(1, 5)] + [("out", i) for i in range(1, 5)]
FRAMES = len(ORDER)


def is_effect_color(c) -> bool:
    """기절 효과 색: 아주 밝거나(흰 고리) 채도가 높은 색(하늘색). 골렘 돌은 회색이다."""
    r, g, b = c[:3]
    return min(r, g, b) > 200 or max(r, g, b) - min(r, g, b) > 45


def components(points: set) -> list[set]:
    out, seen = [], set()
    for p in points:
        if p in seen:
            continue
        comp, stack = set(), [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            comp.add((x, y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in points and q not in seen:
                        seen.add(q)
                        stack.append(q)
        out.append(comp)
    return out


def clean(frame: Image.Image) -> Image.Image:
    w, h = frame.size
    px = frame.load()
    solid = {(x, y) for y in range(h) for x in range(w) if px[x, y][3] and not is_effect_color(px[x, y])}
    body = max(components(solid), key=len)
    # 실루엣: 몸 바깥을 테두리에서부터 채우고, 닿지 않은 곳(몸과 몸 안의 구멍)이 실루엣
    outside, stack = set(), [(0, 0)]
    while stack:
        x, y = stack.pop()
        if (x, y) in outside or (x, y) in body or not (0 <= x < w and 0 <= y < h):
            continue
        outside.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    out = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and (x, y) not in outside:
                opx[x, y] = px[x, y]
    return out


def foot_of(frame: Image.Image) -> tuple[int, int]:
    """발 밑 가운데: 가장 아래 불투명 줄과, 아래 6줄에 있는 픽셀의 가로 가운데."""
    w, h = frame.size
    px = frame.load()
    bottom = max(y for y in range(h) for x in range(w) if px[x, y][3])
    xs = [x for y in range(bottom - 5, bottom + 1) for x in range(w) if px[x, y][3]]
    return (min(xs) + max(xs)) // 2, bottom


def build(view: str) -> list[Image.Image]:
    frames = []
    for seg, i in ORDER:
        src = clean(Image.open(SRC / f"{seg}_{view}_{i}.png").convert("RGBA"))
        fx, fy = foot_of(src)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(src, (FOOT[0] - fx, FOOT[1] - fy))
        frames.append(canvas)
    return frames


def main() -> None:
    views = {v: build(v) for v in ("south", "east", "north")}
    views["west"] = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in views["east"]]
    for view, frames in views.items():
        sheet = Image.new("RGBA", (CANVAS[0] * FRAMES, CANVAS[1]), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.alpha_composite(f, (i * CANVAS[0], 0))
        sheet.save(OUT / f"stun_{view}.png")
    # 미리보기: 네 방향 나란히, 무릎은 잠깐 버팀
    seq = list(range(7)) + [6] * 6 + list(range(7, FRAMES)) + [0] * 3
    bg = (40, 44, 52, 255)
    gif = []
    for i in seq:
        im = Image.new("RGBA", (CANVAS[0] * 4, CANVAS[1]), bg)
        for k, view in enumerate(("south", "east", "north", "west")):
            im.alpha_composite(views[view][i], (k * CANVAS[0], 0))
        gif.append(im.convert("RGB"))
    big = Image.new("RGB", (gif[0].width, gif[0].height * len(gif)))
    for k, im in enumerate(gif):
        big.paste(im, (0, k * gif[0].height))
    pal = big.quantize(colors=256, method=Image.MEDIANCUT, dither=0)
    frames = [pal.crop((0, k * gif[0].height, gif[0].width, (k + 1) * gif[0].height)) for k in range(len(gif))]
    frames[0].save(HERE / "stun_4dir_preview.gif", save_all=True, append_images=frames[1:], duration=120, loop=0)
    print("saved", [f"stun_{v}.png" for v in views], (CANVAS[0] * FRAMES, CANVAS[1]))


if __name__ == "__main__":
    main()
