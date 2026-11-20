"""불 붙음 (2026-11-20 사용자 결정): 불 속성 칼로 맞으면 불이 붙어 체력이 서서히 깎인다.

- 한 대 맞을 때마다 BURN_SECONDS_PER_HIT 초씩 길어지고, 최대 BURN_MAX_SECONDS 초까지 쌓인다 (많이 때릴수록 오래 탐).
- 타는 동안 BURN_DAMAGE_PER_SECOND 의 피해를 BURN_TICK 초마다 나눠 준다.
- 회피(대쉬)할 수 있는 캐릭터는 회피하면 불이 꺼진다 (extinguish). 골렘처럼 회피가 없으면 다 탈 때까지 탄다.
- BurnFlames: 타는 대상 몸에서 불꽃 알갱이가 피어올라 식으며 사라지는 그림용 입자 (대상 발 밑 기준 원본 픽셀, 위쪽 +).

pico2d 를 쓰지 않는 순수 로직이다. 주인공·적이 함께 쓴다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

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
class Flame:
    x: float  # 대상 발 밑 가운데 기준 원본 픽셀 (오른쪽 +)
    y: float  # 위쪽 +
    vx: float
    vy: float
    size: float
    life: float
    age: float = 0.0


@dataclass
class BurnFlames:
    """타는 대상 몸에서 피어오르는 불꽃 알갱이. width·height = 대상 몸 크기 (원본 픽셀)."""
    width: float
    height: float
    rng: random.Random = field(default_factory=random.Random)
    flames: list[Flame] = field(default_factory=list)
    _timer: float = 0.0

    def update(self, dt: float, burning: bool) -> None:
        for f in self.flames:
            f.age += dt
            f.vx *= 0.9
            f.x += f.vx * dt
            f.y += f.vy * dt
        self.flames = [f for f in self.flames if f.age < f.life]
        if not burning:
            return
        self._timer -= dt
        while self._timer <= 0.0:
            self._spawn()
            self._timer += self.rng.expovariate(config.BURN_FLAME_RATE * self.width * self.height / 100)

    def _spawn(self) -> None:
        rng = self.rng
        half = self.width / 2
        y = rng.uniform(0.0, self.height * 0.85)
        x = rng.uniform(-half, half) * (0.6 + 0.4 * (1 - y / self.height))  # 위로 갈수록 좁게
        self.flames.append(Flame(x, y, rng.uniform(-8, 8), rng.uniform(40, 70), rng.uniform(2.5, 5.0),
                                 rng.uniform(0.3, 0.6)))

    def pixels(self) -> list[tuple[int, int, int, tuple[int, int, int]]]:
        """그릴 네모들 (x, y, 크기, 색), 원본 픽셀.

        알갱이마다 위로 길쭉한 열 덩어리를 쌓고(가까운 것끼리 붙어 불꽃 혀가 됨), 열을 BURN_FLAME_LEVELS 로 끊어
        색을 고른다 (픽셀풍): 뜨거운 가운데는 희고 노랗고, 가장자리·꼭대기로 갈수록 주황 → 붉게. 알갱이는 식으며 작아진다.
        """
        heat: dict[tuple[int, int], float] = {}
        for f in self.flames:
            life = f.age / f.life
            r = f.size * (1 - 0.5 * life)
            strength = (1 - life) ** 0.7
            for py in range(math.floor(f.y - r), math.floor(f.y + 2.8 * r) + 1):
                for px in range(math.floor(f.x - r), math.floor(f.x + r) + 1):
                    dy = py + 0.5 - f.y
                    dy = dy / 2.8 if dy > 0 else dy  # 위로 길쭉하게 (불꽃 혀)
                    d = math.hypot(px + 0.5 - f.x, dy) / r
                    if d < 1:
                        heat[(px, py)] = heat.get((px, py), 0.0) + strength * (1 - d)
        out = []
        for (px, py), h in heat.items():
            colour = None
            for level, c in config.BURN_FLAME_LEVELS:
                if h >= level:
                    colour = c
            if colour is not None:
                out.append((px, py, 1, colour))
        return out
