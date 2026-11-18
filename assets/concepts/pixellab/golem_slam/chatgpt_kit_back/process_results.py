"""ChatGPT 가 그린 골렘 후면 두 손 내려찍기 핵심 자세(result_north.png: 서기 / 들기 / 내려찍기 / 일어서기)를 게임 크기로 정리.

1. 바깥 테두리에서 회색 배경을 채워 지운다 (골렘은 검은 외곽선이 있어 안쪽 회색은 남는다).
2. 가로로 떨어진 네 자세를 자른다.
3. 서기 자세의 키를 게임 뒷모습(north.png, 96×96)의 키에 맞춰 같은 배율로 줄인다 (BOX).
4. 색을 게임 뒷모습 그림의 색 중 가장 가까운 색으로 맞춘다.
5. 내려찍기 캔버스(144×176)에 두 발(아래 6줄) 가운데·발 밑을 FOOT 에 맞춰 놓는다.
   다리는 네 자세 모두 같은 자리라 디딘 발 가운데로 맞추면 된다.

출력: keys/north_{stand,raise,slam,rise}.png (144×176), keys_preview.png
실행: python process_results.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
_spec = importlib.util.spec_from_file_location(
    "kick_process", HERE.parents[1] / "golem_kick" / "chatgpt_kit" / "process_results.py")
_kick = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_kick)
palette_of, remove_bg, snap = _kick.palette_of, _kick.remove_bg, _kick.snap  # 발차기와 같은 정리 함수

OUT = HERE / "keys"
CANVAS = (144, 176)
FOOT = (72, 166)
NAMES = ("stand", "raise", "slam", "rise")


def split4(im: Image.Image) -> list[Image.Image]:
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
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:4])
    out = []
    for x0, x1 in runs:
        piece = im.crop((x0, 0, x1, h))
        out.append(piece.crop(piece.getbbox()))
    return out


def feet_center(im: Image.Image) -> tuple[float, int]:
    bb = im.getbbox()
    a = im.getchannel("A").load()
    xs = [x for y in range(bb[3] - 6, bb[3]) for x in range(im.width) if a[x, y]]
    return (min(xs) + max(xs)) / 2, bb[3]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    idle = Image.open(ROOT / "assets/images/golem/north.png").convert("RGBA")
    ib = idle.getbbox()
    pal = palette_of(idle)
    poses = split4(remove_bg(Image.open(HERE / "result_north.png")))
    scale = (ib[3] - ib[1]) / poses[0].height
    cells = []
    for name, p in zip(NAMES, poses):
        small = snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.BOX), pal)
        fx, fy = feet_center(small)
        c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        c.alpha_composite(small, (round(FOOT[0] - fx), FOOT[1] - fy))
        c.save(OUT / f"north_{name}.png")
        cells.append(c)
    sheet = Image.new("RGBA", (CANVAS[0] * 4, CANVAS[1]), (90, 90, 100, 255))
    for i, c in enumerate(cells):
        sheet.alpha_composite(c, (i * CANVAS[0], 0))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(HERE / "keys_preview.png")
    print("배율", round(scale, 3), [c.getbbox() for c in cells])


if __name__ == "__main__":
    main()
