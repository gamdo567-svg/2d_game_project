"""골렘 ① 두 손 내려찍기 4방향 프레임 정리 + 충격 이펙트 미리보기.

2026-11-17 사용자 지적으로 다시 그림: 처음 시안은 방향마다 동작이 달랐다(정면은 다리 고정, 측면·후면은 다리를 움직임,
후면은 손이 등에 가려지지 않음). 그래서 PixelLab 핵심 자세 두 장(`Slam Raise`: 두 주먹을 머리 위로, 발 고정 /
`Slam Impact`: 상체를 숙여 주먹을 앞 땅에, 후면은 손이 가려짐)을 4방향 state 로 만들고 구간을 이었다.

입력: keypose_<dir>_frames.png = join 결과 19장 (들기 0~6, 내려찍기 7~11, 일어섬 12~18). 칸 크기는 SIZES.
- 내려찍기 사이 장(8~10)에는 PixelLab 이 흰 섬광·궤적을 그려 넣어 쓰지 않는다. 들기 끝(6) → 착지(11) 한 장 만에 떨어진다.
- 일어섬 첫 장(12)은 착지(11)와 같은 자세라 뺀다.
- 구간마다 캔버스가 달라, 구간 첫 장을 앞 구간 마지막 장(같은 자세)의 발 밑에 맞춰 옮긴다 (발 구르기와 같은 방법).
- 4방향 모두 CANVAS 에 첫 장의 발 밑 가운데를 FOOT 에 맞춰 놓는다.

출력: aligned/slam_<dir>.png (가로 한 줄 14장: 들기 0~6, 착지 7, 일어섬 8~13), slam_4dir_preview.gif
실행: python build_golem_slam.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "aligned"
# 방향별 원본: (파일, 칸 크기, 구간, 쓸 장)
# 정면은 처음 다시 그린 것(19장: 들기 / 내려찍기 / 일어섬). 측면·후면은 착지 자세를 다시 만듦
# ('Slam Impact Flat': 등을 곧게 펴고 숙여 팔·주먹이 보이게, 후면은 머리가 어깨 아래로 내려가고 양팔이 보이게.
#  2026-11-17 사용자 지적: 측면 등이 갑자기 볼록, 후면이 내려찍는 동작으로 안 보임) → 14장: 들기 0~6 / 착지·일어섬 7~13.
SOUTH = ("keypose_south_frames.png", (124, 140), [(0, 7), (7, 12), (12, 19)], [0, 1, 2, 3, 4, 5, 6, 11, 13, 14, 15, 16, 17, 18])
FLAT_CLIPS, FLAT_KEEP = [(0, 7), (7, 14)], list(range(14))
SOURCES = {
    "south": SOUTH,
    "east": ("flat_east_frames.png", (132, 164), FLAT_CLIPS, FLAT_KEEP),
    # 후면 일어섬은 팔이 먼저 옆으로 돌아가 다시 만듦 (pixminimax: 팔은 아래로 뻗은 채 등이 천천히 펴지고 머리가 올라옴).
    # 16장 (들기 0~6 / 착지·일어섬 7~15) 중 일어섬 8장에서 6장을 고른다.
    "north": ("flat_north_b_frames.png", (116, 164), [(0, 7), (7, 16)], list(range(8)) + [8, 9, 11, 12, 14, 15]),
    "west": ("flat_west_frames.png", (128, 156), FLAT_CLIPS, FLAT_KEEP),
}
IMPACT = 7  # 착지 장 (모든 방향 같은 자리)
CANVAS = (144, 176)
FOOT = (72, 166)


def load(name: str) -> list[Image.Image]:
    path, (w, h), clips, _ = SOURCES[name]
    im = Image.open(HERE / path).convert("RGBA")
    cols = im.width // w
    count = clips[-1][1]
    return [im.crop(((i % cols) * w, (i // cols) * h, (i % cols) * w + w, (i // cols) * h + h)) for i in range(count)]


def foot(b):
    return (b[0] + b[2]) / 2, b[3]


def align(frames: list[Image.Image], clips, keep) -> list[Image.Image]:
    offsets = [(0, 0)] * len(frames)
    for k, (start, end) in enumerate(clips):
        shift = (0, 0)
        if k == len(clips) - 1:
            # 마지막(일어섬) 구간은 끝 장이 첫 장과 같은 서 있는 자세: 그 둘을 맞춘다.
            # (숙인 착지 자세는 팔이 앞으로 뻗어 가로 가운데로 맞추면 옆으로 밀림)
            (px, py), (cx, cy) = foot(frames[0].getbbox()), foot(frames[end - 1].getbbox())
            shift = (round(px - cx), py - cy)
        elif k > 0:
            (px, py), (cx, cy) = foot(frames[start - 1].getbbox()), foot(frames[start].getbbox())
            prev = offsets[start - 1]
            shift = (round(prev[0] + px - cx), prev[1] + py - cy)
        for i in range(start, end):
            offsets[i] = shift
    fx, fy = foot(frames[0].getbbox())
    base = (round(FOOT[0] - fx), FOOT[1] - fy)
    out = []
    for i in keep:
        c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        c.alpha_composite(frames[i], (base[0] + offsets[i][0], base[1] + offsets[i][1]))
        out.append(c)
    return out


def build() -> dict[str, list[Image.Image]]:
    OUT.mkdir(exist_ok=True)
    sets = {name: align(load(name), SOURCES[name][2], SOURCES[name][3]) for name in SOURCES}
    for name, frames in sets.items():
        strip = Image.new("RGBA", (CANVAS[0] * len(frames), CANVAS[1]), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            strip.paste(f, (i * CANVAS[0], 0))
        strip.save(OUT / f"slam_{name}.png")
        boxes = [f.getbbox() for f in frames]
        print(name, "범위", min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
              max(b[3] for b in boxes), "처음/끝 발", foot(boxes[0]), foot(boxes[-1]))
    return sets


def preview(sets: dict[str, list[Image.Image]]) -> None:
    sys.path.insert(0, str(ROOT / "assets/concepts/vfx/slam"))
    import build_golem_slam_impact as fx  # noqa: E402
    FX = fx.main()
    T, N, SC, TICK = 32, 8, 2, 1 / 24
    SZ = N * T
    facing = {"south": (0, 1), "east": (1, 0), "north": (0, -1), "west": (-1, 0)}  # 화면 기준 (y 아래로 +)
    floor = Image.new("RGBA", (SZ, SZ), (88, 84, 80, 255))
    d = ImageDraw.Draw(floor)
    for x in range(0, SZ, T):
        for y in range(0, SZ, T):
            d.rectangle((x, y, x + T - 1, y + T - 1), outline=(76, 72, 68, 255))
    seq = []
    for i in range(IMPACT):  # 들기
        seq += [(i, None)] * 2
    seq += [(IMPACT - 1, None)] * 4  # 위에서 멈춤
    k = 0
    for gi in [IMPACT] * 4 + [8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13]:  # 쾅(멈칫) → 일어섬
        seq.append((gi, round(k * TICK * fx.FPS)))
        k += 1
    while round(k * TICK * fx.FPS) < len(FX):
        seq.append((13, round(k * TICK * fx.FPS)))
        k += 1
    seq += [(0, None)] * 8
    shake = [(0, 0), (3, -1), (-3, 1), (2, 0), (-1, 0)]
    out = []
    for gi, fi in seq:
        sheet = Image.new("RGBA", (SZ * 2, SZ * 2), (30, 28, 32, 255))
        for n, name in enumerate(("south", "east", "north", "west")):
            world = floor.copy()
            gx, gy = SZ // 2, SZ // 2 + T  # 2×2 바닥 가운데 (발 밑)
            mx, my = facing[name]
            ex, ey = SZ // 2 + round(mx * 1.6 * T), SZ // 2 + round(my * 1.6 * T)  # 손이 닿는 곳
            if fi is not None and fi < len(FX):
                world.alpha_composite(FX[fi], (ex - fx.C, ey - fx.C))
            world.alpha_composite(sets[name][gi], (gx - FOOT[0], gy - FOOT[1]))
            ImageDraw.Draw(world).text((4, 4), name, fill=(255, 255, 255, 255))
            sh = shake[fi] if fi is not None and fi < len(shake) else (0, 0)
            screen = Image.new("RGBA", (SZ, SZ), (30, 28, 32, 255))
            screen.alpha_composite(world, sh)
            sheet.paste(screen, ((n % 2) * SZ, (n // 2) * SZ))
        out.append(sheet.resize((SZ * 2 * SC, SZ * 2 * SC), Image.NEAREST))
    out[0].save(HERE / "slam_4dir_preview.gif", save_all=True, append_images=out[1:],
                duration=round(TICK * 1000), loop=0)


if __name__ == "__main__":
    preview(build())
