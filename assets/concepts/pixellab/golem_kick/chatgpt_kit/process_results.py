"""ChatGPT 가 그린 골렘 발차기 핵심 자세(result_<dir>.png: 서기 / 준비 / 차기 가로로 3개)를 게임 크기로 정리.

1. 바깥 테두리에서 시작해 회색 배경을 채워 지운다 (골렘은 검은 외곽선이 있어 안쪽 회색은 남는다).
2. 연결된 덩어리로 세 자세를 나눈다 (작은 점은 버림).
3. 서기 자세의 키를 게임 서 있는 그림(96×96 원본)의 키에 맞춰 같은 배율로 세 자세를 줄인다 (BOX → 팔레트).
4. 색을 게임 골렘 그림의 색 목록에 가장 가까운 색으로 맞춘다.
5. 128×128 캔버스에 서 있는 그림(idle128: 96 그림을 (16,16) 에)과 발 밑 가운데가 같도록 놓는다.

출력: keys/<dir>_{stand,windup,kick}.png (128×128), keys_preview.png
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE / "keys"
CELL = 128
PAD = 16  # 96 그림을 128 캔버스에 놓는 여백 (PixelLab 에 올린 idle128 과 같음)


def remove_bg(im: Image.Image, tol: int = 26) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = px[5, 5][:3]
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        r, g, b, a = px[x, y]
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tol:
            continue
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))
    return im


def split_poses(im: Image.Image) -> list[Image.Image]:
    """알파가 있는 열을 묶어 가로로 나뉜 덩어리를 찾는다 (큰 것 3개)."""
    w, h = im.size
    a = im.getchannel("A").load()
    cols = [any(a[x, y] for y in range(h)) for x in range(w)]
    runs, start = [], None
    for x, c in enumerate(cols + [False]):
        if c and start is None:
            start = x
        elif not c and start is not None:
            runs.append((start, x))
            start = None
    runs = sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:3]
    runs.sort()
    out = []
    for x0, x1 in runs:
        piece = im.crop((x0, 0, x1, h))
        out.append(piece.crop(piece.getbbox()))
    return out


def palette_of(im: Image.Image) -> list[tuple[int, int, int]]:
    cols = {p[:3] for p in im.convert("RGBA").getdata() if p[3] > 0}
    return sorted(cols)


def snap(im: Image.Image, pal) -> Image.Image:
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            best = min(pal, key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2)
            px[x, y] = (*best, 255)
    return im


def main() -> None:
    OUT.mkdir(exist_ok=True)
    previews = []
    for d in ("south", "east", "north", "west"):
        idle = Image.open(ROOT / "assets/images/golem" / f"{d}.png").convert("RGBA")
        ib = idle.getbbox()
        pal = palette_of(idle)
        poses = split_poses(remove_bg(Image.open(HERE / f"result_{d}.png")))
        scale = (ib[3] - ib[1]) / poses[0].height  # 서기 자세 키 → 게임 그림 키
        foot_x = PAD + (ib[0] + ib[2]) / 2
        foot_y = PAD + ib[3]
        row = []
        for name, p in zip(("stand", "windup", "kick"), poses):
            small = p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.BOX)
            small = snap(small, pal)
            canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
            # 발 밑: 가장 아래 줄을 foot_y 에, 가로는 그 자세에서 '아래 6줄'의 가운데(디딘 발)를 서기의 가운데에
            bb = small.getbbox()
            a = small.getchannel("A").load()
            xs = [x for y in range(max(0, bb[3] - 6), bb[3]) for x in range(small.width) if a[x, y]]
            cx = (min(xs) + max(xs)) / 2 if name == "stand" else None
            row.append((name, small, bb, xs))
        # 서기 자세의 디딘 발 가운데를 기준으로 세 자세를 같은 양만큼 옮긴다 (ChatGPT 그림 안의 상대 위치 유지)
        stand_small, stand_bb, stand_xs = row[0][1], row[0][2], row[0][3]
        base_cx = (min(stand_xs) + max(stand_xs)) / 2
        for name, small, bb, xs in row:
            canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
            if name == "stand":
                cx = base_cx
            else:
                # 디딘 발(가장 아래 줄 근처에서 가장 큰 덩어리)의 가운데를 서기와 같은 자리에
                cx = (min(xs) + max(xs)) / 2 if (max(xs) - min(xs)) < small.width * 0.45 else base_cx
            ox, oy = round(foot_x - cx), round(foot_y - bb[3])
            canvas.alpha_composite(small, (ox, oy))
            canvas.save(OUT / f"{d}_{name}.png")
            previews.append(canvas)
        print(d, "배율", round(scale, 3), [r[1].size for r in row])
    sheet = Image.new("RGBA", (CELL * 3, CELL * 4), (90, 90, 100, 255))
    for i, c in enumerate(previews):
        sheet.alpha_composite(c, ((i % 3) * CELL, (i // 3) * CELL))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(HERE / "keys_preview.png")


if __name__ == "__main__":
    main()
