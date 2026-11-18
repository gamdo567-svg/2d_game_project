"""주인공 후면 공격(1·2·3타) 핵심 자세를 ChatGPT 에 요청하기 위한 묶음 (2026-11-18 사용자 요청).

PixelLab 은 후면을 제대로 못 그려서, 후면 패링·회피처럼 핵심 자세를 ChatGPT 로 받고 사이는 PixelLab 으로 채운다.
- ref_player_back_x12.png     : 게임 주인공 뒷모습(32×48) 12배, 회색 배경 (생김새·색 기준)
- ref_back_parry_x6.png       : 완성된 후면 패링 (뒷모습에서 칼이 어떻게 보이는지: 몸에 가린 부분은 안 보임)
- motion_guide_side_combo.png : 완성된 측면 1·2·3타 (줄마다 한 타, 동작 순서 참고)
실행: python build_kit.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BG = (128, 128, 128, 255)


def on_bg(im):
    c = Image.new("RGBA", im.size, BG)
    c.alpha_composite(im.convert("RGBA"))
    return c


def main():
    back = Image.open(ROOT / "assets/images/player/idle/back.png").convert("RGBA").crop((0, 0, 32, 48))
    on_bg(back).resize((32 * 12, 48 * 12), Image.NEAREST).save(HERE / "ref_player_back_x12.png")

    parry = Image.open(HERE.parent / "parry_back_kit" / "parry_back_composed_x4.png").convert("RGBA")
    p = on_bg(parry)
    p.resize((round(p.width * 1.5), round(p.height * 1.5)), Image.NEAREST).save(HERE / "ref_back_parry_x6.png")

    grid = Image.open(HERE.parent / "remake_preview" / "combo_side_sword_grid.png").convert("RGBA")
    rows = grid.crop((0, 0, grid.width, 3 * grid.height // 4))  # 1·2·3타 세 줄 (마지막 서기 줄 제외)
    g = Image.new("RGBA", (rows.width, rows.height + 30), BG)
    g.alpha_composite(rows, (0, 30))
    d = ImageDraw.Draw(g)
    for i, label in enumerate(["HIT 1: diagonal down slash", "HIT 2: rising up slash", "HIT 3: straight thrust"]):
        d.text((6, 30 + i * rows.height // 3 + 4), label, fill=(255, 255, 255, 255))
    g.save(HERE / "motion_guide_side_combo.png")
    print("ok")


if __name__ == "__main__":
    main()
