"""칸 레이캐스트 (순수 로직). 2026-11-18 사용자 요청: 골렘 레이저가 벽을 통과하지 않게.

시작점에서 끝점으로 곧게 가며 지나가는 칸을 차례로 본다 (DDA: 칸 경계를 넘을 때마다 다음 칸).
좌표는 칸 좌표(실수): 칸 (c, r) 는 x 가 c 이상 c+1 미만, y 가 r 이상 r+1 미만.
"""
from __future__ import annotations

import math
from typing import Callable

Point = tuple[float, float]


def first_open_stop(start: Point, end: Point, is_wall: Callable[[int, int], bool]) -> tuple[Point, bool]:
    """start 에서 end 로 가다 처음 만나는 벽 바로 앞 칸의 가운데와 True 를 돌려준다. 벽이 없으면 (end, False).

    start 칸이 벽이면 start 를 그대로 돌려준다 (막힘).
    """
    x0, y0 = start
    x1, y1 = end
    col, row = math.floor(x0), math.floor(y0)
    if is_wall(col, row):
        return start, True
    end_col, end_row = math.floor(x1), math.floor(y1)
    dx, dy = x1 - x0, y1 - y0
    step_c = 1 if dx > 0 else -1
    step_r = 1 if dy > 0 else -1
    # 다음 세로·가로 칸 경계까지 가는 데 드는 t (0~1), 한 칸을 지날 때마다 드는 t
    t_max_x = ((col + (step_c > 0)) - x0) / dx if dx else math.inf
    t_max_y = ((row + (step_r > 0)) - y0) / dy if dy else math.inf
    t_dx = abs(1 / dx) if dx else math.inf
    t_dy = abs(1 / dy) if dy else math.inf
    while (col, row) != (end_col, end_row):
        prev = (col, row)
        if t_max_x < t_max_y:
            if t_max_x > 1:
                break
            col += step_c
            t_max_x += t_dx
        else:
            if t_max_y > 1:
                break
            row += step_r
            t_max_y += t_dy
        if is_wall(col, row):
            return (prev[0] + 0.5, prev[1] + 0.5), True
    return end, False
