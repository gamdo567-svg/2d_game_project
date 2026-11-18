"""ChatGPT 가 그린 골렘 기절 핵심 자세(result_<dir>.png: 서기 / 휘청 / 무릎)를 게임 크기로 정리 (2026-11-18).

1. 회색 배경을 바깥에서 채워 지우고, 가로로 떨어진 세 자세를 자른다 (발차기와 같은 정리 함수).
2. 서기 자세의 키를 게임 서 있는 그림(96×96)의 키에 맞춰 같은 배율로 세 자세를 줄인다 (BOX).
3. 색을 게임 그림 색 중 가장 가까운 색으로 맞추고, 밝기 분포를 게임 그림과 같게 한다
   (match_tone: 후면 내려찍기에서 원본보다 밝고 흐릿하던 문제와 같은 처리).
4. CANVAS 에 발 밑(가장 아래 줄)과 아래 6줄 가운데를 FOOT 에 맞춘다. 장마다 DX 로 가로 자리를 손본다.

출력: keys/<dir>_{stand,stagger,kneel}.png, keys_preview.png
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
palette_of, remove_bg, snap = _kick.palette_of, _kick.remove_bg, _kick.snap

OUT = HERE / "keys"
CANVAS = (144, 128)
FOOT = (72, 120)
NAMES = ("stand", "stagger", "kneel")
DX: dict[tuple[str, str], int] = {}  # (방향, 자세) → 가로 손보기 (픽셀)


def split3(im: Image.Image) -> list[Image.Image]:
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
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:3])
    out = []
    for x0, x1 in runs:
        piece = im.crop((x0, 0, x1, h))
        out.append(piece.crop(piece.getbbox()))
    return out


def luma(c) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def match_tone(im: Image.Image, ref: Image.Image) -> Image.Image:
    """밝기 순서를 그대로 두고 밝기 분포를 ref 와 같게 (어두운 외곽선·그늘·하이라이트 비율을 원본에 맞춤)."""
    ref_cols = sorted((p for p in ref.get_flattened_data() if p[3]), key=luma)
    im = im.copy()
    px = im.load()
    pts = sorted(((x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3]), key=lambda q: luma(px[q]))
    n = len(pts)
    for i, q in enumerate(pts):
        px[q] = ref_cols[min(len(ref_cols) - 1, int(i / n * len(ref_cols)))]
    return im


def feet_center(im: Image.Image) -> tuple[float, int]:
    bb = im.getbbox()
    a = im.getchannel("A").load()
    xs = [x for y in range(bb[3] - 6, bb[3]) for x in range(im.width) if a[x, y]]
    return (min(xs) + max(xs)) / 2, bb[3]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cells = []
    for d in ("south", "east", "north"):
        idle = Image.open(ROOT / "assets/images/golem" / f"{d}.png").convert("RGBA")
        ib = idle.getbbox()
        pal = palette_of(idle)
        poses = split3(remove_bg(Image.open(HERE / f"result_{d}.png")))
        scale = (ib[3] - ib[1]) / poses[0].height
        for name, p in zip(NAMES, poses):
            small = snap(p.resize((max(1, round(p.width * scale)), max(1, round(p.height * scale))), Image.BOX), pal)
            small = match_tone(small, idle)
            fx, fy = feet_center(small)
            c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            c.alpha_composite(small, (round(FOOT[0] - fx) + DX.get((d, name), 0), FOOT[1] - fy))
            c.save(OUT / f"{d}_{name}.png")
            cells.append(c)
        print(d, "배율", round(scale, 3))
    sheet = Image.new("RGBA", (CANVAS[0] * 3, CANVAS[1] * 3), (90, 90, 100, 255))
    for i, c in enumerate(cells):
        sheet.alpha_composite(c, ((i % 3) * CANVAS[0], (i // 3) * CANVAS[1]))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(HERE / "keys_preview.png")


if __name__ == "__main__":
    main()
