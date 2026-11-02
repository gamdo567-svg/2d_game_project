"""주인공 이동 확인용 장면.

- 칸 격자 위에서 주인공을 8방향으로 움직인다.
- 맵 데이터, 벽 충돌, 전투 등은 포함하지 않는다. 이동 가능 범위는 화면(격자) 안이다.

이 모듈은 pico2d 를 import 하지 않는다. 그리기는 전달받은 renderer 로만 한다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import InputState
from game.player.player import Player
from game.world.grid import Grid


class FieldScene:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.player = Player(grid, config.PLAYER_START_COL, config.PLAYER_START_ROW)

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        self.player.update(dt, input_state)

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
        grid = self.grid
        renderer.fill_screen(config.COLOR_BACKGROUND)
        renderer.draw_grid(grid, config.COLOR_GRID_LINE)

        self.player.draw(renderer)

        top = grid.height_px
        renderer.draw_text(16, top - 24, "WASD / 방향키: 이동    ESC: 종료", config.COLOR_TEXT_DIM)
        player = self.player
        info = f"칸 ({player.col}, {player.row}) | 상태 {player.state} | 방향 {player.facing.name}"
        renderer.draw_text(16, top - 50, info, config.COLOR_TEXT_DIM)
