"""다른 이미지 도구(ChatGPT 등)에 줄 골렘 발차기 핵심 자세 요청 묶음을 만든다.

- ref_golem_<dir>_x8.png : 게임 골렘 서 있는 그림(96×96)을 8배(768×768) nearest 확대, 회색 배경
- pose_guide_<dir>.png   : skeleton 버전(같은 다리·같은 동작)의 서기 / 준비 / 차기 자세를 6배로 나란히, 번호 표시
실행: python build_kit.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BG = (128, 128, 128, 255)


def main():
    for d in ("south", "east", "north", "west"):
        idle = Image.open(ROOT / "assets/images/golem" / f"{d}.png").convert("RGBA")
        canvas = Image.new("RGBA", idle.size, BG)
        canvas.alpha_composite(idle)
        canvas.resize((idle.width * 8, idle.height * 8), Image.NEAREST).save(HERE / f"ref_golem_{d}_x8.png")

        strip = Image.open(HERE.parent / "aligned" / f"kick_{d}.png").convert("RGBA")
        cell = 128
        picks = [(0, "1 STAND"), (3, "2 WIND-UP"), (5, "3 KICK")]
        S = 5
        sheet = Image.new("RGBA", (cell * S * len(picks), cell * S + 60), BG)
        dr = ImageDraw.Draw(sheet)
        for k, (i, label) in enumerate(picks):
            f = Image.new("RGBA", (cell, cell), BG)
            f.alpha_composite(strip.crop((i * cell, 0, i * cell + cell, cell)))
            sheet.paste(f.resize((cell * S, cell * S), Image.NEAREST), (k * cell * S, 60))
            dr.text((k * cell * S + 20, 18), label, fill=(255, 255, 255, 255))
        sheet.save(HERE / f"pose_guide_{d}.png")
    print("ok")


if __name__ == "__main__":
    main()
