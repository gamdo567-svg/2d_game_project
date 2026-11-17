"""공격 한 번(Strike)과 공격이 닿는 칸 계산.

주인공은 휘두르는 프레임에 들어서는 순간 Strike 를 하나 낸다. 장면이 attack_tiles 로 닿는 칸을 구해
그 칸에 있는 대상에게 피해를 준다. 판정 단위는 칸이다 (2026-11-17 사용자 결정, D-024).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Strike:
    col: int  # 공격하는 칸 (주인공 위치)
    row: int
    direction: tuple[int, int]  # 바라보는 방향 (dx, dy), 위쪽이 +1
    reach: int  # 앞으로 몇 칸까지
    damage: int
    width: int = 1  # 가로(바라보는 방향의 옆) 몇 칸. 홀수, 가운데 줄이 바라보는 방향 (2026-11-17)


def attack_tiles(strike: Strike, is_wall: Callable[[int, int], bool]) -> list[tuple[int, int]]:
    """공격이 닿는 칸: 바라보는 방향으로 reach 칸, 가로 width 칸 (가운데 줄 + 양옆 같은 수).

    줄마다 앞으로 나아가다 벽을 만나면 그 줄은 그 앞에서 멈춘다 (벽 너머는 맞지 않음).
    """
    dx, dy = strike.direction
    side_x, side_y = -dy, dx  # 바라보는 방향의 옆
    half = strike.width // 2
    tiles = []
    for lane in range(-half, half + 1):
        for k in range(1, strike.reach + 1):
            tile = (strike.col + dx * k + side_x * lane, strike.row + dy * k + side_y * lane)
            if is_wall(*tile):
                break
            tiles.append(tile)
    return tiles
