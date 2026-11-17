"""골렘 걷기 4방향 프레임 정리 (PixelLab skeleton-v3 'walking-8-frames', 보폭 0.85·팔 흔들기 0.6).

2026-11-17 사용자 지적으로 방식 변경: 처음 시도(v3 자유 동작, 기본 템플릿, '한 발 든 자세' 반전)는
정면·후면이 쩍벌로 걷거나 측면이 막대처럼 가늘어지거나 걸음이 끊겼다. skeleton-v3 는 골렘 뼈대에 정해진
걷기 동작(왼발·오른발이 번갈아 나오는 8장)을 따라 그려 덩치·색이 유지되고 걸음 주기가 깔끔하다.

모든 장을 같은 캔버스(CANVAS)에 놓고, 방향마다 8장 전체의 '평균 발 밑'을 FOOT 에 맞춘다
(걷는 동안 몸이 위아래로 출렁이는 것은 그대로 둔다).

입력: skeleton_4dir.png (8장 × 4줄, 128×128: south, east, north, west)
출력: aligned/walk_<dir>.png (가로 한 줄 8장), walk_preview.gif (1.5칸/초로 칸 위를 이동, 2배 확대)
실행: python build_golem_walk.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "aligned"
SRC, CELL = HERE / "skeleton_4dir.png", 128
ROWS = ("south", "east", "north", "west")
FRAMES = 8
CANVAS = (128, 128)
FOOT = (64, 118)  # 발 밑 가운데 (캔버스 안 픽셀, 위에서부터)
TILES_PER_CYCLE = 2.0  # 8장 한 주기(왼발 + 오른발)에 걷는 칸 수


def load() -> dict[str, list[Image.Image]]:
    im = Image.open(SRC).convert("RGBA")
    return {name: [im.crop((i * CELL, r * CELL, i * CELL + CELL, r * CELL + CELL)) for i in range(FRAMES)]
            for r, name in enumerate(ROWS)}


def place(frames: list[Image.Image]) -> list[Image.Image]:
    """8장의 가로 가운데·발 밑 평균을 FOOT 에 맞춰 모두 같은 양만큼 옮긴다."""
    boxes = [f.getbbox() for f in frames]
    cx = sum((b[0] + b[2]) / 2 for b in boxes) / len(boxes)
    bottom = max(b[3] for b in boxes)  # 딛고 있는 발이 닿는 가장 아래 줄
    dx, dy = round(FOOT[0] - cx), FOOT[1] - bottom
    out = []
    for f in frames:
        c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        c.alpha_composite(f, (dx, dy))
        out.append(c)
    return out


def preview(sets: dict[str, list[Image.Image]]) -> None:
    T, cols, rows, speed, fps = 32, 8, 6, 1.5, 24
    floor = Image.new("RGBA", (cols * T, rows * T), (88, 84, 80, 255))
    d = ImageDraw.Draw(floor)
    for x in range(0, cols * T, T):
        for y in range(0, rows * T, T):
            d.rectangle((x, y, x + T - 1, y + T - 1), outline=(76, 72, 68, 255))
    moves = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
    starts = {"east": (1.0, 3.5), "west": (7.0, 3.5), "south": (4.0, 1.2), "north": (4.0, 5.6)}
    out = []
    for name in ("east", "south", "west", "north"):
        frames = sets[name]
        for k in range(round(fps * 4 / speed)):
            dist = k / fps * speed
            idx = int(dist / TILES_PER_CYCLE * FRAMES) % FRAMES
            (mx, my), (sx, sy) = moves[name], starts[name]
            world = floor.copy()
            world.alpha_composite(frames[idx], (round((sx + mx * dist) * T - FOOT[0]),
                                                round((sy + my * dist) * T - FOOT[1])))
            ImageDraw.Draw(world).text((4, 4), f"walk {name}", fill=(255, 255, 255, 255))
            out.append(world.resize((world.width * 2, world.height * 2), Image.NEAREST))
    out[0].save(HERE / "walk_preview.gif", save_all=True, append_images=out[1:], duration=round(1000 / fps), loop=0)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    sets = {name: place(frames) for name, frames in load().items()}
    for name, frames in sets.items():
        strip = Image.new("RGBA", (CANVAS[0] * FRAMES, CANVAS[1]), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            strip.paste(f, (i * CANVAS[0], 0))
        strip.save(OUT / f"walk_{name}.png")
        boxes = [f.getbbox() for f in frames]
        print(name, "범위", min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    preview(sets)


if __name__ == "__main__":
    main()
