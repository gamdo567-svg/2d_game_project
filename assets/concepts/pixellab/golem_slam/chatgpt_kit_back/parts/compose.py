"""후면 내려찍기 착지·일어섬을 원본 뒷모습(north.png) 부위로 다시 짜 맞추기 (2026-11-18 사용자 요청: 질감이 원본과 다름).

장마다 (96×96, 발 밑이 원본과 같은 자리) 지금 그림의 실루엣을 그대로 두고, 그 안을 원본 부위로 채운다:
다리·골반(원본 그대로) → 어깨·윗팔 → 머리 → 등(원본 등 그림을 몸통 타원 크기로 늘림, 테두리 외곽선).
마지막에 지금 그림의 실루엣으로 잘라, 자세(모양)는 한 픽셀도 바뀌지 않는다. 비는 칸은 지금 그림 픽셀.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
REF = Image.open(ROOT / "assets/images/golem/north.png").convert("RGBA")
OUTLINE = (12, 11, 16, 255)


def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def darkest():
    return min((p for p in REF.get_flattened_data() if p[3]), key=luma)


def paste(dst, box, at, scale=None):
    part = REF.crop(box)
    if scale:
        part = part.resize(scale, Image.NEAREST)
    dst.alpha_composite(part, at)


def legs(dst, dy=0):
    # 골반·다리: 팔(양옆 주먹)과 겹치지 않는 열만
    paste(dst, (29, 58, 69, 78), (29, 58 + dy))
    paste(dst, (24, 78, 74, 91), (24, 78 + dy))


def torso(dst, cx, cy, rx, ry, src=(32, 27, 64, 59)):
    """원본 등 그림(src)을 타원(cx, cy, rx, ry) 크기로 늘려 채우고 테두리에 외곽선."""
    w, h = 2 * rx + 1, 2 * ry + 1
    tex = REF.crop(src).resize((w, h), Image.NEAREST)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, w - 1, h - 1), fill=255)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.paste(tex, (0, 0), mask)
    px, mp = layer.load(), mask.load()
    out = darkest()
    for y in range(h):
        for x in range(w):
            if mp[x, y] and any(not (0 <= x + a < w and 0 <= y + b < h) or not mp[x + a, y + b]
                                for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = out
    dst.alpha_composite(layer, (cx - rx, cy - ry))


def clip(composed, frame):
    """지금 그림의 실루엣만 남기고, 채워지지 않은 칸은 지금 그림 픽셀."""
    out = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    a, c, f = out.load(), composed.load(), frame.load()
    for y in range(frame.height):
        for x in range(frame.width):
            if f[x, y][3]:
                a[x, y] = c[x, y] if c[x, y][3] else f[x, y]
    return out


def compose_slam(frame):
    """7: 착지 (등을 숙여 머리가 어깨 뒤로, 손은 등에 가려짐)."""
    c = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    legs(c)
    paste(c, (8, 19, 34, 60), (8, 24))   # 왼쪽 어깨·윗팔
    paste(c, (62, 19, 89, 60), (62, 24))  # 오른쪽 어깨·윗팔
    paste(c, (34, 4, 62, 28), (35, 15))   # 머리 (어깨 뒤로 거의 가려짐)
    torso(c, 49, 41, 21, 20)
    return clip(c, frame)


# 8~12 일어섬: (머리 꼭대기 y, 어깨·팔을 원본보다 내린 양, 등 타원 cx, cy, rx, ry). 그림에서 재어 둠.
RISE = {
    8: (10, 4, 50, 42, 20, 18),
    9: (10, 4, 49, 43, 21, 19),
    10: (9, 3, 48, 42, 22, 19),
    11: (7, 2, 48, 43, 21, 20),
    12: (5, 0, 48, 42, 20, 20),
}


def compose_rise(frame, head_top, arm_dy, cx, cy, rx, ry):
    """8~12: 등이 펴지며 머리가 올라오고, 팔은 몸과 함께 올라옴. 팔은 원본 팔 전체를 두고 실루엣으로 자른다."""
    c = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    legs(c)
    paste(c, (6, 19, 34, 82), (6, 19 + arm_dy))
    paste(c, (62, 19, 91, 82), (62, 19 + arm_dy))
    paste(c, (34, 4, 62, 28), (34, head_top - 1))
    torso(c, cx, cy, rx, ry)
    return clip(c, frame)


CROP = (24, 76)  # 144×176 칸 안에서 96×96 을 자르는 자리 (발 밑이 원본 그림과 같은 자리)


def compose_sheet(sheet: Image.Image) -> Image.Image:
    """slam_north 시트(144×176 × 14)의 7~12장을 다시 짜 맞춘 시트."""
    out = sheet.copy()
    for i in range(7, 13):
        box = (i * 144 + CROP[0], CROP[1], i * 144 + CROP[0] + 96, CROP[1] + 96)
        frame = sheet.crop(box)
        new = compose_slam(frame) if i == 7 else compose_rise(frame, *RISE[i])
        out.paste((0, 0, 0, 0), box)
        out.alpha_composite(new, box[:2])
    return out


if __name__ == "__main__":
    sheet = Image.open(sys.argv[1]).convert("RGBA")
    new = compose_sheet(sheet)
    new.save(sys.argv[2])
    cmp = Image.new("RGBA", (96 * 8, 192), (60, 60, 70, 255))
    for k, i in enumerate(range(6, 14)):
        box = (i * 144 + CROP[0], CROP[1], i * 144 + CROP[0] + 96, CROP[1] + 96)
        cmp.alpha_composite(sheet.crop(box), (96 * k, 0))
        cmp.alpha_composite(new.crop(box), (96 * k, 96))
    cmp.resize((cmp.width * 3, cmp.height * 3), Image.NEAREST).save(HERE / "cmp_all.png")
