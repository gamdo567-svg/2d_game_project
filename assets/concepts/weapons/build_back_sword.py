"""등에 멘 칼 그림을 칼 그림에서 계산해 만든다 (2026-11-18 사용자 요청: 평소에는 검을 등에 매고 다님).

입력: assets/images/player/weapons/<무기>.png (56×10, 칼끝 오른쪽, 한가운데가 손).
1. 칼날 부분(가드 오른쪽)을 가죽 칼집으로 감싼다: 칼날보다 얇게(외곽선 + 가죽 한 줄 + 외곽선), 끝에 금속 마구리.
   손잡이·가드는 칼 그림 그대로.
2. SCALE 배 (지금은 원래 크기, nearest).
3. 방향마다 기울여 64×64 캔버스에 놓는다. 캔버스 아래 가운데가 주인공 발 밑이고, 32×48 주인공 그림은
   캔버스 (16, 16)~(48, 64) 에 놓인다고 보고 자리를 정한다. 손잡이는 오른쪽 어깨 위로 (오른손으로 뽑기 쉽게).
   - front: 몸 뒤. 오른쪽 어깨(화면 왼쪽) 위로 손잡이, 칼집 끝은 몸 아래 오른쪽.
   - back:  등 위(몸 앞에 그림). 오른쪽 어깨(화면 오른쪽) 위로 손잡이, 칼집은 등을 가로질러 왼쪽 아래.
   - side:  오른쪽을 볼 때, 몸 뒤. 머리 뒤로 손잡이, 칼집은 등 쪽 아래로. 왼쪽은 게임이 뒤집는다.
출력: assets/images/player/weapons/<무기>_back_<view>.png (64×64), back_sword_preview.png (서 있는 그림 위에 얹은 8배)
실행: python build_back_sword.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WEAPONS = ROOT / "assets" / "images" / "player" / "weapons"
PLAYER = ROOT / "assets" / "images" / "player"
WEAPON = "old_sword"
SCALE = 1.0  # 칼 그림의 실제 길이는 34픽셀(56칸 중)이라 원래 크기로 멘다
CANVAS = 64
BODY = (16, 16)  # 32×48 주인공 그림이 놓이는 캔버스 자리 (왼쪽 위)
OUTLINE = (22, 15, 20, 255)
LEATHER = [(40, 26, 26, 255), (56, 36, 32, 255), (74, 48, 40, 255)]  # 어두운 → 밝은 (망토보다 어둡게)
CHAPE = (213, 153, 103, 255)  # 칼집 끝 금속 (가드와 같은 색)
# 방향별: (가드 자리 = 주인공 그림 좌표, 각도: 칼끝 방향, 화면 위가 + / 0 = 오른쪽, 몸 뒤에 그리는지)
PLACES = {
    "front": ((7, 15), -55, True),
    "back": ((22, 19), -122, False),
    "side": ((8, 16), -100, True),
}


def sheathed(sword: Image.Image) -> Image.Image:
    """칼날을 가죽 칼집으로 감싼 그림 (같은 56×10)."""
    w, h = sword.size
    px = sword.load()
    # 가드: 손(한가운데) 근처에서 가장 긴 세로 줄
    hand = w // 2
    guard_x = max(range(hand - 4, hand + 5), key=lambda x: sum(1 for y in range(h) if px[x, y][3]))
    blade_cols = [x for x in range(guard_x + 1, w) if any(px[x, y][3] for y in range(h))]
    # 칼날 두께는 가드에서 3칸 떨어진 곳부터 잰다 (가드 기둥이 섞이면 칼집이 두꺼워짐)
    blade_rows = [y for y in range(h) if any(px[x, y][3] for x in blade_cols if x > guard_x + 3)]
    # 칼날보다 얇게: 칼날 외곽선 안쪽 줄만 (가운데 한 줄 가죽 + 위아래 외곽선). 2026-11-18 사용자 지적: 두꺼우면 화살통처럼 보임
    top, bottom = min(blade_rows) + 1, max(blade_rows) - 1
    tip = max(blade_cols)
    out = sword.copy()
    opx = out.load()
    for x in range(guard_x + 1, tip + 1):
        for y in range(h):
            opx[x, y] = (0, 0, 0, 0)
        for y in range(top, bottom + 1):
            if y in (top, bottom) or x == tip:
                opx[x, y] = OUTLINE
            elif x >= tip - 2:
                opx[x, y] = CHAPE
            else:
                opx[x, y] = LEATHER[2] if x % 9 != 4 else LEATHER[0]  # 가운데 한 줄, 가끔 가죽 띠
    return out


def place(item: Image.Image, guard: tuple[int, int], angle: float) -> Image.Image:
    """칼집 칼을 줄이고 기울여, 손 자리(그림 한가운데)를 guard(주인공 그림 좌표)에 놓는다."""
    w, h = item.size
    small = item.resize((round(w * SCALE), max(3, round(h * SCALE))), Image.NEAREST)
    big = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    big.alpha_composite(small, (48 - small.width // 2, 48 - small.height // 2))
    rot = big.rotate(angle, resample=Image.NEAREST, center=(48, 48))
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    gx, gy = BODY[0] + guard[0], BODY[1] + guard[1]
    canvas.alpha_composite(rot, (gx - 48, gy - 48)) if gx >= 48 and gy >= 48 else canvas.paste(
        rot.crop((48 - gx, 48 - gy, 48 - gx + CANVAS, 48 - gy + CANVAS)), (0, 0))
    return canvas


def main() -> None:
    sword = Image.open(WEAPONS / f"{WEAPON}.png").convert("RGBA")
    item = sheathed(sword)
    preview = Image.new("RGBA", (CANVAS * 3, CANVAS), (40, 44, 52, 255))
    for k, (view, (guard, angle, behind)) in enumerate(PLACES.items()):
        art = place(item, guard, angle)
        art.save(WEAPONS / f"{WEAPON}_back_{view}.png")
        body = Image.open(PLAYER / "idle" / f"{view}.png").convert("RGBA").crop((0, 0, 32, 48))
        cell = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        if behind:
            cell.alpha_composite(art)
            cell.alpha_composite(body, BODY)
        else:
            cell.alpha_composite(body, BODY)
            cell.alpha_composite(art)
        preview.alpha_composite(cell, (k * CANVAS, 0))
    preview.resize((preview.width * 8, preview.height * 8), Image.NEAREST).save(HERE / "back_sword_preview.png")
    item.resize((item.width * 8, item.height * 8), Image.NEAREST).save(HERE / "sheathed_sword_x8.png")
    print("saved", [f"{WEAPON}_back_{v}.png" for v in PLACES])


if __name__ == "__main__":
    main()


def head_anchor(sheet: Image.Image, frame: int, w: int, h: int) -> tuple[int, int]:
    """그림 한 장의 머리 꼭대기: (발 밑 가운데에서 가로로 떨어진 양, 발 밑에서 위로 높이)."""
    cell = sheet.crop((frame * w, 0, frame * w + w, h))
    px = cell.load()
    top = min(y for y in range(h) for x in range(w) if px[x, y][3])
    xs = [x for y in range(top, top + 4) for x in range(w) if px[x, y][3]]
    return round((min(xs) + max(xs)) / 2 - w / 2), h - top


def offsets() -> dict:
    """상태·방향별로 장마다 등 칼을 옮길 양 (원본 픽셀, 오른쪽·위가 +): 서 있기 첫 장 머리 꼭대기 기준."""
    sizes = {"idle": (32, 48), "walk": (32, 48), "jump": (48, 56), "dodge": (64, 48)}
    table = {}
    for state, (w, h) in sizes.items():
        table[state] = {}
        for view in ("front", "side", "back"):
            sheet = Image.open(PLAYER / state / f"{view}.png").convert("RGBA")
            base = head_anchor(Image.open(PLAYER / "idle" / f"{view}.png").convert("RGBA"), 0, 32, 48)
            table[state][view] = tuple(
                (ax - base[0], ay - base[1]) for ax, ay in
                (head_anchor(sheet, f, w, h) for f in range(sheet.width // w)))
    return table


if __name__ == "__main__" and "--offsets" in __import__("sys").argv:
    for state, views in offsets().items():
        print(f'    "{state}": {{')
        for view, t in views.items():
            print(f'        "{view}": {t},')
        print("    },")
