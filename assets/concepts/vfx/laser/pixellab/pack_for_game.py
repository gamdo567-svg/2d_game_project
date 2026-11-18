"""PixelLab VFX Creator 로 만든 골렘 레이저 충전 그림을 게임 시트로 옮긴다 (2026-11-18 사용자 요청).

충전은 두 겹으로 나눴다 (사용자 요청: 빛이 뚝뚝 끊기며 모여 부자연스러움 → 자연스럽게):
- motes/ ('Golem laser charge motes'): 빛 알갱이가 가운데로 끊임없이 빨려 드는 반복 16장, 16fps, 80×80.
  게임은 지난 시간으로 프레임을 골라 실제 속도로 돌린다.
  → assets/images/effects/golem_laser_charge_motes.png (80×80 × 16, 가로 한 줄, 칸 가운데 = 코어)
- orb/ ('Golem laser charge orb'): 코어의 구가 점에서 지름 약 15픽셀까지 커지는 24장, 32×32.
  게임은 충전 진행도로 프레임을 고른다.
  → assets/images/effects/golem_laser_charge_orb.png (32×32 × 24, 가로 한 줄, 칸 가운데 = 코어)
- charge/ ('Golem laser charge', 한 덩어리 24장)는 첫 시안: 충전 4초에 24장이라 1초에 6장씩 끊겨 보여 쓰지 않는다.
- blast/ ('Golem laser blast')는 비교용: 사용자가 예전 계산 그림 폭발이 낫다고 해 게임에 쓰지 않는다.
원본 픽셀 크기는 게임 원본(칸 32픽셀)과 같아 늘리지 않는다. 게임은 RENDER_SCALE 로 키워 그린다.
실행: python pack_for_game.py
"""
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3] / "images" / "effects"


def to_row(stem: Path, out: Path) -> int:
    """PixelLab 내보내기(시트 + json 의 프레임 자리)를 가로 한 줄 시트로. 프레임 가운데 = 기준점(가운데)."""
    frames = json.loads(stem.with_suffix(".json").read_text(encoding="utf-8"))["frames"]
    sheet = Image.open(stem.with_suffix(".png")).convert("RGBA")
    w, h = frames[0]["frame"]["w"], frames[0]["frame"]["h"]
    row = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        r = f["frame"]
        row.alpha_composite(sheet.crop((r["x"], r["y"], r["x"] + w, r["y"] + h)), (i * w, 0))
    row.save(out)
    return len(frames)


def main() -> None:
    n1 = to_row(HERE / "motes" / "golem-laser-charge-motes", GAME / "golem_laser_charge_motes.png")
    n2 = to_row(HERE / "orb" / "golem-laser-charge-orb", GAME / "golem_laser_charge_orb.png")
    print("ok", n1, n2)


if __name__ == "__main__":
    main()
