"""칸 단위 실시간 이동 (상하좌우 4방향).

- 논리적 위치는 항상 정수 칸 좌표 (col, row) 이다.
- 이동을 시작하는 순간 논리적 위치는 도착 칸으로 바뀌고,
  그림은 출발 칸에서 도착 칸까지 delta time 으로 보간해 그린다.
- 키를 계속 누르고 있으면, 한 칸 이동이 끝날 때 남은 시간을 이어 받아
  다음 칸 이동을 바로 시작한다 (끊김 없는 연속 이동).
- 대각선 이동은 없다 (2026-11-03 사용자 결정).
"""
from __future__ import annotations

from game.world.grid import Grid


class GridMover:
    def __init__(self, grid: Grid, col: int, row: int, speed: float) -> None:
        if not grid.in_bounds(col, row):
            raise ValueError(f"시작 칸 ({col}, {row}) 이 격자 밖입니다.")
        if speed <= 0:
            raise ValueError("speed 는 0 보다 커야 합니다.")
        self.grid = grid
        self.col = col  # 논리적 칸 좌표 (이동 중이면 도착 칸)
        self.row = row
        self.speed = speed  # 칸/초

        self._from_col = col  # 이동 출발 칸
        self._from_row = row
        self._progress = 1.0  # 0.0 = 출발 칸, 1.0 = 도착 칸

    @property
    def is_moving(self) -> bool:
        return self._progress < 1.0

    @property
    def move_direction(self) -> tuple[int, int]:
        """지금 진행 중인 한 칸 이동의 방향 (dx, dy). 멈춰 있으면 (0, 0)."""
        if not self.is_moving:
            return 0, 0
        return self.col - self._from_col, self.row - self._from_row

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
        step_duration = 1.0 / self.speed
        remaining = dt
        while True:
            if not self.is_moving:
                if not self._try_start(dx, dy):
                    return
            step_time = step_duration * (1.0 - self._progress)
            if remaining < step_time:
                self._progress += remaining / step_duration
                return
            # 이번 칸 도착. 남은 시간은 다음 칸 이동에 넘긴다.
            remaining -= step_time
            self._progress = 1.0
            self._from_col, self._from_row = self.col, self.row
            if remaining <= 0.0:
                return

    def _try_start(self, dx: int, dy: int) -> bool:
        """(dx, dy) 방향으로 한 칸 이동을 시작한다. 못 움직이면 False."""
        if dx != 0 and dy != 0:
            raise ValueError("대각선 이동은 지원하지 않습니다.")
        if dx == 0 and dy == 0:
            return False
        if not self.grid.in_bounds(self.col + dx, self.row + dy):
            return False  # 화면(격자) 밖으로는 나가지 않는다
        self._from_col, self._from_row = self.col, self.row
        self.col += dx
        self.row += dy
        self._progress = 0.0
        return True
