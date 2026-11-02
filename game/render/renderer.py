"""pico2d 그리기 함수 래퍼.

장면(scene)은 pico2d 를 직접 호출하지 않고 Renderer 를 통해 그린다.
Renderer 는 pico2d.open_canvas() 이후에 생성해야 한다 (폰트 로드 때문).
"""
from __future__ import annotations

import os

import pico2d

from game.world.grid import Grid

Color = tuple[int, int, int]

# pico2d 패키지에 포함된 기본 폰트 (한글 지원)
_DEFAULT_FONT_PATH = os.path.join(
    os.path.dirname(pico2d.__file__), "data", "ConsolaMalgun.ttf"
)


class Renderer:
    def __init__(self, screen_width: int, screen_height: int, font_size: int = 18) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._font = self._load_font(font_size)

    @staticmethod
    def _load_font(size: int):
        """기본 폰트를 불러온다. 실패해도 게임은 계속 실행한다 (글자만 생략)."""
        try:
            return pico2d.load_font(_DEFAULT_FONT_PATH, size)
        except (IOError, OSError):
            print(f"WARNING: 폰트를 불러오지 못했습니다: {_DEFAULT_FONT_PATH}")
            return None

    # ----- 기본 도형 -----
    def fill_screen(self, color: Color) -> None:
        r, g, b = color
        pico2d.draw_rectangle(
            0, 0, self.screen_width - 1, self.screen_height - 1, r, g, b, filled=True
        )

    def fill_rect(self, left: float, bottom: float, right: float, top: float, color: Color) -> None:
        """[left, right) x [bottom, top) 영역을 채운다."""
        r, g, b = color
        pico2d.draw_rectangle(left, bottom, right - 1, top - 1, r, g, b, filled=True)

    def draw_line(self, x1: float, y1: float, x2: float, y2: float, color: Color) -> None:
        r, g, b = color
        pico2d.draw_line(x1, y1, x2, y2, r, g, b)

    def draw_text(self, x: float, y: float, text: str, color: Color) -> None:
        """(x, y) 를 왼쪽·세로 중앙 기준으로 글자를 그린다."""
        if self._font is not None:
            self._font.draw(x, y, text, color)

    # ----- 칸 격자 -----
    def draw_grid(self, grid: Grid, color: Color) -> None:
        left, bottom = grid.origin_x, grid.origin_y
        right, top = left + grid.width_px, bottom + grid.height_px
        for col in range(grid.cols + 1):
            x = min(left + col * grid.tile_size, right - 1)
            self.draw_line(x, bottom, x, top - 1, color)
        for row in range(grid.rows + 1):
            y = min(bottom + row * grid.tile_size, top - 1)
            self.draw_line(left, y, right - 1, y, color)

    def fill_tile(self, grid: Grid, col: float, row: float, color: Color, inset: int = 0) -> None:
        """칸 하나를 채운다. inset 만큼 안쪽으로 여백을 둔다."""
        left, bottom, right, top = grid.tile_to_pixel_rect(col, row)
        self.fill_rect(left + inset, bottom + inset, right - inset, top - inset, color)
