"""주인공 이동 확인용 장면.

- 칸 격자 위에서 주인공을 상하좌우 4방향으로 움직인다.
- 맵 데이터, 벽 충돌, 전투 등은 포함하지 않는다. 이동 가능 범위는 격자(맵) 안이다.
- 맵이 화면보다 크므로 카메라가 주인공을 따라간다. 카메라 위치는 grid 의 원점(origin)으로 반영한다.

이 모듈은 pico2d 를 import 하지 않는다. 그리기는 전달받은 renderer 로만 한다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import InputState
from game.player.player import Player
from game.world.camera import Camera
from game.world.grid import Grid


class FieldScene:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.player = Player(grid, config.PLAYER_START_COL, config.PLAYER_START_ROW)
        self.camera = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, grid.width_px, grid.height_px)
        self._follow_player()

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        self.player.update(dt, input_state)
        self._follow_player()

    def _follow_player(self) -> None:
        # 보간 중인 그림 위치(칸 중심)를 따라가 스크롤이 칸 단위로 끊기지 않게 한다.
        vcol, vrow = self.player.mover.visual_position
        tile = self.grid.tile_size
        self.camera.follow((vcol + 0.5) * tile, (vrow + 0.5) * tile)
        self.grid.origin_x = -self.camera.left
        self.grid.origin_y = -self.camera.bottom

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
        grid = self.grid
        renderer.fill_screen(config.COLOR_BACKGROUND)
        renderer.draw_grid(grid, config.COLOR_GRID_LINE)

        self.player.draw(renderer)

        top = config.SCREEN_HEIGHT  # 글자는 카메라와 무관하게 화면에 고정
        renderer.draw_text(16, top - 24, "WASD / 방향키: 이동    ESC: 종료", config.COLOR_TEXT_DIM)
        player = self.player
        info = f"칸 ({player.col}, {player.row}) | 상태 {player.state} | 방향 {player.facing.name}"
        renderer.draw_text(16, top - 50, info, config.COLOR_TEXT_DIM)
