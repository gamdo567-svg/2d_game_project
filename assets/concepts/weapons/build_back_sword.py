"""등에 멘 칼 그림을 만든다 (2026-11-18 사용자 요청: 평소에는 검을 등에 매고 다님).

지금은 PixelLab 그림(pixellab_sheath/)을 자리에 맞춰 놓는다 (PIXELLAB_ART). 아래 1~3 은 처음의 계산 방식(밑그림용으로 남김).

입력: assets/images/player/weapons/<무기>.png (56×10, 칼끝 오른쪽, 한가운데가 손).
1. 칼날 부분(가드 오른쪽)을 가죽 칼집으로 감싼다: 칼날과 같은 두께(칼이 들어갈 자리), 끝에 금속 마구리, 검은 외곽선.
   손잡이·가드는 칼 그림 그대로.
2. SCALE 배 (지금은 원래 크기, nearest).
3. 방향마다 기울여 64×64 캔버스에 놓는다. 캔버스 아래 가운데가 주인공 발 밑이고, 32×48 주인공 그림은
   캔버스 (16, 16)~(48, 64) 에 놓인다고 보고 자리를 정한다. 손잡이는 오른쪽 어깨 위로 (오른손으로 뽑기 쉽게).
   - front: 몸 뒤. 오른쪽 어깨(화면 왼쪽) 위로 손잡이, 칼집 끝은 몸 아래 오른쪽.
   - back:  등 위(몸 앞에 그림). 오른쪽 어깨(화면 오른쪽) 위로 손잡이, 칼집은 등을 가로질러 왼쪽 아래.
   - side:  오른쪽을 볼 때, 몸 뒤. 칼집은 등에 붙어 거의 망토 뒤에 가려지고 끝만 살짝. 왼쪽은 게임이 뒤집는다.
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
# 방향별: (가드 자리 = 주인공 그림 좌표, 각도: 칼끝 방향, 화면 위가 + / 0 = 오른쪽, 몸 뒤에 그리는지, 얇게)
# 얇게: 칼집 넓은 면이 아니라 옆 날을 보는 방향이라 외곽선 사이 가죽 한 줄 (2026-11-18 사용자 지적: 측면이 두꺼움)
PLACES = {
    "front": ((7, 15), -55, True, False),
    "back": ((22, 19), -122, False, False),
    "side": ((10, 14), -105, True, True),  # 등에 붙여 망토 뒤로 (밖으로 튀어나오면 화살통처럼 보임, 사용자 지적)
}


def sheathed(sword: Image.Image, thin: bool = False) -> Image.Image:
    """칼날을 가죽 칼집으로 감싼 그림 (같은 56×10). thin 이면 외곽선 사이 가죽 한 줄 (옆에서 본 칼집)."""
    w, h = sword.size
    px = sword.load()
    # 가드: 손(한가운데) 근처에서 가장 긴 세로 줄
    hand = w // 2
    guard_x = max(range(hand - 4, hand + 5), key=lambda x: sum(1 for y in range(h) if px[x, y][3]))
    blade_cols = [x for x in range(guard_x + 1, w) if any(px[x, y][3] for y in range(h))]
    # 칼날 두께는 가드에서 3칸 떨어진 곳부터 잰다 (가드 기둥이 섞이면 칼집이 두꺼워짐)
    blade_rows = [y for y in range(h) if any(px[x, y][3] for x in blade_cols if x > guard_x + 3)]
    top, bottom = min(blade_rows), max(blade_rows)  # 칼날과 같은 두께 (칼이 들어갈 자리, 2026-11-18 사용자 요청)
    if thin:
        top, bottom = top + 1, bottom - 1
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
            elif x % 9 == 4:  # 가죽 띠
                opx[x, y] = LEATHER[0]
            else:
                opx[x, y] = LEATHER[1] if thin else (
                    LEATHER[2] if y == top + 1 else LEATHER[0] if y == bottom - 1 else LEATHER[1])
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


# PixelLab 그림 (2026-11-18 사용자 결정: 계산해 돌린 칼집은 픽셀이 깔끔하지 않고 측면은 칼집처럼 안 보임).
# 처음부터 그 각도로 그린 그림이라 돌리지 않는다. (파일, 좌우 반전, 그림의 가드 자리, 몸에 놓을 가드 자리 = 주인공 그림 좌표)
# 사선 그림은 지금 칼집 모양을 밑그림으로 줘 칼날 두께에 맞춘 것 (pixellab_sheath/diag_C.png).
PIXELLAB_ART = {
    "front": ("diag_C.png", False, (16, 16), (8, 16)),
    "back": ("diag_C.png", True, (16, 16), (21, 19)),
    # 측면은 사선 그림(diag_C)을 세운 것을 밑그림으로 다시 그린 side_C (같은 칼로 보이게, 2026-11-18 사용자 지적)
    "side": ("side_C.png", False, (12, 15), (7, 15)),
}


# 측면 칼집을 한 줄 얇게 (2026-11-18 사용자 요청: 측면 검 굵기를 조금만 줄임). 칼집 부분(가드 아래 줄들)에서
# 가운데 가죽 세로줄 하나를 빼고 오른쪽을 한 칸 당긴다: 폭 5 → 4픽셀 (반 픽셀은 못 줄여 가장 적게 줄인 것).
THIN_COLUMNS = {"side_C.png": (12, range(18, 37))}


def thin(art: Image.Image, name: str) -> Image.Image:
    if name not in THIN_COLUMNS:
        return art
    col, rows = THIN_COLUMNS[name]
    out = art.copy()
    src, dst = art.load(), out.load()
    for y in rows:
        for x in range(col, art.width):
            dst[x, y] = src[x + 1, y] if x + 1 < art.width else (0, 0, 0, 0)
    return out


def place_art(view: str) -> Image.Image:
    name, flip, (ax, ay), (tx, ty) = PIXELLAB_ART[view]
    art = thin(Image.open(HERE / "pixellab_sheath" / name).convert("RGBA"), name)
    if flip:
        art = art.transpose(Image.FLIP_LEFT_RIGHT)
        ax = art.width - 1 - ax
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.alpha_composite(art, (BODY[0] + tx - ax, BODY[1] + ty - ay))
    return canvas


def main() -> None:
    sword = Image.open(WEAPONS / f"{WEAPON}.png").convert("RGBA")
    item = sheathed(sword)
    preview = Image.new("RGBA", (CANVAS * 3, CANVAS), (40, 44, 52, 255))
    for k, (view, (guard, angle, behind, thin)) in enumerate(PLACES.items()):
        art = place_art(view)  # 예전 계산 그림: place(sheathed(sword, thin), guard, angle)
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
