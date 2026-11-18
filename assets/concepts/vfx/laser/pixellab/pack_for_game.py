"""PixelLab VFX Creator 로 만든 골렘 레이저 이펙트를 게임 시트로 옮긴다 (2026-11-18 사용자 요청: PixelLab 으로).

- charge/part/part-charge_up.png (PixelLab 'Golem laser charge', 24장, 5열, 칸 87×86, manifest.json)
  → assets/images/effects/golem_laser_charge.png: 88×88 칸 24장 가로 한 줄, 칸 가운데 = 골렘 코어.
  PixelLab 캔버스에서 코어는 (47, 46), 조각 칸의 왼쪽 위는 발 기준점(45, 89) + offset(-41, -86) = (4, 3).
- blast/ ('Golem laser blast') 는 비교용으로만 남긴다: 사용자가 예전 계산 그림 폭발이 낫다고 해 게임에는 쓰지 않음.
원본 픽셀 크기는 게임 원본(칸 32픽셀)과 같아 늘리지 않는다. 게임은 RENDER_SCALE 로 키워 그린다.
실행: python pack_for_game.py
"""
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3] / "images" / "effects"


def frames_from(sheet: Image.Image, w: int, h: int, cols: int, count: int) -> list[Image.Image]:
    return [sheet.crop(((i % cols) * w, (i // cols) * h, (i % cols + 1) * w, (i // cols + 1) * h)) for i in range(count)]


def pack(frames, size, center_in_frame, out):
    sheet = Image.new("RGBA", (size * len(frames), size), (0, 0, 0, 0))
    cx, cy = center_in_frame
    for i, f in enumerate(frames):
        cell = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        cell.alpha_composite(f.convert("RGBA"), (size // 2 - cx, size // 2 - cy))
        sheet.alpha_composite(cell, (i * size, 0))
    sheet.save(out)
    return sheet


def main() -> None:
    m = json.loads((HERE / "charge" / "part" / "manifest.json").read_text(encoding="utf-8"))
    clip = m["clips"][0]
    fw, fh = clip["frame"]["w"], clip["frame"]["h"]
    left = m["anchor"]["x"] + clip["offset"]["x"]
    top = m["anchor"]["y"] + clip["offset"]["y"]
    core = (47 - left, 46 - top)  # 조각 칸 안의 코어 자리
    charge = frames_from(Image.open(HERE / "charge" / "part" / "part-charge_up.png"), fw, fh,
                         clip["sheets"][0]["columns"], clip["frames"])
    pack(charge, 88, core, GAME / "golem_laser_charge.png")

    # 폭발('Golem laser blast')은 비교 뒤 예전 계산 그림을 쓰기로 해(사용자 결정) 게임으로 옮기지 않는다.
    print("ok", len(charge))


if __name__ == "__main__":
    main()
