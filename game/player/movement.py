"""칸 단위 실시간 이동 (상하좌우 4방향).

- 논리적 위치는 항상 정수 칸 좌표 (col, row) 이다.
- 이동을 시작하는 순간 논리적 위치는 도착 칸으로 바뀌고,
  그림은 출발 칸에서 도착 칸까지 delta time 으로 보간해 그린다.
- 키를 계속 누르고 있으면, 한 칸 이동이 끝날 때 남은 시간을 이어 받아
  다음 칸 이동을 바로 시작한다 (끊김 없는 연속 이동).
- 대각선 이동은 없다 (2026-11-03 사용자 결정).
- 들어갈 수 있는 칸인지는 can_enter(col, row) 로 묻는다 (기본: 격자 안이면 됨). 벽 충돌은 이것으로 막는다.
- 걷는 중 방향 바꾸기 (2026-11-17 사용자 결정, 조작감): 반대 방향은 그 자리에서 바로 되돌아간다
  (같은 직선 위라 사선이 생기지 않음). 옆 방향은 지금 칸을 마친 뒤 꺾는다 — 칸 사이에서 바로 꺾으면
  사선으로 움직여 상하좌우 이동 규칙에 어긋난다 (사용자 지적으로 제거).
"""
from __future__ import annotations

import math
from typing import Callable

from game.world.grid import Grid

CanEnter = Callable[[int, int], bool]


class GridMover:
    def __init__(self, grid: Grid, col: int, row: int, speed: float, can_enter: CanEnter | None = None) -> None:
        if not grid.in_bounds(col, row):
            raise ValueError(f"시작 칸 ({col}, {row}) 이 격자 밖입니다.")
        if speed <= 0:
            raise ValueError("speed 는 0 보다 커야 합니다.")
        self.grid = grid
        self.col = col  # 논리적 칸 좌표 (이동 중이면 도착 칸)
        self.row = row
        self.speed = speed  # 칸/초
        self.can_enter = can_enter or grid.in_bounds
        self._step_duration = 1.0 / speed  # 지금 진행 중인 이동에 걸리는 시간 (회피는 따로 정함)

        self._from_col: float = col  # 그림 보간의 출발점 (방향을 바꾸면 그 순간 보이던 위치라 실수일 수 있음)
        self._from_row: float = row
        self._progress = 1.0  # 0.0 = 출발점, 1.0 = 도착 칸
        self._dir = (0, 0)  # 지금 이동 방향
        self._origin = (col, row)  # 지금 이동에서 떠나온 칸
        self._dashing = False  # 회피 중에는 방향을 바꾸지 않는다

    @property
    def is_moving(self) -> bool:
        return self._progress < 1.0

    @property
    def move_direction(self) -> tuple[int, int]:
        """지금 진행 중인 한 칸 이동의 방향 (dx, dy). 멈춰 있으면 (0, 0)."""
        if not self.is_moving:
            return 0, 0
        return self._dir

    @property
    def visual_position(self) -> tuple[float, float]:
        """그리기용 칸 좌표 (실수). 이동 중이면 두 칸 사이를 보간한 값."""
        t = self._progress
        return (
            self._from_col + (self.col - self._from_col) * t,
            self._from_row + (self.row - self._from_row) * t,
        )

    def update(self, dt: float, dx: int, dy: int) -> None:
        """dt 초만큼 이동을 진행한다. (dx, dy) 는 지금 누르고 있는 방향 (직선 한 방향)."""
        if self.is_moving and not self._dashing and (dx, dy) not in ((0, 0), self._dir):
            self._redirect(dx, dy)
        remaining = dt
        while True:
            if not self.is_moving:
                if not self._try_start(dx, dy):
                    return
            step_time = self._step_duration * (1.0 - self._progress)
            if remaining < step_time:
                self._progress += remaining / self._step_duration
                return
            # 이번 칸 도착. 남은 시간은 다음 칸 이동에 넘긴다.
            remaining -= step_time
            self._progress = 1.0
            self._from_col, self._from_row = self.col, self.row
            self._origin = (self.col, self.row)
            self._step_duration = 1.0 / self.speed
            self._dashing = False
            if remaining <= 0.0:
                return

    def hurry(self, duration: float) -> None:
        """걷던 한 칸의 남은 거리를 duration 초 안에 마저 간다 (공격하려고 칸에 바로 서기, 2026-11-17).

        지금 보이는 위치에서 도착 칸까지 이어지므로 그림이 튀지 않는다. 회피 중이거나 이미 더 빨리 도착하면 그대로 둔다.
        """
        if not self.is_moving or self._dashing:
            return
        if self._step_duration * (1.0 - self._progress) <= duration:
            return
        self._from_col, self._from_row = self.visual_position
        self._progress = 0.0
        self._step_duration = duration

    def dash(self, dx: int, dy: int, max_tiles: int, duration: float) -> int:
        """(dx, dy) 방향으로 최대 max_tiles 칸을 duration 초에 한 번에 미끄러지듯 이동한다 (회피).

        들어갈 수 없는 칸을 만나면 그 앞까지만 간다. 간 칸 수를 돌려준다 (0 이면 움직이지 않음).
        한 칸 이동 중이었다면 지금 그려지는 위치에서 바로 출발한다 (그림이 튀지 않게).
        """
        if (dx == 0) == (dy == 0):
            raise ValueError("회피는 상하좌우 한 방향이어야 합니다.")
        tiles = 0
        while tiles < max_tiles and self._enterable(self.col + dx * (tiles + 1), self.row + dy * (tiles + 1)):
            tiles += 1
        if tiles == 0:
            return 0
        self._from_col, self._from_row = self.visual_position
        self._origin = (self.col, self.row)
        self.col += dx * tiles
        self.row += dy * tiles
        self._dir = (dx, dy)
        self._progress = 0.0
        self._step_duration = duration
        self._dashing = True
        return tiles

    def _enterable(self, col: int, row: int) -> bool:
        return self.grid.in_bounds(col, row) and self.can_enter(col, row)

    def _redirect(self, dx: int, dy: int) -> None:
        """걷는 중 방향 바꾸기: 반대 방향이면 떠나온 칸으로 바로 되돌아간다. 옆 방향은 칸을 마친 뒤 (사선 방지)."""
        if (dx, dy) != (-self._dir[0], -self._dir[1]):
            return
        target = self._origin
        new_origin = (self.col, self.row)
        if not self._enterable(*target):
            return
        vx, vy = self.visual_position
        distance = math.hypot(target[0] - vx, target[1] - vy)
        self._from_col, self._from_row = vx, vy
        self.col, self.row = target
        self._origin = new_origin
        self._dir = (dx, dy)
        self._progress = 0.0
        self._step_duration = max(distance, 1e-6) / self.speed

    def _try_start(self, dx: int, dy: int) -> bool:
        """(dx, dy) 방향으로 한 칸 이동을 시작한다. 못 움직이면 False."""
        if dx != 0 and dy != 0:
            raise ValueError("대각선 이동은 지원하지 않습니다.")
        if dx == 0 and dy == 0:
            return False
        if not self._enterable(self.col + dx, self.row + dy):
            return False  # 맵 밖이나 벽 칸으로는 들어가지 않는다
        self._from_col, self._from_row = self.col, self.row
        self._origin = (self.col, self.row)
        self.col += dx
        self.row += dy
        self._dir = (dx, dy)
        self._progress = 0.0
        return True
