"""검 속성이 다 차오른 순간 터지는 폭발 (2026-11-20 사용자: 원소 부여가 심심함, 더 역동적으로).

칼 가운데에서 속성 색 고리가 빠르게 퍼지며 얇아지고, 빛줄기가 사방으로 뻗었다 사라진다 (약 0.35초).
불 = 노랑·주황, 전기 = 흰빛·하늘색, 어둠 = 반투명 검은 고리 (그림자). 원본 픽셀 격자(y 위로)의 점 목록을 낸다.
pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

import math

BURST_TIME = 0.35  # 초
RAYS = 10
COLOURS = {
    "fire": ((255, 240, 170), (255, 150, 40)),
    "lightning": ((245, 252, 255), (120, 205, 255)),
    "dark": (None, None),  # 반투명 검정 (그림자)
}


def burst_pixels(element: str, age: float, centre: tuple[float, float]) -> list[tuple]:
    """age 초 지난 폭발의 점들: (x, y, 색) 또는 어둠이면 (x, y, None, 짙기). 끝났으면 빈 목록."""
    if age < 0 or age >= BURST_TIME:
        return []
    t = age / BURST_TIME
    ease = 1 - (1 - t) ** 3  # 처음 빠르게 퍼짐
    radius = 3 + 22 * ease
    thick = max(1.0, 3.0 * (1 - t))
    inner, outer = COLOURS.get(element, COLOURS["fire"])
    cx, cy = centre
    out: list[tuple] = []

    def put(x: int, y: int, colour, alpha: float) -> None:
        if colour is None:
            out.append((x, y, None, alpha))
        else:
            out.append((x, y, colour))

    fade = 1 - t
    for y in range(math.floor(cy - radius - thick), math.floor(cy + radius + thick) + 1):
        for x in range(math.floor(cx - radius - thick), math.floor(cx + radius + thick) + 1):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if abs(d - radius) <= thick / 2:
                put(x, y, inner if t < 0.4 else outer, 0.9 * fade)
    for k in range(RAYS):  # 빛줄기: 고리 안쪽에서 바깥으로
        a = 2 * math.pi * k / RAYS + 0.3
        r0, r1 = radius * 0.55, radius * (1.05 + 0.25 * (k % 2))
        steps = max(1, int(r1 - r0))
        for s in range(steps + 1):
            r = r0 + (r1 - r0) * s / steps
            put(math.floor(cx + math.cos(a) * r), math.floor(cy + math.sin(a) * r),
                outer if s < steps * 0.6 else inner, 0.8 * fade)
    if t < 0.25:  # 처음 번쩍: 가운데 작은 덩어리
        for y in range(math.floor(cy - 2), math.floor(cy + 3)):
            for x in range(math.floor(cx - 2), math.floor(cx + 3)):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= 2.5:
                    put(x, y, inner, 0.95)
    return out
