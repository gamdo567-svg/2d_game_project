"""주인공 회피 핵심 자세를 다른 이미지 도구(ChatGPT 등)에 요청하기 위한 묶음 (2026-11-18 사용자 요청).

PixelLab 만으로는 후면을 제대로 못 그려서, 패링 후면·골렘 차기처럼 핵심 자세를 ChatGPT 로 받고
사이 동작은 PixelLab(시작·끝 자세 지정)으로 채운다.
- ref_player_<front|side|back>_x12.png : 게임 주인공 서 있는 그림(32×48)을 12배, 회색 배경 (생김새·색 기준)
- ref_player_all_x8.png                : 세 방향을 나란히 (한 번에 올릴 때)
실행: python build_kit.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BG = (128, 128, 128, 255)


def on_bg(im):
    c = Image.new("RGBA", im.size, BG)
    c.alpha_composite(im.convert("RGBA"))
    return c


def main():
    views = {}
    for view in ("front", "side", "back"):
        im = Image.open(ROOT / f"assets/images/player/idle/{view}.png").convert("RGBA").crop((0, 0, 32, 48))
        views[view] = im
        on_bg(im).resize((32 * 12, 48 * 12), Image.NEAREST).save(HERE / f"ref_player_{view}_x12.png")
    row = Image.new("RGBA", (32 * 3 + 16, 48), BG)
    for i, view in enumerate(("front", "side", "back")):
        row.alpha_composite(views[view], (i * 40, 0))
    row.resize((row.width * 8, row.height * 8), Image.NEAREST).save(HERE / "ref_player_all_x8.png")
    print("ok")


if __name__ == "__main__":
    main()
