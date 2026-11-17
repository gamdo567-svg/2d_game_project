"""주인공 이동 확인용 장면.

- 글자 맵 파일(config.FIELD_MAP_PATH)의 칸 맵 위에서 주인공을 상하좌우 4방향으로 움직인다.
- 벽 칸으로는 들어갈 수 없다 (game/physics/collision.py). 벽은 타일 그림이 생기기 전까지 단색 칸으로 그린다.
- 맵이 화면보다 크므로 카메라가 주인공을 따라간다. 카메라 위치는 grid 의 원점(origin)으로 반영한다.

이 모듈은 pico2d 를 import 하지 않는다. 그리기는 전달받은 renderer 로만 한다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import InputState
from game.physics.collision import can_enter
from game.player.player import Player
from game.world.camera import Camera
from game.world.grid import Grid
from game.world.tile_map import TileMap


class FieldScene:
    def __init__(self, grid: Grid, tile_map: TileMap | None = None) -> None:
        self.grid = grid
        self.tile_map = tile_map or TileMap.load(config.FIELD_MAP_PATH)
        if (self.tile_map.cols, self.tile_map.rows) != (grid.cols, grid.rows):
            raise ValueError(f"맵 크기 {self.tile_map.cols}×{self.tile_map.rows} 가 격자 {grid.cols}×{grid.rows} 와 다릅니다.")
        start = self.tile_map.player_start or (config.PLAYER_START_COL, config.PLAYER_START_ROW)
        self.player = Player(grid, *start, can_enter=lambda col, row: can_enter(self.tile_map, col, row))
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
        for col, row in sorted(self.tile_map.walls):
            renderer.fill_tile(grid, col, row, config.COLOR_WALL_EDGE)
            renderer.fill_tile(grid, col, row, config.COLOR_WALL, inset=3)

        self.player.draw(renderer)

        top = config.SCREEN_HEIGHT  # 글자는 카메라와 무관하게 화면에 고정
        renderer.draw_text(16, top - 24, "WASD / 방향키: 이동    클릭: 공격(연타 3단 콤보)    Space: 점프    F: 패링    ESC: 종료", config.COLOR_TEXT_DIM)
        player = self.player
        info = f"칸 ({player.col}, {player.row}) | 상태 {player.state} | 방향 {player.facing.name}"
        renderer.draw_text(16, top - 50, info, config.COLOR_TEXT_DIM)
