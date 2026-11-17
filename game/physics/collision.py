"""칸 단위 충돌 판정.

이동은 한 칸씩이므로 "그 칸에 들어갈 수 있는가"만 판단한다. 맵 밖과 벽 칸에는 들어갈 수 없다.
몬스터 등 움직이는 장애물이 생기면 여기에 함께 판단한다.
게임 로직 모듈이라 pico2d 를 import 하지 않는다.
"""
from __future__ import annotations

from game.world.tile_map import TileMap


def can_enter(tile_map: TileMap, col: int, row: int) -> bool:
    """(col, row) 칸으로 들어갈 수 있는지."""
    return not tile_map.is_wall(col, row)
