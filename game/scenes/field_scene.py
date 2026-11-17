"""주인공 이동 확인용 장면.

- 글자 맵 파일(config.FIELD_MAP_PATH)의 칸 맵 위에서 주인공을 상하좌우 4방향으로 움직인다.
- 벽 칸으로는 들어갈 수 없다 (game/physics/collision.py). 벽은 타일 그림이 생기기 전까지 단색 칸으로 그린다.
- 맵의 `D` 칸에 연습용 허수아비를 세운다. 허수아비 칸도 지나갈 수 없다.
- 주인공이 낸 공격(Strike)을 칸 단위로 판정해 닿는 칸의 허수아비·골렘에게 피해를 준다 (벽 너머는 맞지 않음).
- 맵의 `G` 칸에 골렘(2×2)을 둔다. 골렘이 낸 공격(EnemyAttack)은 주인공이 받는다 (패링·회피 무적·점프 판정은 Player).
  ① 내려찍기가 패링당하면 골렘의 패링 게이지가 찬다.
- 맵이 화면보다 크므로 카메라가 주인공을 따라간다. 카메라 위치는 grid 의 원점(origin)으로 반영한다.

이 모듈은 pico2d 를 import 하지 않는다. 그리기는 전달받은 renderer 로만 한다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import InputState
from game.combat.enemy_attack import PARRIED
from game.combat.strike import attack_tiles
from game.combat.training_dummy import TrainingDummy
from game.effects.effect import ScreenShake, SpriteEffect
from game.enemies.golem import Golem
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
        self.dummies = [TrainingDummy(col, row) for col, row in self.tile_map.dummies]
        self.golems = [Golem(col, row, self.tile_map.is_wall) for col, row in self.tile_map.golems]
        self.player = Player(grid, *start, can_enter=self.can_enter)
        self.camera = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, grid.width_px, grid.height_px)
        self.effects: list[SpriteEffect] = []  # 재생 중인 이펙트 (그리기 전용)
        self.shake = ScreenShake()
        self._follow_player()

    # ----- 로직 -----
    def can_enter(self, col: int, row: int) -> bool:
        """벽·허수아비·골렘이 있는 칸에는 들어갈 수 없다."""
        return (can_enter(self.tile_map, col, row)
                and not any((d.col, d.row) == (col, row) for d in self.dummies)
                and not any((col, row) in g.tiles for g in self.golems))

    def _golem_can_place(self, golem: Golem, col: int, row: int) -> bool:
        """골렘의 왼쪽 아래 칸을 (col, row) 에 둘 수 있는지: 2×2 가 모두 벽·허수아비·주인공·다른 골렘이 없는 칸."""
        player = (self.player.col, self.player.row)
        for c in range(col, col + golem.size):
            for r in range(row, row + golem.size):
                if not can_enter(self.tile_map, c, r) or (c, r) == player:
                    return False
                if any((d.col, d.row) == (c, r) for d in self.dummies):
                    return False
                if any((c, r) in g.tiles for g in self.golems if g is not golem):
                    return False
        return True

    def update(self, dt: float, input_state: InputState) -> None:
        self.player.update(dt, input_state)
        for strike in self.player.strikes:
            tiles = attack_tiles(strike, self.tile_map.is_wall)
            for dummy in self.dummies:
                if (dummy.col, dummy.row) in tiles:
                    dummy.take_hit(strike.damage, strike.direction)
            for golem in self.golems:
                if golem.tiles.intersection(tiles):
                    golem.take_hit(strike.damage, strike.direction)
        for dummy in self.dummies:
            dummy.update(dt)
        player_tile = (self.player.col, self.player.row)
        for golem in self.golems:
            golem.update(dt, player_tile, lambda c, r, g=golem: self._golem_can_place(g, c, r))
            for attack in golem.attacks:
                if self.player.receive_attack(attack) == PARRIED:
                    golem.on_parried()
            self._start_effects(golem.effects)
        self._update_effects(dt)
        self._follow_player()

    def _start_effects(self, effects: list[SpriteEffect]) -> None:
        for effect in effects:
            self.effects.append(effect)
            if effect.shake:
                self.shake.start(**effect.shake)

    def _update_effects(self, dt: float) -> None:
        for effect in self.effects:
            effect.update(dt)
        self.effects = [e for e in self.effects if not e.finished]
        self.shake.update(dt)

    def _follow_player(self) -> None:
        # 보간 중인 그림 위치(칸 중심)를 따라가 스크롤이 칸 단위로 끊기지 않게 한다.
        vcol, vrow = self.player.mover.visual_position
        tile = self.grid.tile_size
        self.camera.follow((vcol + 0.5) * tile, (vrow + 0.5) * tile)
        # 화면 흔들림은 카메라 위치에 더한다: 바닥·이펙트·인물이 모두 같이 흔들린다 (글자·체력 막대는 화면에 고정)
        shake_x, shake_y = self.shake.offset
        self.grid.origin_x = -self.camera.left + shake_x
        self.grid.origin_y = -self.camera.bottom + shake_y

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
        grid = self.grid
        renderer.fill_screen(config.COLOR_BACKGROUND)
        renderer.draw_grid(grid, config.COLOR_GRID_LINE)
        for col, row in sorted(self.tile_map.walls):
            renderer.fill_tile(grid, col, row, config.COLOR_WALL_EDGE)
            renderer.fill_tile(grid, col, row, config.COLOR_WALL, inset=3)

        for golem in self.golems:
            golem.draw_warning(renderer, grid)  # 공격 예고 칸·레이저는 바닥에
        for effect in self.effects:  # 바닥 이펙트 (금·솟은 바닥 판·돌): 인물보다 먼저
            self._draw_effect(renderer, effect)
        # 위쪽 행(멀리 있는 것)부터 그려서 아래쪽 행이 앞에 보이게 한다
        actors = [(dummy.row, dummy.draw) for dummy in self.dummies]
        actors += [(golem.visual_position[1], golem.draw) for golem in self.golems]
        actors.append((self.player.mover.visual_position[1], lambda r, g: self.player.draw(r)))
        for _, draw in sorted(actors, key=lambda a: -a[0]):
            draw(renderer, grid)

        self._draw_hud(renderer)

    def _draw_effect(self, renderer, effect: SpriteEffect) -> None:
        """이펙트 프레임 가운데를 터진 점(칸 좌표)의 픽셀 위치에 맞춰 그린다."""
        spec, grid = effect.spec, self.grid
        x = grid.origin_x + effect.x * grid.tile_size
        y = grid.origin_y + effect.y * grid.tile_size
        size = spec["frame_size"]
        renderer.draw_sheet_frame(str(spec["path"]), effect.frame_index, spec["columns"], size, size,
                                  x, y, size * config.RENDER_SCALE, size * config.RENDER_SCALE)

    def _draw_hud(self, renderer) -> None:
        top = config.SCREEN_HEIGHT  # 글자는 카메라와 무관하게 화면에 고정
        renderer.draw_text(16, top - 24, "WASD / 방향키: 이동    클릭: 공격(연타 3단 콤보)    Space: 점프    F: 패링    Q: 회피    ESC: 종료", config.COLOR_TEXT_DIM)
        player = self.player
        info = f"칸 ({player.col}, {player.row}) | 상태 {player.state} | 방향 {player.facing.name}"
        renderer.draw_text(16, top - 50, info, config.COLOR_TEXT_DIM)
        # 주인공 체력·패링 게이지 (화면 왼쪽 위에 고정)
        renderer.draw_text(16, top - 76, "HP", config.COLOR_TEXT_DIM)
        renderer.fill_rect(48, top - 84, 248, top - 70, config.COLOR_BAR_BACK)
        renderer.fill_rect(48, top - 84, 48 + 200 * player.hp / player.max_hp, top - 70, config.COLOR_PLAYER_HP)
        renderer.fill_rect(48, top - 92, 248, top - 86, config.COLOR_BAR_BACK)
        renderer.fill_rect(48, top - 92, 48 + 200 * player.posture.value, top - 86, config.COLOR_POSTURE)
