"""패링 성공 이펙트(노란 불꽃 파티클) 프레임 생성기. 2026-11-17 사용자 요청: 패링에 성공하면 노란색 성공 파티클.

원본(1x) 64x64 캔버스, 가운데 (32, 32) 가 칼이 부딪힌 점. 게임은 RENDER_SCALE(2)로 nearest 확대해 그린다.
구성: 첫 순간 흰·노란 십자 섬광 → 둥근 충격 고리가 퍼지며 사라짐 → 불꽃 알갱이가 사방으로 튀어 떨어지며
흰색 → 노랑 → 주황으로 식고 꺼짐. 같은 결과가 나오도록 난수 시드를 고정한다.

출력: assets/images/effects/parry_spark.png (가로 한 줄 FRAMES 장), 같은 폴더의 parry_spark_preview.gif (4배)
실행: python build_parry_spark.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
S = 64
C = S // 2
FRAMES = 9
FPS = 24

WHITE = (255, 255, 236, 255)
Y1 = (255, 240, 140, 255)
Y2 = (255, 214, 70, 255)
Y3 = (240, 170, 40, 255)
ORANGE = (214, 116, 30, 255)
RAMP = [WHITE, Y1, Y2, Y3, ORANGE]  # 뜨거움 → 식음

rng = random.Random(7)


class Spark:
    def __init__(self) -> None:
        self.angle = rng.uniform(0, 2 * math.pi)
        self.speed = rng.uniform(90, 190)  # 원본 픽셀/초
        self.life = rng.uniform(0.18, 0.36)
        self.size = 2 if rng.random() < 0.35 else 1

    def at(self, t: float):
        """t 초 뒤 위치와 색 단계 (꺼졌으면 None). 위로 튄 것도 중력으로 떨어진다 (y 는 아래로 +)."""
        if t > self.life:
            return None
        drag = 1 - 0.55 * t / self.life
        x = C + math.cos(self.angle) * self.speed * t * drag
        y = C + math.sin(self.angle) * self.speed * t * drag + 160 * t * t
        heat = t / self.life
        return x, y, min(len(RAMP) - 1, int(heat * len(RAMP)))


SPARKS = [Spark() for _ in range(22)]


def put(img: Image.Image, x: float, y: float, color, size: int = 1) -> None:
    px = img.load()
    for dx in range(size):
        for dy in range(size):
            xi, yi = int(x) + dx, int(y) + dy
            if 0 <= xi < S and 0 <= yi < S:
                px[xi, yi] = color


def frame(f: int) -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    t = f / FPS
    # 충격 고리: 반지름이 커지며 점점 듬성듬성 사라짐
    if 1 <= f <= 5:
        r = 5 + f * 3.2
        steps = 56
        keep = 1.0 - (f - 1) * 0.2
        for i in range(steps):
            if (i * 7 % 10) / 10 >= keep:
                continue
            a = 2 * math.pi * i / steps
            put(img, C + math.cos(a) * r, C + math.sin(a) * r, Y1 if f <= 2 else Y2)
    # 불꽃 알갱이: 짧은 꼬리(지난 위치)와 함께
    for sp in SPARKS:
        now = sp.at(t)
        if now is None:
            continue
        x, y, heat = now
        before = sp.at(max(0.0, t - 0.02))
        if before and heat <= 2:
            put(img, before[0], before[1], RAMP[min(len(RAMP) - 1, heat + 1)])
        put(img, x, y, RAMP[heat], sp.size)
    # 십자 섬광: 처음 세 장만, 점점 작아짐
    if f <= 2:
        arm = (11, 8, 4)[f]
        for k in range(-arm, arm + 1):
            col = WHITE if abs(k) <= arm // 2 else Y1
            put(img, C + k, C, col)
            put(img, C, C + k, col)
        diag = (5, 3, 0)[f]
        for k in range(-diag, diag + 1):
            put(img, C + k, C + k, Y1)
            put(img, C + k, C - k, Y1)
        core = (3, 2, 1)[f]
        for dx in range(-core, core + 1):
            for dy in range(-core, core + 1):
                if abs(dx) + abs(dy) <= core:
                    put(img, C + dx, C + dy, WHITE)
    return img


def main() -> None:
    frames = [frame(f) for f in range(FRAMES)]
    sheet = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        sheet.alpha_composite(im, (i * S, 0))
    out = ROOT / "images" / "effects" / "parry_spark.png"
    sheet.save(out)
    bg = (32, 29, 39, 255)
    big = []
    for im in frames:
        b = Image.new("RGBA", (S, S), bg)
        b.alpha_composite(im)
        big.append(b.resize((S * 4, S * 4), Image.NEAREST).convert("RGB"))
    big[0].save(HERE / "parry_spark_preview.gif", save_all=True, append_images=big[1:] + [big[-1]] * 6,
                duration=round(1000 / FPS) * 3, loop=0)
    print("saved", out, sheet.size)


if __name__ == "__main__":
    main()
