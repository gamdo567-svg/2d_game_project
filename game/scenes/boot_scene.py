"""초기 환경 확인용 장면.

- 칸 격자를 그려 칸 좌표와 픽셀 좌표의 변환을 눈으로 확인한다.
- delta time 기반 타이머로 표식을 깜빡여, FPS 와 무관하게 시간이 흐르는지 확인한다.
- 게임플레이 기능(이동, 전투 등)은 포함하지 않는다.

이 모듈은 pico2d 를 import 하지 않는다. 그리기는 전달받은 renderer 로만 한다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import InputState
from game.world.grid import Grid


class BootScene:
    BLINK_INTERVAL = 0.5  # 표식 깜빡임 간격(초)
    FPS_SAMPLE_INTERVAL = 0.5  # FPS 표시 갱신 간격(초)

    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        # 확인용 표식 위치 (칸 좌표). 격자 중앙 칸.
        self.marker_col = grid.cols // 2
        self.marker_row = grid.rows // 2

        self.elapsed = 0.0  # 장면 시작 후 경과 시간(초)
        self.marker_visible = True
        self._blink_timer = 0.0

        self.fps = 0.0
        self._fps_timer = 0.0
        self._fps_frames = 0

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        self.elapsed += dt

        self._blink_timer += dt
        while self._blink_timer >= self.BLINK_INTERVAL:
            self._blink_timer -= self.BLINK_INTERVAL
            self.marker_visible = not self.marker_visible

        self._fps_frames += 1
        self._fps_timer += dt
        if self._fps_timer >= self.FPS_SAMPLE_INTERVAL:
            self.fps = self._fps_frames / self._fps_timer
            self._fps_frames = 0
            self._fps_timer = 0.0

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
        grid = self.grid
        renderer.fill_screen(config.COLOR_BACKGROUND)

        # 칸 (0, 0): 좌표 원점이 왼쪽 아래임을 확인
        renderer.fill_tile(grid, 0, 0, config.COLOR_ORIGIN_TILE)
        renderer.draw_grid(grid, config.COLOR_GRID_LINE)

        if self.marker_visible:
            renderer.fill_tile(
                grid, self.marker_col, self.marker_row, config.COLOR_MARKER, inset=4
            )

        # 안내 문구 (화면 위쪽)
        top = grid.height_px
        renderer.draw_text(16, top - 24, "2D Action RPG - 초기 개발 환경", config.COLOR_TEXT)
        renderer.draw_text(16, top - 50, "ESC: 종료", config.COLOR_TEXT_DIM)

        mx, my = grid.tile_to_pixel(self.marker_col, self.marker_row)
        info = (
            f"FPS {self.fps:5.1f} | 경과 {self.elapsed:6.1f}s | "
            f"표식 칸 ({self.marker_col}, {self.marker_row}) -> 픽셀 ({mx:.0f}, {my:.0f})"
        )
        renderer.draw_text(16, top - 76, info, config.COLOR_TEXT_DIM)

        # 원점 칸 옆 표시
        _, origin_y = grid.tile_to_pixel(0, 0)
        renderer.draw_text(grid.tile_size + 8, origin_y, "<- 칸 (0, 0)", config.COLOR_TEXT_DIM)
