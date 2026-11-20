"""불 붙음 (2026-11-20 사용자 결정): 불 속성 칼로 맞으면 불이 붙어 체력이 서서히 깎인다.

- 한 대 맞을 때마다 BURN_SECONDS_PER_HIT 초씩 길어지고, 최대 BURN_MAX_SECONDS 초까지 쌓인다 (많이 때릴수록 오래 탐).
- 타는 동안 BURN_DAMAGE_PER_SECOND 의 피해를 BURN_TICK 초마다 나눠 준다.
- 회피(대쉬)할 수 있는 캐릭터는 회피하면 불이 꺼진다 (extinguish). 골렘처럼 회피가 없으면 다 탈 때까지 탄다.
- BurnFlames: 타는 몸 여러 자리에 붙는 불꽃 혀·불티·연기 (그림용, draw_burn 이 그린다).

pico2d 를 쓰지 않는 순수 로직이다. 주인공·적이 함께 쓴다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from game import config


class Burn:
    """불 붙음 상태. update 가 이번에 깎을 피해(정수)를 돌려준다."""

    def __init__(self) -> None:
        self.time_left = 0.0  # 남은 타는 시간 (초)
        self._tick = 0.0  # 다음 피해까지 쌓인 시간

    @property
    def burning(self) -> bool:
        return self.time_left > 0.0

    def ignite(self) -> None:
        """불 속성 공격을 한 대 맞음: 타는 시간이 늘어난다 (최대치까지)."""
        if not self.burning:
            self._tick = 0.0
        self.time_left = min(config.BURN_MAX_SECONDS, self.time_left + config.BURN_SECONDS_PER_HIT)

    def extinguish(self) -> None:
        """불이 꺼짐 (회피, 죽음 등)."""
        self.time_left = 0.0
        self._tick = 0.0

    def update(self, dt: float) -> int:
        """시간이 흐른다. 이번에 깎을 피해를 돌려준다 (BURN_TICK 초마다 한 번)."""
        if not self.burning:
            return 0
        step = min(dt, self.time_left)
        self.time_left = max(0.0, self.time_left - dt)
        self._tick += step
        damage = 0
        while self._tick >= config.BURN_TICK - 1e-9:
            self._tick -= config.BURN_TICK
            damage += round(config.BURN_DAMAGE_PER_SECOND * config.BURN_TICK)
        if not self.burning:
            self._tick = 0.0
        return damage


@dataclass
class Spark:
    """날아오르는 불티 (1 픽셀) 또는 연기 덩어리 (size > 0)."""
    x: float  # 대상 발 밑 가운데 기준 원본 픽셀 (오른쪽 +)
    y: float  # 위쪽 +
    vx: float
    vy: float
    life: float
    size: float = 0.0
    age: float = 0.0


class BurnFlames:
    """타는 대상 몸에 붙는 불꽃 (2026-11-20 사용자: 불타는 느낌이 전혀 안 듦 → 다시 만듦).

    - 불꽃 혀 시트(effects/burn/flame.png)를 몸 여러 자리(anchors)에 박자를 엇갈려 붙인다. 오래 탈수록(많이 맞을수록)
      붙는 자리가 늘어난다 (아래 자리부터). 붙을 때 커지며 피어나고, 꺼질 때 작아지며 사그라든다.
    - 불티: 불꽃에서 1 픽셀 불티가 흔들리며 높이 날아올라 식는다. 연기: 꼭대기 위로 옅은 그림자 덩어리가 피어오른다.
    anchors = ((x, y, 크기, 몸 뒤), ...) 대상 발 밑 가운데 기준 원본 픽셀 (위쪽 +). 몸 뒤인 불꽃은 몸보다 먼저 그린다.
    """

    def __init__(self, anchors: tuple, rng: random.Random | None = None) -> None:
        self.anchors = anchors
        self.rng = rng or random.Random()
        self.heat = [0.0] * len(anchors)  # 자리마다 불꽃 세기 0~1 (피어남·사그라듦)
        self.phase = [self.rng.random() for _ in anchors]  # 자리마다 시트 박자 어긋남
        self.clock = 0.0
        self.sparks: list[Spark] = []
        self.smoke: list[Spark] = []
        self._spark_timer = 0.0
        self._smoke_timer = 0.0

    def active_count(self, time_left: float) -> int:
        """남은 타는 시간에 따라 불이 붙은 자리 수 (BURN_FULL_SECONDS 이상이면 전부)."""
        if time_left <= 0.0:
            return 0
        n = len(self.anchors)
        return 1 + int((n - 1) * min(1.0, time_left / config.BURN_FULL_SECONDS))

    def update(self, dt: float, time_left: float) -> None:
        self.clock += dt
        active = self.active_count(time_left)
        for k in range(len(self.anchors)):
            target = 1.0 if k < active else 0.0
            step = dt / (config.BURN_FLARE_TIME if target else config.BURN_FADE_TIME)
            self.heat[k] = min(target, self.heat[k] + step) if target > self.heat[k] else max(target, self.heat[k] - step)
        for p in self.sparks + self.smoke:
            p.age += dt
            p.x += p.vx * dt + math.sin(p.age * 9 + p.life * 20) * 6 * dt
            p.y += p.vy * dt
        self.sparks = [p for p in self.sparks if p.age < p.life]
        self.smoke = [p for p in self.smoke if p.age < p.life]
        if active == 0:
            return
        lit = [a for a, h in zip(self.anchors, self.heat) if h > 0.3]
        if not lit:
            return
        rng = self.rng
        self._spark_timer -= dt
        while self._spark_timer <= 0.0:
            x, y, size, _ = rng.choice(lit)
            self.sparks.append(Spark(x + rng.uniform(-4, 4) * size, y + rng.uniform(8, 22) * size,
                                     rng.uniform(-10, 10), rng.uniform(35, 75), rng.uniform(0.45, 0.9)))
            self._spark_timer += rng.expovariate(config.BURN_SPARK_RATE * active)
        self._smoke_timer -= dt
        while self._smoke_timer <= 0.0:
            x, y, size, _ = max(lit, key=lambda a: a[1] + 30 * a[2])  # 가장 높은 불꽃 위
            self.smoke.append(Spark(x + rng.uniform(-3, 3), y + 30 * size, rng.uniform(-4, 4), rng.uniform(14, 24),
                                    rng.uniform(0.8, 1.3), rng.uniform(2.0, 3.5)))
            self._smoke_timer += rng.expovariate(config.BURN_SMOKE_RATE)

    def flames(self, behind: bool) -> list[tuple[float, float, float, int]]:
        """그릴 불꽃 혀 (x, y, 크기, 시트 장). 시트 아래 가운데(불이 붙은 줄)를 (x, y) 에."""
        out = []
        for (x, y, size, back), h, ph in zip(self.anchors, self.heat, self.phase):
            if back != behind or h <= 0.05:
                continue
            frame = int((self.clock * config.BURN_FLAME_FPS + ph * config.BURN_FLAME_FRAMES)) % config.BURN_FLAME_FRAMES
            out.append((x, y, size * (0.35 + 0.65 * h), frame))
        return out

    def spark_pixels(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        """불티 (x, y, 색): 처음 노랗다가 주황 → 붉게 식는다."""
        colours = config.BURN_SPARK_COLORS
        return [(math.floor(p.x), math.floor(p.y), colours[min(len(colours) - 1, int(p.age / p.life * len(colours)))])
                for p in self.sparks]

    def smoke_puffs(self) -> list[tuple[float, float, float, float]]:
        """연기 (x, y, 반지름, 짙기): 오르며 커지고 옅어진다."""
        return [(p.x, p.y, p.size * (1 + p.age / p.life), config.BURN_SMOKE_ALPHA * (1 - p.age / p.life))
                for p in self.smoke]


def draw_burn(renderer, flames: BurnFlames, cx: float, bottom: float, behind: bool) -> None:
    """불꽃을 화면에 그린다 (cx, bottom = 대상 발 밑 가운데 화면 좌표). 몸 뒤 불꽃은 몸 전에, 나머지와 불티·연기는 몸 다음에."""
    s = config.RENDER_SCALE
    w, h = config.BURN_FLAME_SIZE
    foot = config.BURN_FLAME_BASE_MARGIN
    for x, y, size, frame in flames.flames(behind):
        dw, dh = round(w * s * size), round(h * s * size)
        renderer.draw_sprite_frame(config.BURN_FLAME_SHEET, frame, w, h, cx + x * s, bottom + (y - foot * size) * s,
                                   dw, dh)
    if behind:
        return
    for x, y, radius, alpha in flames.smoke_puffs():
        r = max(1, round(radius))
        for py in range(-r, r + 1):
            span = round(math.sqrt(max(0, r * r - py * py)))
            renderer.fill_shade(cx + (x - span) * s, bottom + (y + py) * s, cx + (x + span + 1) * s,
                                bottom + (y + py + 1) * s, alpha)
    for x, y, colour in flames.spark_pixels():
        renderer.fill_rect(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, colour)
