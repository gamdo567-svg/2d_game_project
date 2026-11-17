"""골렘 ① 내려찍기 그림(PixelLab, 정면) + 충격 이펙트 + 화면 흔들림 미리보기 (게임 배율 2배)."""
from pathlib import Path

from PIL import Image, ImageDraw

import build_golem_slam_impact as fx

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FX = fx.main()
src = Image.open(ROOT / "assets/concepts/pixellab/golem_slam/slam_south_frames.png").convert("RGBA")
W = 120
G = [src.crop(((i % 3) * W, (i // 3) * W, (i % 3) * W + W, (i // 3) * W + W)) for i in range(9)]
foot_bottom = G[0].getbbox()[3]
foot_cx = (G[0].getbbox()[0] + G[0].getbbox()[2]) // 2

T, N, SC = 32, 8, 2
SZ = N * T
gx, gy = SZ // 2, 3 * T  # 골렘 2×2 의 바닥 가운데 (발 밑)
ex, ey = gx, gy + round(0.6 * T)  # 손이 닿는 곳 (발 앞)
floor = Image.new("RGBA", (SZ, SZ), (88, 84, 80, 255))
d = ImageDraw.Draw(floor)
for x in range(0, SZ, T):
    for y in range(0, SZ, T):
        d.rectangle((x, y, x + T - 1, y + T - 1), outline=(76, 72, 68, 255))
d.rectangle((gx - 48, gy, gx + 47, gy + 95), outline=(170, 70, 70, 255))  # 앞 3×3 판정

SHAKE = [(0, 0), (3, -1), (-3, 1), (2, 0), (-1, 0)]
TICK = 1 / 24
# (골렘 그림, 이펙트 프레임) : 들기 0~4 → 쾅 5 (멈칫) → 6~8
seq = []
for i in range(5):
    seq += [(i, None)] * 2
seq += [(4, None)] * 2
k = 0
for gi in [5, 5, 5, 6, 6, 7, 7, 8]:
    seq.append((gi, min(len(FX) - 1, round(k * TICK * fx.FPS))))
    k += 1
while round(k * TICK * fx.FPS) < len(FX):
    seq.append((8, round(k * TICK * fx.FPS)))
    k += 1
seq += [(0, None)] * 10

frames = []
for n, (gi, fi) in enumerate(seq):
    world = floor.copy()
    if fi is not None:
        world.alpha_composite(FX[fi], (ex - fx.C, ey - fx.C))
    world.alpha_composite(G[gi], (gx - foot_cx, gy - foot_bottom))
    shake = SHAKE[fi] if fi is not None and fi < len(SHAKE) else (0, 0)
    screen = Image.new("RGBA", (SZ, SZ), (30, 28, 32, 255))
    screen.alpha_composite(world, shake)
    frames.append(screen.resize((SZ * SC, SZ * SC), Image.NEAREST))
frames[0].save(HERE / "golem_slam_impact_preview.gif", save_all=True, append_images=frames[1:],
               duration=round(TICK * 1000), loop=0)
print(len(frames))
