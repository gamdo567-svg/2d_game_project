"""칸(타일) 좌표와 렌더링(픽셀) 좌표의 변환.

좌표계 규칙:
    - 칸 좌표 (col, row): 게임 로직의 기준. (0, 0) 은 맵의 왼쪽 아래 칸.
      col 은 오른쪽으로, row 는 위쪽으로 증가한다.
    - 픽셀 좌표 (x, y): 렌더링 전용. pico2d 규칙에 따라 원점은 화면 왼쪽 아래,
      y 는 위쪽으로 증가한다.

게임 로직(이동 가능 여부, 충돌, 공격 범위 등)은 칸 좌표로만 판단하고,
픽셀 좌표는 그릴 때만 계산한다.

칸 사이를 부드럽게 이동하는 연출을 위해 tile_to_pixel 은 실수 칸 좌표
(예: col=2.5)도 받는다. 카메라(화면 스크롤)가 필요해지면
origin_x / origin_y 를 카메라 오프셋으로 사용해 확장한다.
"""
from __future__ import annotations

import math


class Grid:
    """고정 크기 칸 격자."""

    def __init__(
        self,
        cols: int,
        rows: int,
        tile_size: int,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ) -> None:
        if cols <= 0 or rows <= 0:
            raise ValueError("cols 와 rows 는 1 이상이어야 합니다.")
        if tile_size <= 0:
            raise ValueError("tile_size 는 1 이상이어야 합니다.")
        self.cols = cols
        self.rows = rows
        self.tile_size = tile_size
        self.origin_x = origin_x  # 칸 (0, 0) 의 왼쪽 아래 모서리 픽셀 x
        self.origin_y = origin_y  # 칸 (0, 0) 의 왼쪽 아래 모서리 픽셀 y

    @property
    def width_px(self) -> int:
        return self.cols * self.tile_size

    @property
    def height_px(self) -> int:
        return self.rows * self.tile_size

    def in_bounds(self, col: int, row: int) -> bool:
        """칸 좌표가 격자 안에 있는지 확인한다."""
        return 0 <= col < self.cols and 0 <= row < self.rows

    def tile_to_pixel(self, col: float, row: float) -> tuple[float, float]:
        """칸 좌표 -> 해당 칸 중심의 픽셀 좌표."""
        half = self.tile_size / 2
        x = self.origin_x + col * self.tile_size + half
        y = self.origin_y + row * self.tile_size + half
        return x, y

    def tile_to_pixel_rect(
        self, col: float, row: float
    ) -> tuple[float, float, float, float]:
        """칸 좌표 -> 칸 영역 (left, bottom, right, top) 픽셀 좌표.

        right / top 은 칸 바깥 경계(= 다음 칸의 시작)이다.
        """
        left = self.origin_x + col * self.tile_size
        bottom = self.origin_y + row * self.tile_size
        return left, bottom, left + self.tile_size, bottom + self.tile_size

    def pixel_to_tile(self, x: float, y: float) -> tuple[int, int]:
        """픽셀 좌표 -> 그 점을 포함하는 칸 좌표. 격자 밖일 수 있다."""
        col = math.floor((x - self.origin_x) / self.tile_size)
        row = math.floor((y - self.origin_y) / self.tile_size)
        return col, row
