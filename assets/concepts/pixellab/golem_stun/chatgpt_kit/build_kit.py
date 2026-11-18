"""골렘 기절 핵심 자세를 다른 이미지 도구(ChatGPT 등)에 요청하기 위한 묶음 (2026-11-18).

- ref_golem_<dir>_x8.png : 게임 골렘 서 있는 그림(96×96)을 8배 nearest 확대, 회색 배경 (생김새·색 기준)
  dir = south(정면), east(측면, 오른쪽을 봄), north(후면). 서쪽은 동쪽을 뒤집어 쓴다.
실행: python build_kit.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BG = (128, 128, 128, 255)


def main():
    for d in ("south", "east", "north"):
        idle = Image.open(ROOT / "assets/images/golem" / f"{d}.png").convert("RGBA")
        canvas = Image.new("RGBA", idle.size, BG)
        canvas.alpha_composite(idle)
        canvas.resize((idle.width * 8, idle.height * 8), Image.NEAREST).save(HERE / f"ref_golem_{d}_x8.png")
    print("ok")


if __name__ == "__main__":
    main()
