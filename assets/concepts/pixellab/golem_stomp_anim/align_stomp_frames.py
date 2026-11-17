"""골렘 발 구르기(C 버전) 프레임 위치 맞추기.

PixelLab 이 구간(들기 / 내려찍기 / 반동)마다 다른 크기의 캔버스에 그려, 구간이 바뀔 때 골렘이 몇 픽셀씩
아래로 밀려 보였다 (2026-11-17 사용자 지적). 각 구간의 첫 그림은 앞 구간의 마지막 그림과 같은 자세이므로,
두 그림의 실제 픽셀 범위(아래 끝·가로 가운데)가 같아지도록 구간 전체를 옮긴다. 그 뒤 모든 방향을
같은 크기 캔버스에 놓고, 첫 그림(서 있는 자세)의 발 밑 가운데를 고정 기준점(ANCHOR)에 맞춘다.

입력: <dir>_c_frames.png (join 으로 이어 붙인 19장: 들기 0~6, 내려찍기 7~11, 반동 12~18)
출력: aligned/<dir>.png (가로 한 줄 19장, 프레임 CANVAS), aligned/README.txt
실행: python align_stomp_frames.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "aligned"
SIZES = {"south": (168, 124), "east": (132, 144), "north": (156, 136), "west": (124, 140)}
CLIPS = [(0, 7), (7, 12), (12, 19)]
CANVAS = (176, 152)
ANCHOR = (88, 140)  # 첫 그림의 발 밑 가운데가 놓일 자리 (캔버스 안 픽셀)


def load(name: str) -> list[Image.Image]:
    w, h = SIZES[name]
    im = Image.open(HERE / f"{name}_c_frames.png").convert("RGBA")
    cols = im.width // w
    return [im.crop(((i % cols) * w, (i // cols) * h, (i % cols) * w + w, (i // cols) * h + h)) for i in range(19)]


def foot(bbox: tuple[int, int, int, int]) -> tuple[float, int]:
    """픽셀 범위의 (가로 가운데, 아래 끝)."""
    return (bbox[0] + bbox[2]) / 2, bbox[3]


def align(frames: list[Image.Image]) -> tuple[list[Image.Image], list[tuple[int, int]]]:
    """구간마다 옮길 양을 정해 같은 캔버스에 놓는다. 옮긴 양 목록도 돌려준다."""
    offsets = [(0, 0)] * len(frames)
    shift = (0, 0)
    for k, (start, end) in enumerate(CLIPS):
        if k > 0:
            px, py = foot(frames[start - 1].getbbox())
            cx, cy = foot(frames[start].getbbox())
            prev = offsets[start - 1]
            shift = (round(prev[0] + px - cx), prev[1] + py - cy)
        for i in range(start, end):
            offsets[i] = shift
    fx, fy = foot(frames[0].getbbox())
    base = (round(ANCHOR[0] - fx), ANCHOR[1] - fy)
    out = []
    for f, (dx, dy) in zip(frames, offsets):
        c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        c.alpha_composite(f, (base[0] + dx, base[1] + dy))
        out.append(c)
    return out, offsets


def main() -> None:
    OUT.mkdir(exist_ok=True)
    report = []
    for name in SIZES:
        frames, offsets = align(load(name))
        strip = Image.new("RGBA", (CANVAS[0] * len(frames), CANVAS[1]), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            strip.paste(f, (i * CANVAS[0], 0))
        strip.save(OUT / f"{name}.png")
        first, last = foot(frames[0].getbbox()), foot(frames[-1].getbbox())
        report.append(f"{name}: 구간별 옮김 {sorted(set(offsets), key=offsets.index)}, "
                      f"처음 발 {first} / 마지막 발 {last}")
    text = ("골렘 발 구르기 C 버전, 위치를 맞춘 프레임 (align_stomp_frames.py).\n"
            f"프레임 {CANVAS[0]}x{CANVAS[1]}, 가로 한 줄 19장. 들기 0~6, 내려찍기 7~11 (9 = 착지), 반동 12~18.\n"
            f"첫 그림의 발 밑 가운데 = 캔버스 {ANCHOR}.\n\n" + "\n".join(report) + "\n")
    (OUT / "README.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
