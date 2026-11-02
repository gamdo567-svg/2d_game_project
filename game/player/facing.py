"""바라보는 방향과 방향별 스프라이트 선택.

이동은 8방향이지만, 그림은 front/back/side 3종 원본으로 4방향을 표현한다.
왼쪽은 side(오른쪽을 보는 그림)를 좌우 반전해 그린다.
"""
from __future__ import annotations

from enum import Enum


class Facing(Enum):
    """화면에 보이는 4방향. 값은 칸 좌표 기준 단위 벡터 (dy 는 위쪽이 +1)."""

    DOWN = (0, -1)
    UP = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


# 방향 -> (원본 그림 이름, 좌우 반전 여부)
_SPRITE_VIEWS: dict[Facing, tuple[str, bool]] = {
    Facing.DOWN: ("front", False),
    Facing.UP: ("back", False),
    Facing.RIGHT: ("side", False),
    Facing.LEFT: ("side", True),
}


def sprite_view(facing: Facing) -> tuple[str, bool]:
    """방향에 맞는 원본 그림 이름(front/back/side)과 좌우 반전 여부."""
    return _SPRITE_VIEWS[facing]


def facing_for_direction(dx: int, dy: int, current: Facing) -> Facing:
    """입력 방향 (dx, dy) 에 맞는 바라보는 방향을 고른다.

    - 입력이 없으면 현재 방향을 유지한다.
    - 직선 입력이면 그 방향을 본다.
    - 대각선 입력이면, 현재 방향이 두 성분 중 하나와 같을 때 그대로 유지해
      그림이 깜빡이지 않게 한다. 그렇지 않으면 좌우(side) 그림을 쓴다.
      걷는 동작이 가장 잘 보이는 그림이 측면이기 때문이다.
    """
    if dx == 0 and dy == 0:
        return current
    horizontal = Facing.RIGHT if dx > 0 else Facing.LEFT
    vertical = Facing.UP if dy > 0 else Facing.DOWN
    if dy == 0:
        return horizontal
    if dx == 0:
        return vertical
    if current in (horizontal, vertical):
        return current
    return horizontal
