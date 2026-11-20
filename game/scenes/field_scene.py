"""주인공 이동 확인용 장면.

- 글자 맵 파일(config.FIELD_MAP_PATH)의 칸 맵 위에서 주인공을 상하좌우 4방향으로 움직인다.
- 벽 칸으로는 들어갈 수 없다 (game/physics/collision.py). 벽은 타일 그림이 생기기 전까지 단색 칸으로 그린다.
- 맵의 `D` 칸에 연습용 허수아비를 세운다. 허수아비 칸도 지나갈 수 없다.
- 주인공이 낸 공격(Strike)을 칸 단위로 판정해 닿는 칸의 허수아비·골렘에게 피해를 준다 (벽 너머는 맞지 않음).
- 맵의 `G` 칸에 골렘(1×2)을 둔다. 골렘이 낸 공격(EnemyAttack)은 주인공이 받는다 (패링·회피 무적·점프 판정은 Player).
  ① 내려찍기가 패링당하면 골렘의 패링 게이지가 찬다.
- 맵이 화면보다 크므로 카메라가 주인공을 따라간다. 카메라 위치는 grid 의 원점(origin)으로 반영한다.

이 모듈은 pico2d 를 import 하지 않는다. 그리기는 전달받은 renderer 로만 한다.
"""
from __future__ import annotations

import json
import math
import os

from game import config
from game.input.input_state import InputState
from game.combat.enemy_attack import PARRIED
from game.combat.strike import attack_tiles
from game.combat.training_dummy import TrainingDummy
from game.effects.effect import ScreenShake, SpriteEffect
from game.enemies.aggro import AggroTracker
from game.enemies.golem import Golem
from game.physics.collision import can_enter
from game.player.player import Player, parry_spark_point
from game.world.camera import Camera
from game.world.grid import Grid
from game.world.tile_map import TileMap


def load_torches(path: str) -> dict | None:
    """맵 그림을 만들 때 내보낸 횃불 자리 (없으면 None)."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def torch_glow_opacity(time: float, index: int) -> float:
    """횃불 빛 고리 불투명도: 빠르기가 다른 두 사인파를 섞어 불규칙하게 깜빡임 (횃불마다 박자가 다름)."""
    phase = index * 1.7
    swing = 0.6 * math.sin(time * 7.3 + phase) + 0.4 * math.sin(time * 12.9 + phase * 2.3)
    return max(0.0, min(1.0, config.MAP_TORCH_GLOW_BASE + config.MAP_TORCH_GLOW_SWING * swing))


class FieldScene:
    def __init__(self, grid: Grid, tile_map: TileMap | None = None) -> None:
        self.grid = grid
        # 바탕 그림은 기본 맵 파일에 짝지은 것만 쓴다 (테스트 등에서 맵을 직접 넘기면 단색 네모로 그림)
        self.map_background = (config.map_background_path(config.FIELD_MAP_PATH)
                                if tile_map is None else None)
        self.map_walltop = config.map_walltop_path(config.FIELD_MAP_PATH) if tile_map is None else None
        self.torches = load_torches(config.map_torches_path(config.FIELD_MAP_PATH)) if tile_map is None else None
        self.time = 0.0  # 장면이 흐른 시간 (횃불 불꽃·빛 깜빡임)
        self.tile_map = tile_map or TileMap.load(config.FIELD_MAP_PATH)
        if (self.tile_map.cols, self.tile_map.rows) != (grid.cols, grid.rows):
            raise ValueError(f"맵 크기 {self.tile_map.cols}×{self.tile_map.rows} 가 격자 {grid.cols}×{grid.rows} 와 다릅니다.")
        start = self.tile_map.player_start or (config.PLAYER_START_COL, config.PLAYER_START_ROW)
        self.dummies = [TrainingDummy(col, row) for col, row in self.tile_map.dummies]
        # 몬스터는 휴면으로 시작하고, 주인공은 한 번에 한 마리만 끈다 (2026-11-20 어그로 시스템)
        self.golems = [Golem(col, row, self.tile_map.is_wall, dormant=True) for col, row in self.tile_map.golems]
        self.aggro = AggroTracker()
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
        """골렘의 왼쪽 아래 칸을 (col, row) 에 둘 수 있는지: 몸 칸(1×2)이 모두 벽·허수아비·주인공·다른 골렘이 없는 칸."""
        player = (self.player.col, self.player.row)
        for c in range(col, col + golem.width):
            for r in range(row, row + golem.height):
                if not can_enter(self.tile_map, c, r) or (c, r) == player:
                    return False
                if any((d.col, d.row) == (c, r) for d in self.dummies):
                    return False
                if any((c, r) in g.tiles for g in self.golems if g is not golem):
                    return False
        return True

    def update(self, dt: float, input_state: InputState) -> None:
        self.time += dt
        self.player.update(dt, input_state)
        for shake in self.player.shake_requests:  # 검 속성이 다 차오른 순간 등
            self.shake.start(**shake)
        for strike in self.player.strikes:
            tiles = attack_tiles(strike, self.tile_map.is_wall)
            for dummy in self.dummies:
                if (dummy.col, dummy.row) in tiles and dummy.take_hit(strike.damage, strike.direction):
                    if strike.element == config.BURN_ELEMENT:
                        dummy.ignite()  # 불 속성 칼: 불이 붙음
            for golem in self.golems:
                if golem.tiles.intersection(tiles) and golem.take_hit(strike.damage, strike.direction):
                    self.aggro.on_hit(golem)  # 휴면 중에 맞으면 (끈 몬스터가 없을 때) 깨어나 끌림
                    if strike.element == config.BURN_ELEMENT:
                        golem.ignite()
        for dummy in self.dummies:
            dummy.update(dt)
        player_tile = (self.player.col, self.player.row)
        self.aggro.update(player_tile, self.golems)
        for golem in self.golems:
            golem.update(dt, player_tile, lambda c, r, g=golem: self._golem_can_place(g, c, r))
            for attack in golem.attacks:
                result = self.player.receive_attack(attack)
                # 막지 못한 빨강·노랑 공격은 레이저 스택, 맞은 것은 세지 않음 (2026-11-18 사용자 결정)
                golem.on_attack_result(attack, result, self.player.last_perfect_dodge)
                if self.player.last_perfect_dodge:
                    golem.on_perfect_dodged()  # 퍼펙트 회피당하면 패링 게이지가 찬다 (2026-11-18 사용자 요청)
                if result == PARRIED:
                    golem.on_parried()
                    # 패링 성공: 칼이 막은 자리에서 노란 불꽃 (2026-11-17 사용자 요청)
                    point = parry_spark_point(self.player.col, self.player.row, self.player.facing)
                    self._start_effects([SpriteEffect(config.PARRY_SPARK_EFFECT, *point)])
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
    def _draw_map_background(self, renderer) -> bool:
        """맵 바탕 그림(지하 미궁 타일을 미리 합친 한 장)을 그린다. 그림이 없거나 못 읽으면 False."""
        if not self.map_background or not os.path.exists(self.map_background):
            return False
        grid = self.grid
        width, height = grid.cols * config.LOGICAL_TILE_SIZE, grid.rows * config.LOGICAL_TILE_SIZE
        return renderer.draw_sprite_frame(
            self.map_background, 0, width, height,
            grid.origin_x + grid.width_px / 2, grid.origin_y, grid.width_px, grid.height_px,
        )

    def _draw_torches(self, renderer) -> None:
        """벽 횃불: 따뜻한 빛 고리(불투명도가 두 사인파로 흔들림) → 불꽃 그림. 횃불마다 박자를 어긋나게 한다."""
        if not self.torches:
            return
        grid, scale = self.grid, config.RENDER_SCALE
        map_height = grid.rows * config.LOGICAL_TILE_SIZE
        info = self.torches
        fw, fh, frames = info["frame_width"], info["frame_height"], info["frames"]
        for k, spot in enumerate(info["torches"]):
            x = grid.origin_x + spot["x"] * scale
            flame_y = grid.origin_y + (map_height - spot["flame_y"]) * scale
            bottom = grid.origin_y + (map_height - spot["bottom"]) * scale
            opacity = torch_glow_opacity(self.time, k)
            renderer.draw_image_centered(config.MAP_TORCH_GLOW, x, flame_y, opacity=opacity)
            frame = int(self.time * config.MAP_TORCH_FPS + k * 3) % frames
            renderer.draw_sprite_frame(config.MAP_TORCH_SHEET, frame, fw, fh, x, bottom, fw * scale, fh * scale)

    def _draw_walltop_band(self, renderer, row: int) -> None:
        """칸 줄 row 의 벽 가운데 위가 바닥인 칸의 솟은 윗면 (그 줄 칸 위쪽 경계 바로 위에 붙음)."""
        grid = self.grid
        band = config.MAP_WALL_OVERHANG
        width = grid.cols * config.LOGICAL_TILE_SIZE
        height = band * config.RENDER_SCALE
        top_of_row = grid.origin_y + (row + 1) * grid.tile_size
        renderer.draw_sheet_frame(self.map_walltop, self.tile_map.rows - 1 - row, 1, width, band,
                                  grid.origin_x + grid.width_px / 2, top_of_row + height / 2, grid.width_px, height)

    def draw(self, renderer) -> None:
        grid = self.grid
        renderer.fill_screen(config.COLOR_BACKGROUND)
        if not self._draw_map_background(renderer):
            renderer.draw_grid(grid, config.COLOR_GRID_LINE)
            for col, row in sorted(self.tile_map.walls):
                renderer.fill_tile(grid, col, row, config.COLOR_WALL_EDGE)
                renderer.fill_tile(grid, col, row, config.COLOR_WALL, inset=3)
        self._draw_torches(renderer)

        for golem in self.golems:
            golem.draw_warning(renderer, grid)  # 공격 예고 칸·레이저는 바닥에
        for effect in self.effects:  # 바닥 이펙트 (금·솟은 바닥 판·돌): 인물보다 먼저
            if not effect.spec.get("on_top"):
                self._draw_effect(renderer, effect)
        # 위쪽 행(멀리 있는 것)부터 그려서 아래쪽 행이 앞에 보이게 한다
        actors = [(dummy.row, dummy.draw) for dummy in self.dummies]
        actors += [(golem.visual_position[1], golem.draw) for golem in self.golems]
        actors.append((self.player.mover.visual_position[1], lambda r, g: self.player.draw(r)))
        # 솟은 벽 윗면 띠: 줄 R 의 띠는 위 칸(R+1)에 선 인물보다 나중에, 줄 R 인물보다 먼저 (벽 뒤 인물의 발을 가림)
        if self.map_walltop and os.path.exists(self.map_walltop):
            actors += [(row + 0.5, lambda r, g, row=row: self._draw_walltop_band(r, row))
                       for row in range(self.tile_map.rows - 1)]
        for _, draw in sorted(actors, key=lambda a: -a[0]):
            draw(renderer, grid)
        for effect in self.effects:  # 인물 위에 그리는 이펙트 (패링 불꽃)
            if effect.spec.get("on_top"):
                self._draw_effect(renderer, effect)

        self._draw_hud(renderer)

    def _draw_effect(self, renderer, effect: SpriteEffect) -> None:
        """이펙트 프레임 가운데를 터진 점(칸 좌표)의 픽셀 위치에 맞춰 그린다."""
        spec, grid = effect.spec, self.grid
        x = grid.origin_x + effect.x * grid.tile_size
        y = grid.origin_y + effect.y * grid.tile_size
        size = spec["frame_size"]
        tiles = spec.get("draw_tiles")  # 범위 칸 수에 맞춰 그릴 때 (없으면 원본 × RENDER_SCALE)
        draw = tiles * grid.tile_size if tiles else size * config.RENDER_SCALE
        renderer.draw_sheet_frame(str(spec["path"]), effect.frame_index, spec["columns"], size, size, x, y, draw, draw)

    def _draw_hud(self, renderer) -> None:
        top = config.SCREEN_HEIGHT  # 화면에 고정 (카메라와 무관)
        player = self.player
        # 조작 안내·칸/상태 글자는 지저분해 보여 지움 (2026-11-17 사용자 요청). 체력·패링 게이지만 왼쪽 위에.
        renderer.draw_text(16, top - 24, "HP", config.COLOR_TEXT_DIM)
        renderer.fill_rect(48, top - 32, 248, top - 18, config.COLOR_BAR_BACK)
        renderer.fill_rect(48, top - 32, 48 + 200 * player.hp / player.max_hp, top - 18, config.COLOR_PLAYER_HP)
        renderer.fill_rect(48, top - 40, 248, top - 34, config.COLOR_BAR_BACK)
        renderer.fill_rect(48, top - 40, 48 + 200 * player.posture.value, top - 34, config.COLOR_POSTURE)
        # 검 속성 (2026-11-20): 1·2·3 으로 고른 속성, 검에 입혀져 있으면 표시
        enchant = player.enchant
        label = f"속성 {config.SWORD_ELEMENT_NAMES[enchant.selected]}"
        if enchant.active is not None:
            label += f" · 검: {config.SWORD_ELEMENT_NAMES[enchant.active]}"
        renderer.draw_text(16, top - 58, label, config.SWORD_ELEMENT_COLORS[enchant.selected])
