"""골렘 ① 두 손 내려찍기 후면 핵심 자세를 다른 이미지 도구(ChatGPT 등)에 요청하기 위한 묶음 (2026-11-18).

후면은 PixelLab 이 내려찍은 뒤 팔부터 먼저 되돌려 그려서(몸은 숙였는데 팔만 옆으로 돌아옴),
핵심 자세 4장(서기·들기·내려찍기·일어서기)을 다른 도구로 그린다.

- ref_golem_north_x8.png  : 게임 골렘 뒷모습 서 있는 그림(96×96)을 8배, 회색 배경 (생김새·색 기준)
- motion_guide.png        : 윗줄 = 정면 내려찍기(잘 된 것)의 같은 순간 4장, 아랫줄 = 지금 후면(1·2 는 그대로 써도 됨, 3·4 가 문제)
실행: python build_kit.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
GOLEM = ROOT / "assets/images/golem"
BG = (128, 128, 128, 255)
CELL = (144, 176)  # slam_<dir>.png 한 칸
PICKS = [(0, "1 STAND"), (5, "2 RAISE"), (7, "3 SLAM"), (9, "4 RISING")]
S = 4


def on_bg(im):
    c = Image.new("RGBA", im.size, BG)
    c.alpha_composite(im.convert("RGBA"))
    return c


def main():
    idle = Image.open(GOLEM / "north.png")
    on_bg(idle).resize((idle.width * 8, idle.height * 8), Image.NEAREST).save(HERE / "ref_golem_north_x8.png")

    w, h = CELL
    rows = [("FRONT (good, for timing/pose)", "slam_south.png"), ("BACK now (3 and 4 are wrong)", "slam_north.png")]
    top = 40
    guide = Image.new("RGBA", (w * S * len(PICKS), (h * S + top) * len(rows)), BG)
    d = ImageDraw.Draw(guide)
    for r, (title, name) in enumerate(rows):
        strip = Image.open(GOLEM / name).convert("RGBA")
        y = r * (h * S + top)
        d.text((10, y + 8), title, fill=(255, 255, 0, 255))
        for k, (i, label) in enumerate(PICKS):
            f = on_bg(strip.crop((i * w, 0, i * w + w, h)))
            guide.paste(f.resize((w * S, h * S), Image.NEAREST), (k * w * S, y + top))
            d.text((k * w * S + 250, y + 8), label, fill=(255, 255, 255, 255))
    guide.save(HERE / "motion_guide.png")
    print("ok")


if __name__ == "__main__":
    main()
