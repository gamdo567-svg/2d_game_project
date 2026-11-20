"""어둠 능력: 그림자 분신 (2026-11-20 사용자 결정).

- 어둠을 입힌 검으로 3타까지 다 때리면 그 자리·그 방향에 그림자 분신이 남는다 (최대 SHADOW_CLONE_MAX 개, 넘으면 가장 오래된 것이 흩어짐).
- 분신은 움직이지 않고, 주인공이 평타를 치면 자기 자리에서 자기 방향으로 같은 타를 같이 친다 (피해 SHADOW_CLONE_DAMAGE_SCALE 배).
- 흩어져 사라지는 때: 분신이 있는 칸에 선 채 평타를 침 / 몬스터 공격에 맞음 / 아무것도 안 하고 SHADOW_CLONE_IDLE 초 /
  주인공이 SHADOW_CLONE_RANGE 칸보다 멀어짐 / 검의 어둠 속성이 풀리거나 바뀜.
- 그림: 반투명 검은 그림자 (player/shadow/ 그림, 그리기는 player.py), 발밑에 어둠이 일렁이고 위로 어둠 기운이 피어오름.
  흩어질 때는 검은 연기 덩어리로 부서져 흩날린다.

pico2d 를 쓰지 않는 순수 로직이다. 좌표는 칸, 연기는 칸 발 밑 가운데 기준 원본 픽셀 (위쪽 +).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game import config
from game.combat.strike import Strike
from game.player.facing import Facing

Tile = tuple[int, int]


@dataclass
class ShadowClone:
    col: int
    row: int
    facing: Facing
    idle: float = 0.0  # 마지막으로 같이 친 뒤 흐른 시간
    key: tuple | None = None  # 같이 치고 있는 주인공의 타 (strike_id, 타 번호)
    age: float = 0.0  # 나타난 뒤 흐른 시간 (나타날 때 서서히 짙어짐)


@dataclass
class Puff:
    """검은 연기 덩어리 (흩어짐·어둠 기운). 위치는 그 분신 칸 발 밑 가운데 기준 원본 픽셀."""
    col: int
    row: int
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    life: float
    alpha: float
    age: float = 0.0


@dataclass
class ShadowClones:
    rng: random.Random = field(default_factory=random.Random)
    clones: list[ShadowClone] = field(default_factory=list)
    puffs: list[Puff] = field(default_factory=list)
    _wisp_timer: float = 0.0

    def spawn(self, col: int, row: int, facing: Facing) -> None:
        """3타를 다 때린 자리에 분신이 남는다. 같은 칸에 있던 분신은 새것으로 바뀌고, 너무 많으면 가장 오래된 것이 흩어진다."""
        for clone in [c for c in self.clones if (c.col, c.row) == (col, row)]:
            self.scatter(clone)
        self.clones.append(ShadowClone(col, row, facing))
        while len(self.clones) > config.SHADOW_CLONE_MAX:
            self.scatter(self.clones[0])
        self._burst(col, row, 10, 0.45)  # 나타날 때 어둠이 훅 피어오름

    def on_attack_start(self, key: tuple, player_tile: Tile) -> None:
        """주인공이 새 타를 시작했다: 주인공이 서 있는 칸의 분신은 흩어지고, 나머지는 같은 타를 같이 친다."""
        for clone in list(self.clones):
            if (clone.col, clone.row) == player_tile:
                self.scatter(clone)
            else:
                clone.key = key
                clone.idle = 0.0

    def strikes(self, key: tuple, strike: Strike) -> list[Strike]:
        """주인공의 공격이 나가는 순간 같은 타를 치는 분신들의 공격 (자기 자리·방향, 피해는 SHADOW_CLONE_DAMAGE_SCALE 배)."""
        damage = max(1, round(strike.damage * config.SHADOW_CLONE_DAMAGE_SCALE))
        return [Strike(c.col, c.row, c.facing.value, strike.reach, damage, strike.width)
                for c in self.clones if c.key == key]

    def hit_tiles(self, tiles) -> None:
        """몬스터 공격이 터졌다: 그 범위 안의 분신은 흩어진다."""
        for clone in [c for c in self.clones if (c.col, c.row) in tiles]:
            self.scatter(clone)

    def scatter(self, clone: ShadowClone) -> None:
        """분신이 검은 연기로 부서져 흩날리며 사라진다."""
        if clone in self.clones:
            self.clones.remove(clone)
            self._burst(clone.col, clone.row, config.SHADOW_SCATTER_PUFFS, 0.6)

    def scatter_all(self) -> None:
        for clone in list(self.clones):
            self.scatter(clone)

    def update(self, dt: float, player_tile: Tile, dark_active: bool) -> None:
        if not dark_active:
            self.scatter_all()  # 검의 어둠 속성이 풀리거나 바뀌면 모두 흩어짐
        for clone in list(self.clones):
            clone.age += dt
            clone.idle += dt
            far = max(abs(clone.col - player_tile[0]), abs(clone.row - player_tile[1])) > config.SHADOW_CLONE_RANGE
            if clone.idle >= config.SHADOW_CLONE_IDLE or far:
                self.scatter(clone)
        for p in self.puffs:
            p.age += dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.94
            p.vy *= 0.97
        self.puffs = [p for p in self.puffs if p.age < p.life]
        # 어둠 기운: 분신 몸에서 옅은 어둠이 천천히 피어오름
        self._wisp_timer -= dt
        while self._wisp_timer <= 0.0 and self.clones:
            clone = self.rng.choice(self.clones)
            rng = self.rng
            self.puffs.append(Puff(clone.col, clone.row, rng.uniform(-7, 7), rng.uniform(2, 30), rng.uniform(-3, 3),
                                   rng.uniform(8, 16), rng.uniform(2.0, 3.5), rng.uniform(0.6, 1.0), 0.28))
            self._wisp_timer += rng.expovariate(config.SHADOW_WISP_RATE * len(self.clones))
        if not self.clones:
            self._wisp_timer = 0.0

    def _burst(self, col: int, row: int, count: int, alpha: float) -> None:
        rng = self.rng
        for _ in range(count):
            a = rng.uniform(0, 2 * math.pi)
            v = rng.uniform(15, 45)
            self.puffs.append(Puff(col, row, rng.uniform(-6, 6), rng.uniform(4, 34), math.cos(a) * v,
                                   math.sin(a) * v * 0.6 + 12, rng.uniform(2.5, 5.0), rng.uniform(0.4, 0.8), alpha))

    def opacity(self, clone: ShadowClone) -> float:
        """분신의 불투명도: 나타날 때 서서히 짙어지고, 사라지기 1초 전부터 옅어짐 (곧 흩어진다는 신호)."""
        appear = min(1.0, clone.age / 0.2)
        left = config.SHADOW_CLONE_IDLE - clone.idle
        fade = 0.45 + 0.55 * min(1.0, left / 1.0)
        return config.SHADOW_CLONE_OPACITY * appear * fade

    def puff_discs(self) -> list[tuple[int, int, float, float, float, float]]:
        """그릴 연기 (칸 col, row, x, y, 반지름, 짙기): 퍼지며 커지고 옅어짐."""
        return [(p.col, p.row, p.x, p.y, p.radius * (1 + p.age / p.life), p.alpha * (1 - p.age / p.life))
                for p in self.puffs]
