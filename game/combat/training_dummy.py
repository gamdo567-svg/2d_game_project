"""연습용 허수아비(밀짚 더미): 공격 판정을 확인하기 위한 대상.

- 칸 하나를 차지하고 주인공이 지나가지 못한다 (장면의 충돌 판정에서 막음).
- 그림은 PixelLab 밀짚 더미 (2026-11-20 사용자 요청: RPG 게임의 더미처럼). 체력에 따라 3단계로 망가진다
  (멀쩡함 → 베인 자국·삐져나온 밀짚 → 머리가 기울고 팔 밀짚이 떨어져 나감).
- 맞으면: 하얗게 깜빡이고, 기둥 밑을 축으로 맞은 쪽으로 기울었다가 용수철처럼 몇 번 흔들리며 멈추고(감쇠 진동),
  살짝 눌렸다 펴지며, 밀짚 부스러기가 튀고, 피해 숫자가 떠오른다.
- 체력이 0 이 되면 무너지는 그림(8장)을 재생하고 부러진 밑동으로 DUMMY_DOWN_TIME 동안 있다가,
  체력을 채워 통 튀어 오르듯 다시 선다. 쓰러진 동안은 맞지 않는다.
모든 시간은 dt(초)로 계산한다. 그리기는 draw(renderer, grid) 에서 renderer 로만 한다 (pico2d 를 import 하지 않음).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from game import config
from game.combat.burn import Burn, BurnFlames, draw_burn
from game.world.grid import Grid


@dataclass
class DamagePopup:
    amount: int
    age: float = 0.0  # 초
    color: tuple[int, int, int] = config.COLOR_DAMAGE_TEXT  # 불 피해는 주황 (COLOR_BURN_TEXT)


@dataclass
class StrawBit:
    """튀는 밀짚 부스러기. 위치·속도는 기둥 밑(회전 축)에서 원본 픽셀 단위, 위쪽 +."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]
    age: float = 0.0


class Spring:
    """감쇠 용수철: 값이 rest 로 돌아가며 흔들린다. 빈도(Hz)와 감쇠비로 정한다."""

    def __init__(self, rest: float, frequency: float, damping: float) -> None:
        self.rest = rest
        self.value = rest
        self.velocity = 0.0
        self.k = (2 * math.pi * frequency) ** 2
        self.c = 2 * damping * 2 * math.pi * frequency

    def update(self, dt: float) -> None:
        # 작은 단계로 나눠 dt 가 커도 튀지 않게 (반암시적 오일러)
        steps = max(1, math.ceil(dt / 0.01))
        h = dt / steps
        for _ in range(steps):
            self.velocity += (-self.k * (self.value - self.rest) - self.c * self.velocity) * h
            self.value += self.velocity * h

    @property
    def settled(self) -> bool:
        return abs(self.value - self.rest) < 1e-3 and abs(self.velocity) < 1e-2


class TrainingDummy:
    def __init__(self, col: int, row: int, max_hp: int = config.DUMMY_MAX_HP) -> None:
        self.col = col
        self.row = row
        self.max_hp = max_hp
        self.hp = max_hp
        self.flash_left = 0.0
        self.down_left = 0.0  # 쓰러져 있는 남은 시간
        self.break_age = 0.0  # 무너지기 시작한 뒤 흐른 시간
        self.popups: list[DamagePopup] = []
        self.bits: list[StrawBit] = []
        self.lean = Spring(0.0, config.DUMMY_WOBBLE_FREQ, config.DUMMY_WOBBLE_DAMPING)  # 기울기(도), 오른쪽 +
        self.squash = Spring(1.0, config.DUMMY_SQUASH_FREQ, config.DUMMY_SQUASH_DAMPING)  # 세로 비율
        self._kick_sign = 1
        self.burn = Burn()  # 불 속성 칼에 맞으면 불이 붙음 (회피가 없어 다 탈 때까지 탐)
        self.flames = BurnFlames(config.BURN_ANCHORS_DUMMY)
        self._seed = (col * 7349 + row * 1973 + 17) & 0x7FFFFFFF

    # ----- 상태 -----
    @property
    def is_down(self) -> bool:
        return self.down_left > 0.0

    @property
    def stage(self) -> int:
        """망가진 단계 0~2 (체력 비율: 2/3 초과 0, 1/3 초과 1, 그 아래 2)."""
        ratio = self.hp / self.max_hp
        return 0 if ratio > 2 / 3 else 1 if ratio > 1 / 3 else 2

    @property
    def break_frame(self) -> int:
        """무너지는 그림 장 번호 (끝까지 가면 마지막 장 = 부러진 밑동)."""
        n = config.DUMMY_BREAK_FRAMES
        return min(n - 1, int(self.break_age / config.DUMMY_BREAK_TIME * n))

    @property
    def lean_degrees(self) -> float:
        return max(-config.DUMMY_WOBBLE_MAX, min(config.DUMMY_WOBBLE_MAX, self.lean.value))

    def _rand(self) -> float:
        """0~1 의사 난수 (허수아비마다 정해져 있어 테스트가 늘 같음)."""
        self._seed = (self._seed * 1103515245 + 12345) & 0x7FFFFFFF
        return self._seed / 0x7FFFFFFF

    def _spray(self, count: int, push: float, spread: float) -> None:
        colors = config.DUMMY_STRAW_COLORS
        for _ in range(count):
            self.bits.append(StrawBit(
                x=(self._rand() - 0.5) * 10, y=18 + self._rand() * 16,
                vx=push * (30 + self._rand() * 60) + (self._rand() - 0.5) * spread,
                vy=20 + self._rand() * 80, life=0.35 + self._rand() * 0.35,
                color=colors[int(self._rand() * len(colors)) % len(colors)]))

    # ----- 맞기 -----
    def take_hit(self, damage: int, direction: tuple[int, int]) -> bool:
        """맞는다. 쓰러져 있으면 맞지 않고 False. direction = 공격이 나아가는 방향 (칸 단위)."""
        if self.is_down:
            return False
        self.hp = max(0, self.hp - damage)
        self.flash_left = config.DUMMY_FLASH_TIME
        self.popups.append(DamagePopup(damage))
        dx = direction[0]
        if dx:  # 옆에서 맞으면 맞은 쪽(공격 방향)으로 기울었다 돌아옴
            sign, kick = (1 if dx > 0 else -1), config.DUMMY_WOBBLE_KICK
        else:  # 위·아래에서 맞으면 좌우로 번갈아 조금 흔들리고 더 크게 눌림
            self._kick_sign = -self._kick_sign
            sign, kick = self._kick_sign, config.DUMMY_WOBBLE_KICK * 0.55
        self.lean.velocity -= sign * kick  # 기울기 값은 반시계 + 라 오른쪽으로 기울면 음수 (lean_right 참고)
        self.squash.velocity -= config.DUMMY_SQUASH_KICK * (1.6 if not dx else 1.0)
        self._spray(config.DUMMY_HIT_BITS, sign if dx else 0, 60)
        if self.hp == 0:
            self._break()
        return True

    def ignite(self) -> None:
        """불 속성 공격에 맞음 (take_hit 다음에 부름). 쓰러져 있으면 붙지 않는다."""
        if not self.is_down:
            self.burn.ignite()

    def _break(self) -> None:
        self.down_left = config.DUMMY_DOWN_TIME
        self.break_age = 0.0
        self.burn.extinguish()
        self._spray(config.DUMMY_BREAK_BITS, 0, 160)

    @property
    def lean_right(self) -> float:
        """오른쪽(+x)으로 기운 정도(도). 그림은 반시계 + 로 돌리므로 -lean_right 로 돌린다."""
        return -self.lean_degrees

    # ----- 시간 -----
    def update(self, dt: float) -> None:
        self.flash_left = max(0.0, self.flash_left - dt)
        burn_damage = self.burn.update(dt)
        if burn_damage and not self.is_down:  # 불 피해: 흔들림 없이 체력만 (숫자는 주황)
            self.hp = max(0, self.hp - burn_damage)
            self.popups.append(DamagePopup(burn_damage, color=config.COLOR_BURN_TEXT))
            if self.hp == 0:
                self._break()
        self.flames.update(dt, self.burn.time_left)
        self.lean.update(dt)
        self.squash.update(dt)
        for popup in self.popups:
            popup.age += dt
        self.popups = [p for p in self.popups if p.age < config.DAMAGE_POPUP_TIME]
        for bit in self.bits:
            bit.age += dt
            bit.vy -= config.DUMMY_BIT_GRAVITY * dt
            bit.x += bit.vx * dt
            bit.y = max(0.0, bit.y + bit.vy * dt)
            if bit.y == 0.0:
                bit.vx *= 0.6
        self.bits = [b for b in self.bits if b.age < b.life]
        if self.is_down:
            self.break_age += dt
            self.down_left = max(0.0, self.down_left - dt)
            if not self.is_down:  # 다시 섬: 눌린 채 나타나 통 튀어 오르고, 밀짚이 조금 흩날림
                self.hp = self.max_hp
                self.lean.value, self.lean.velocity = 0.0, 0.0
                self.squash.value, self.squash.velocity = config.DUMMY_RESPAWN_SQUASH, 0.0
                self._spray(config.DUMMY_HIT_BITS, 0, 120)

    # ----- 그리기 -----
    def draw(self, renderer, grid: Grid) -> None:
        s = config.RENDER_SCALE
        left, bottom, right, _ = grid.tile_to_pixel_rect(self.col, self.row)
        px = (left + right) / 2  # 기둥 밑(회전 축)의 화면 위치
        py = bottom + config.DUMMY_FOOT_PAD * s
        w, h = config.DUMMY_SPRITE_SIZE
        pivot_x, pivot_y = config.DUMMY_PIVOT  # 원본 그림에서 (왼쪽부터, 위에서부터)
        draw_burn(renderer, self.flames, px, py, behind=True)
        if self.is_down:
            # 무너지는 그림 → 마지막 장(부러진 밑동). 회전 없이 기둥 밑을 축 자리에 맞춤
            renderer.draw_sprite_frame(config.DUMMY_BREAK_SHEET, self.break_frame, w, h,
                                       px + (w / 2 - pivot_x) * s, py - (h - pivot_y) * s, w * s, h * s)
        else:
            # 기둥 밑을 축으로 기울이고 세로로 눌림: 그림 가운데 = 축 + 돌린 (가운데 - 축)
            sq = self.squash.value
            angle = self.lean_degrees  # 반시계 +
            ox = (w / 2 - pivot_x) * s  # 그림 가운데의 축 기준 위치 (위쪽 +)
            oy = (pivot_y - h / 2) * s * sq
            a = math.radians(angle)
            cx = px + ox * math.cos(a) - oy * math.sin(a)
            cy = py + ox * math.sin(a) + oy * math.cos(a)
            renderer.draw_image_rotated(config.DUMMY_STAGE_IMAGES[self.stage], cx, cy, w * s, h * s * sq, angle)
            if self.flash_left > 0.0:
                renderer.draw_image_rotated(config.DUMMY_STAGE_WHITE[self.stage], cx, cy, w * s, h * s * sq, angle,
                                            opacity=self.flash_left / config.DUMMY_FLASH_TIME * 0.9)
            # 체력 막대 (머리 위)
            top = py + (pivot_y + 4) * s
            renderer.fill_rect(px - 10 * s, top, px + 10 * s, top + 2 * s, config.COLOR_DUMMY_SHADOW)
            renderer.fill_rect(px - 10 * s, top, px - 10 * s + 20 * s * self.hp / self.max_hp, top + 2 * s,
                               config.COLOR_DUMMY_HP)
        draw_burn(renderer, self.flames, px, py, behind=False)  # 타는 불꽃·불티·연기
        for bit in self.bits:
            bx, by = px + bit.x * s, py + bit.y * s
            renderer.fill_rect(bx, by, bx + 2 * s, by + 1 * s, bit.color)
        for popup in self.popups:
            rise = popup.age / config.DAMAGE_POPUP_TIME * config.DAMAGE_POPUP_RISE * grid.tile_size
            renderer.draw_text(px - 6 * s, py + (pivot_y + 10) * s + rise, str(popup.amount), popup.color)
