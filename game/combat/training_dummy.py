"""연습용 허수아비: 공격 판정을 확인하기 위한 대상.

- 칸 하나를 차지하고 주인공이 지나가지 못한다 (장면의 충돌 판정에서 막음).
- 맞으면 하얗게 깜빡이고, 공격 방향으로 그림만 잠깐 흔들리고, 피해 숫자가 떠오른다.
- 체력이 0 이 되면 쓰러졌다가 DUMMY_DOWN_TIME 뒤에 체력을 채워 다시 선다. 쓰러진 동안은 맞지 않는다.
모든 시간은 dt(초)로 계산한다. 그리기는 draw(renderer, grid) 에서 renderer 로만 한다.
"""
from __future__ import annotations

from dataclasses import dataclass

from game import config
from game.world.grid import Grid


@dataclass
class DamagePopup:
    amount: int
    age: float = 0.0  # 초


class TrainingDummy:
    def __init__(self, col: int, row: int, max_hp: int = config.DUMMY_MAX_HP) -> None:
        self.col = col
        self.row = row
        self.max_hp = max_hp
        self.hp = max_hp
        self.flash_left = 0.0
        self.shake_left = 0.0
        self.shake_direction = (0, 0)
        self.down_left = 0.0  # 쓰러져 있는 남은 시간
        self.popups: list[DamagePopup] = []

    @property
    def is_down(self) -> bool:
        return self.down_left > 0.0

    def take_hit(self, damage: int, direction: tuple[int, int]) -> bool:
        """맞는다. 쓰러져 있으면 맞지 않고 False."""
        if self.is_down:
            return False
        self.hp = max(0, self.hp - damage)
        self.flash_left = config.DUMMY_FLASH_TIME
        self.shake_left = config.DUMMY_SHAKE_TIME
        self.shake_direction = direction
        self.popups.append(DamagePopup(damage))
        if self.hp == 0:
            self.down_left = config.DUMMY_DOWN_TIME
        return True

    def update(self, dt: float) -> None:
        self.flash_left = max(0.0, self.flash_left - dt)
        self.shake_left = max(0.0, self.shake_left - dt)
        for popup in self.popups:
            popup.age += dt
        self.popups = [p for p in self.popups if p.age < config.DAMAGE_POPUP_TIME]
        if self.is_down:
            self.down_left = max(0.0, self.down_left - dt)
            if not self.is_down:
                self.hp = self.max_hp  # 다시 일어남

    def shake_offset(self) -> tuple[float, float]:
        """흔들림: 맞은 방향으로 밀렸다가 돌아오는 그림 위치 (원본 픽셀, 위쪽 +)."""
        if self.shake_left <= 0.0:
            return 0.0, 0.0
        k = config.DUMMY_SHAKE_PIXELS * self.shake_left / config.DUMMY_SHAKE_TIME
        return self.shake_direction[0] * k, self.shake_direction[1] * k

    # ----- 그리기 (임시 도형: 그림이 생기기 전까지) -----
    def draw(self, renderer, grid: Grid) -> None:
        s = config.RENDER_SCALE
        left, bottom, right, _ = grid.tile_to_pixel_rect(self.col, self.row)
        ox, oy = self.shake_offset()
        cx = (left + right) / 2 + ox * s
        base = bottom + oy * s
        white = self.flash_left > 0.0
        wood = config.COLOR_WHITE if white else config.COLOR_DUMMY_WOOD
        straw = config.COLOR_WHITE if white else config.COLOR_DUMMY_STRAW
        renderer.fill_rect(cx - 10 * s, base + 1 * s, cx + 10 * s, base + 3 * s, config.COLOR_DUMMY_SHADOW)
        if self.is_down:
            # 쓰러짐: 기둥이 옆으로 누움
            renderer.fill_rect(cx - 13 * s, base + 2 * s, cx + 7 * s, base + 6 * s, wood)
            renderer.fill_rect(cx + 7 * s, base + 1 * s, cx + 15 * s, base + 8 * s, straw)
        else:
            renderer.fill_rect(cx - 2 * s, base + 2 * s, cx + 2 * s, base + 30 * s, wood)        # 기둥
            renderer.fill_rect(cx - 10 * s, base + 20 * s, cx + 10 * s, base + 23 * s, wood)     # 팔
            renderer.fill_rect(cx - 6 * s, base + 10 * s, cx + 6 * s, base + 24 * s, straw)      # 몸통(짚)
            renderer.fill_rect(cx - 5 * s, base + 25 * s, cx + 5 * s, base + 34 * s, straw)      # 머리
            # 체력 막대
            top = base + 37 * s
            renderer.fill_rect(cx - 10 * s, top, cx + 10 * s, top + 2 * s, config.COLOR_DUMMY_SHADOW)
            renderer.fill_rect(cx - 10 * s, top, cx - 10 * s + 20 * s * self.hp / self.max_hp, top + 2 * s,
                               config.COLOR_DUMMY_HP)
        for popup in self.popups:
            rise = popup.age / config.DAMAGE_POPUP_TIME * config.DAMAGE_POPUP_RISE * grid.tile_size
            renderer.draw_text(cx - 6 * s, base + 44 * s + rise, str(popup.amount), config.COLOR_DAMAGE_TEXT)
