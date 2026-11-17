"""후면 패링 핵심 자세를 다른 이미지 도구(ChatGPT 등)에 요청하기 위한 묶음.

- ref_player_back_x12.png  : 게임 주인공 뒷모습 서 있는 그림(32×48)을 12배, 회색 배경 (생김새·색 기준)
- ref_back_ready_guard_x8.png : PixelLab 이 깨끗하게 그린 후면 당김·막기 자세(64×64)를 8배로 나란히 (자세 참고)
- motion_guide_front_side.png : 완성된 측면·정면 패링 순서(서기·당김·쳐올림·막기·당김)를 6배로 (동작 참고)
실행: python build_kit.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = ROOT / "assets/concepts/pixellab/player_import/remake_raw"
BG = (128, 128, 128, 255)


def on_bg(im):
    c = Image.new("RGBA", im.size, BG)
    c.alpha_composite(im.convert("RGBA"))
    return c


def main():
    back = Image.open(ROOT / "assets/images/player/idle/back.png").convert("RGBA").crop((0, 0, 32, 48))
    on_bg(back).resize((32 * 12, 48 * 12), Image.NEAREST).save(HERE / "ref_player_back_x12.png")

    ready = Image.open(RAW / "parry_ready_north.png")
    guard = Image.open(RAW / "parry_guard_north.png")
    s = Image.new("RGBA", (64 * 2 * 8 + 40, 64 * 8 + 50), BG)
    s.paste(on_bg(ready).resize((512, 512), Image.NEAREST), (0, 50))
    s.paste(on_bg(guard).resize((512, 512), Image.NEAREST), (552, 50))
    d = ImageDraw.Draw(s)
    d.text((20, 15), "1 READY (pull sword up in front)", fill=(255, 255, 255, 255))
    d.text((572, 15), "3 GUARD (sword raised diagonally)", fill=(255, 255, 255, 255))
    s.save(HERE / "ref_back_ready_guard_x8.png")

    rows = [Image.open(RAW / "parry_side_sheet_68.png"), Image.open(RAW / "parry_front_sheet_68.png")]
    g = Image.new("RGBA", (408, 68 * 2 + 20), BG)
    for i, r in enumerate(rows):
        g.alpha_composite(r.convert("RGBA"), (0, 20 + i * 68))
    g = g.resize((g.width * 6, g.height * 6), Image.NEAREST)
    d = ImageDraw.Draw(g)
    for k, label in enumerate(["STAND", "1 READY", "2 SWING UP", "3 GUARD", "3 GUARD", "READY"]):
        d.text((k * 68 * 6 + 20, 30), label, fill=(255, 255, 255, 255))
    g.save(HERE / "motion_guide_front_side.png")
    print("ok")


if __name__ == "__main__":
    main()
