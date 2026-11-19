"""몬스터 어그로 (2026-11-20 사용자 결정).

- 몬스터는 휴면으로 시작한다. 주인공이 config.AGGRO_WAKE_DISTANCE 칸 안에 들어오거나 때리면 깨어나 어그로가 끌린다.
- 주인공은 한 번에 **한 마리**만 끈다. 끈 몬스터가 죽을 때까지 유지하고 (멀어져도 풀리지 않음),
  그동안 다른 몬스터는 다가가도·맞아도 휴면 그대로다 (맞으면 피해만 받음).
- 끈 몬스터가 죽으면 다시 비어, 가까운 휴면 몬스터가 다음에 끌린다.
몬스터는 dormant / alive / distance_to(tile) / wake() 를 갖는다. 게임 로직 모듈이라 pico2d 를 import 하지 않는다.
"""
from __future__ import annotations

from typing import Protocol

from game import config

Tile = tuple[int, int]


class Monster(Protocol):
    @property
    def dormant(self) -> bool: ...

    @property
    def alive(self) -> bool: ...

    def distance_to(self, tile: Tile) -> int: ...

    def wake(self) -> None: ...


class AggroTracker:
    """주인공 한 명이 끈 몬스터 (없으면 None)."""

    def __init__(self, wake_distance: int = config.AGGRO_WAKE_DISTANCE) -> None:
        self.wake_distance = wake_distance
        self.target: Monster | None = None

    def update(self, player_tile: Tile, monsters: list) -> None:
        """끈 몬스터가 죽었으면 놓고, 비어 있으면 거리 안의 가장 가까운 휴면 몬스터를 깨워 끈다."""
        if self.target is not None and not self.target.alive:
            self.target = None
        if self.target is not None:
            return
        near = [m for m in monsters
                if m.alive and m.dormant and m.distance_to(player_tile) <= self.wake_distance]
        if near:
            self._pull(min(near, key=lambda m: m.distance_to(player_tile)))

    def on_hit(self, monster: Monster) -> None:
        """휴면 몬스터를 때림: 끈 몬스터가 없으면 거리와 상관없이 그 몬스터가 끌린다."""
        if self.target is None and monster.alive and monster.dormant:
            self._pull(monster)

    def _pull(self, monster: Monster) -> None:
        self.target = monster
        monster.wake()
