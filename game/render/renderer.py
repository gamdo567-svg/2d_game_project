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
        self._images: dict[str, pico2d.Image | None] = {}
        # 도트 그래픽이 흐려지지 않도록 확대·축소 시 가장 가까운 픽셀을 쓴다.
        # 이 힌트는 이후에 만드는 텍스처(이미지)에 적용된다.
        pico2d.SDL_SetHint(pico2d.SDL_HINT_RENDER_SCALE_QUALITY, b"0")

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

    # ----- 이미지 -----
    def _image(self, path: str) -> pico2d.Image | None:
        """이미지를 처음 쓸 때 한 번만 불러와 보관한다.

        불러오지 못하면 경고를 한 번 출력하고 None 을 돌려준다 (그림만 생략).
        SDL 더미 비디오 드라이버(창 없는 스모크 테스트)에서는 렌더러가 없어 항상 실패한다.
        """
        if path not in self._images:
            try:
                self._images[path] = pico2d.load_image(path)
            except (IOError, OSError):
                print(f"WARNING: 이미지를 불러오지 못했습니다: {path}")
                self._images[path] = None
        return self._images[path]

    def draw_sprite_frame(
        self,
        path: str,
        frame_index: int,
        frame_width: int,
        frame_height: int,
        center_x: float,
        bottom: float,
        draw_width: int,
        draw_height: int,
        flip_horizontal: bool = False,
    ) -> None:
        """가로로 이어 붙인 스프라이트 시트에서 frame_index 번째 프레임을 그린다.

        (center_x, bottom) 은 그림의 아래 가운데 (발끝) 픽셀 좌표다.
        원본 프레임(frame_width × frame_height)을 draw_width × draw_height 로 확대해 그린다.
        확대는 nearest(가장 가까운 픽셀) 방식이고 정수 픽셀 위치에 그려 도트가 번지지 않게 한다.
        """
        image = self._image(path)
        if image is None:
            return
        # pico2d 는 그림 중심 좌표를 받는다. 왼쪽 아래 모서리를 정수 픽셀에 맞춘 뒤 중심을 계산한다.
        x = round(center_x - draw_width / 2) + draw_width / 2
        y = round(bottom) + draw_height / 2
        left = frame_index * frame_width
        flip = "h" if flip_horizontal else ""
        image.clip_composite_draw(
            left, 0, frame_width, frame_height, 0, flip, x, y, draw_width, draw_height
        )
