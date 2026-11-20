"""주인공: 칸 이동(상하좌우), 바라보는 방향, 상태 머신, 애니메이션, 점프·패링·검 공격을 묶는다.

- 논리적 위치와 충돌 영역은 칸 하나 (self.col, self.row) 이다. 점프해도 칸 위치는 그대로다.
- 그림 크기(원본 32×48, 화면 표시 64×96)는 그리기에만 쓰며 충돌 판정과 무관하다.
- 캐릭터 본체 그림과 장비를 따로 그린다. 지금은 공격 중에만 검 그림 한 장을 손 위치·각도에 맞춰 겹쳐 그린다.
- 점프·패링·공격·회피는 서 있거나 걷는 중에만 시작하고, 누르면 바로 시작한다 (진행 중인 한 칸 이동은 마저 간다,
  점프는 공중에서). 행동 중에는 새 이동을 하지 않는다.
- 입력 기억: 행동을 지금 할 수 없을 때 누른 키를 PLAYER_INPUT_BUFFER_TIME 동안 기억했다가 할 수 있게 되면 실행한다.
- 공격은 3단 콤보(SwordCombo). 공격 중 클릭하면 다음 타가 이어지고, 3타 뒤에는 잠시 공격만 할 수 없다.
- 공격 그림은 검이 몸 밖으로 나가므로 96×64 캔버스, 타마다 8프레임이다 (2026-11-17 PixelLab).
  측면·정면 그림이 있고(정면 3타는 예전 5프레임, 후면은 없어 측면), 왼쪽은 측면을 좌우 반전한다.
"""
from __future__ import annotations

from dataclasses import dataclass

import math

import os

from game import config
from game.input.input_state import Action, InputState
from game.combat.enemy_attack import AVOIDED, HIT, MISSED, PARRIED, EnemyAttack
from game.combat.posture import PostureGauge
from game.combat.strike import Strike
from game.player.actions import Dodge, Jump, Parry, SwordCombo, TimedAction, frame_for_progress
from game.player.animation import LoopAnimation
from game.player.facing import Facing, facing_for_direction, sprite_view
from game.player.movement import CanEnter, GridMover
from game.player.enchant import SwordEnchant
from game.player.enchant_fx import EnchantFX
from game.player.sword_dark import DarkField
from game.player.sword_lightning import SWORD_SHAPE, BladeShape, LightningField
from game.player.state_machine import (ATTACK, DODGE, ENCHANT, FREE_STATES, HURT, IDLE, JUMP, PARRY, WALK,
                                       PlayerStateMachine)
from game.world.grid import Grid


@dataclass
class Afterimage:
    """회피 잔상 하나 (그리기 전용): 그 순간의 그림 위치(칸, 실수)·방향·회피 그림 번호, 지난 시간."""
    col: float
    row: float
    view: str
    flip: bool
    frame: int
    age: float = 0.0


def dodge_ghost_sheet_path(view: str) -> str:
    """퍼펙트 회피 잔상 그림 (회피 그림을 그림자처럼 바꾼 것). 예: dodge_ghost/side.png"""
    return str(config.PLAYER_IMAGE_DIR / "dodge_ghost" / f"{view}.png")


def sprite_sheet_path(state: str, view: str) -> str:
    """상태·원본 방향에 해당하는 스프라이트 시트 경로. 예: idle/front.png"""
    return str(config.PLAYER_IMAGE_DIR / state / f"{view}.png")


def attack_sheet_path(hit_number: int, view: str = "side") -> str:
    """콤보 타별 공격 시트 경로. 예: sword_attack/side_1.png"""
    return sprite_sheet_path(ATTACK, f"{view}_{hit_number}")


def attack_hand_sheet_path(hit_number: int, view: str = "side") -> str:
    """콤보 타별 오른손 레이어 시트 경로 (칼 위에 그리는 오른손 주먹만). 예: sword_attack/side_1_hand.png"""
    return sprite_sheet_path(ATTACK, f"{view}_{hit_number}_hand")


# 방향별 공격 칼 위치표. 타 하나가 None 이면 그 방향 그림이 없어 측면을 쓴다.
ATTACK_SWORD_TABLES = {
    "side": config.PLAYER_ATTACK_SWORD,
    "front": config.PLAYER_ATTACK_SWORD_FRONT,
    "back": config.PLAYER_ATTACK_SWORD_BACK,
}
# 방향별 타별 프레임 표 (None = 같은 간격)
ATTACK_FRAME_ENDS = {
    "front": config.PLAYER_ATTACK_FRAME_ENDS_FRONT,
    "back": config.PLAYER_ATTACK_FRAME_ENDS_BACK,
}


def attack_view(facing: Facing, hit_index: int = 0) -> str:
    """공격 그림 방향: 아래 = front, 위 = back, 좌우 = side. 그 방향에 이 타의 그림이 없으면 side."""
    view, _ = sprite_view(facing)
    table = ATTACK_SWORD_TABLES.get(view)
    if table is None or table[hit_index] is None:
        return "side"
    return view


def parry_sheet_path(view: str) -> str:
    """패링 시트 경로 (몸, 칼 없음). 예: parry/side.png"""
    return str(config.PLAYER_IMAGE_DIR / "parry" / f"{view}.png")


def parry_hand_sheet_path(view: str) -> str:
    """패링 오른손 레이어 시트 경로. 예: parry/side_hand.png"""
    return str(config.PLAYER_IMAGE_DIR / "parry" / f"{view}_hand.png")


def parry_spark_point(col: int, row: int, facing: Facing) -> tuple[float, float]:
    """패링 성공 이펙트가 터지는 점 (칸 좌표, 실수): 바라보는 쪽 칼이 막는 자리."""
    dx, dy = facing.value
    forward, up = config.PARRY_SPARK_OFFSET
    if dy:
        # 위·아래를 볼 때는 칼이 몸 앞 가슴 높이에서 막는다: 칼날 쪽으로 조금.
        # 정면은 칼이 화면 오른쪽, 후면은 화면 왼쪽 위로 기운다 (2026-11-18 후면 패링 그림)
        side = config.PARRY_SPARK_FRONT_SIDE if dy < 0 else -config.PARRY_SPARK_FRONT_SIDE
        return col + 0.5 + side, row + up
    return col + 0.5 + dx * forward, row + up


def weapon_sheet_path(weapon: str) -> str:
    """무기 그림 경로 (칼 한 장). 예: weapons/old_sword.png"""
    return str(config.PLAYER_IMAGE_DIR / "weapons" / f"{weapon}.png")


def weapon_back_path(weapon: str, view: str) -> str:
    """등에 멘 칼 그림 경로 (64×64, 아래 가운데가 발 밑). 예: weapons/old_sword_back_front.png"""
    return str(config.PLAYER_IMAGE_DIR / "weapons" / f"{weapon}_back_{view}.png")


def weapon_view_art_path(weapon: str, view: str, hit_number: int) -> str:
    """무기의 찌르기용 칼 그림 시트 경로 (공격 시트와 같은 칸). 예: weapons/old_sword_front_3.png"""
    return str(config.PLAYER_IMAGE_DIR / "weapons" / f"{weapon}_{view}_{hit_number}.png")


SHADOW_PATH = str(config.PLAYER_IMAGE_DIR / "shadow.png")
# 입력을 기억해 두는 행동 (PLAYER_INPUT_BUFFER_TIME)
BUFFERED_ACTIONS = (Action.ATTACK, Action.PARRY, Action.DODGE, Action.JUMP, Action.ENCHANT)
ELEMENT_KEYS = (Action.ELEMENT_1, Action.ELEMENT_2, Action.ELEMENT_3)  # 속성 고르기 (불·전기·어둠)
# 전용 그림이 아직 없는 상태 -> 대신 쓸 그림 상태. 패링은 공격 모션과 함께 만들 때까지 서 있는 그림(첫 프레임).
SPRITE_FALLBACK = {PARRY: IDLE, HURT: IDLE, ENCHANT: IDLE}  # 속성 입히기는 패링 막기 자세(그림이 없으면 서기)
# 대신 쓰는 그림을 자기 애니메이션 프레임으로 재생하는 상태 (나머지는 첫 프레임에 멈춤)
ANIMATED_FALLBACK = {DODGE}
# 좌우가 비대칭인 상태: 왼쪽을 볼 때 측면을 뒤집지 않고 전용 그림(side_left)을 쓴다.
# (예전 점프는 오른손으로 후드를 잡아 썼으나, 2026-11-17 점프 그림은 후드를 잡지 않아 지금은 없음)
LEFT_SHEET_STATES: set[str] = set()


class Player:
    def __init__(self, grid: Grid, col: int, row: int, can_enter: CanEnter | None = None) -> None:
        """can_enter(col, row): 들어갈 수 있는 칸인지 (벽 충돌). 없으면 격자 안이면 된다."""
        self.grid = grid
        self.strikes: list[Strike] = []
        self._last_strike: tuple[int, int] | None = None
        self.mover = GridMover(grid, col, row, speed=config.PLAYER_MOVE_SPEED, can_enter=can_enter)
        self.facing = Facing.DOWN
        self.jump = Jump(config.PLAYER_JUMP_DURATION, config.PLAYER_JUMP_HEIGHT, config.PLAYER_JUMP_FRAME_ENDS,
                         config.PLAYER_JUMP_LANDING_FRAMES, config.PLAYER_JUMP_TAKEOFF_FRAMES)
        self.parry = Parry(config.PLAYER_PARRY_DURATION, config.PLAYER_PARRY_WINDOW, frame_count=1)
        self.combo = SwordCombo(
            config.PLAYER_ATTACK_DURATIONS, config.PLAYER_ATTACK_FRAME_ENDS,
            config.PLAYER_ATTACK_COMBO_WINDOW, config.PLAYER_ATTACK_COOLDOWN,
        )
        self.dodge = Dodge(config.PLAYER_DODGE_DURATION, config.PLAYER_DODGE_MOVE_FRAMES)
        self.dodge_tail_left = 0.0  # 회피가 끝난 뒤 멈춤 그림을 더 보여 줄 남은 시간 (그림만)
        # 회피 잔상 (2026-11-18 사용자 요청): 퍼펙트든 아니든 회피하며 지나온 자리에 남는다
        self._trail_clock = 0.0
        self.afterimages: list[Afterimage] = []
        self.hurt = TimedAction(config.PLAYER_HURT_TIME, 1)
        self.enchant = SwordEnchant()  # 검 속성 (1·2·3 고르기, E 입히기)
        self.effect_clock = 0.0  # 검 이펙트 반복 재생 시간
        # 전기·어둠 이펙트는 시트 대신 게임이 도는 동안 계산해 만든다 (SWORD_PROCEDURAL_ELEMENTS)
        self.procedural = {"lightning": LightningField(), "dark": DarkField()}
        self.fx = EnchantFX()  # 입히기 폭발·털어내기 입자
        self._pending_fx: list[tuple[str, str]] = []  # 그릴 때 칼 자리를 알고 시작할 (종류, 속성)
        self._flicked = False  # 이번 입히기에서 털어내기 입자를 냈는지
        self.shake_requests: list[dict] = []  # 장면이 읽어 화면을 흔든다
        self.max_hp = config.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.posture = PostureGauge()
        self.hit_flash_left = 0.0
        self.parry_succeeded = False  # 이번 패링에서 공격을 막았는지 (우선권)
        # 퍼펙트 회피: 회피를 시작한 칸과 그 뒤 지난 시간, 이번 회피가 퍼펙트였는지, 머리 위 표시 시간
        self._dodge_start_tile: tuple[int, int] | None = None
        self._since_dodge = float("inf")
        self._perfect_this_dodge = False
        self.perfect_text_left = 0.0
        self.last_perfect_dodge = False  # 마지막으로 받은 공격을 퍼펙트 회피했는지
        self.dodge_cooldown_left = 0.0  # 회피를 다시 쓸 수 있을 때까지 남은 시간
        # 상태별 애니메이션. 점프·패링·회피는 행동 진행도에 맞춰 프레임을 고른다.
        self.animations: dict[str, LoopAnimation | Jump | Parry | SwordCombo | Dodge] = {
            IDLE: LoopAnimation(config.PLAYER_IDLE_FRAMES, config.PLAYER_IDLE_FRAME_DURATION),
            WALK: LoopAnimation(config.PLAYER_WALK_FRAMES, config.PLAYER_WALK_FRAME_DURATION),
            JUMP: self.jump,
            PARRY: self.parry,
            ATTACK: self.combo,
            DODGE: self.dodge,
            HURT: self.hurt,
            ENCHANT: self.enchant,
        }
        self._buffer: dict[Action, float] = {}  # 입력 기억: 행동 → 남은 시간
        self.fsm = PlayerStateMachine(on_state_changed=self._on_state_changed)

    # ----- 상태 조회 -----
    @property
    def col(self) -> int:
        return self.mover.col

    @property
    def row(self) -> int:
        return self.mover.row

    @property
    def is_invincible(self) -> bool:
        """무적: 회피 중 내내 (몬스터를 만들면 피해 판정에서 확인한다)."""
        return self.state == DODGE

    @property
    def state(self) -> str:
        return self.fsm.state

    @property
    def animation(self) -> LoopAnimation | Jump | Parry | SwordCombo | Dodge:
        return self.animations[self.state]

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        self.strikes: list[Strike] = []  # 이번 프레임에 낸 공격 (장면이 판정한다)
        self._input = input_state
        self.combo.tick(dt)
        self.dodge_cooldown_left = max(0.0, self.dodge_cooldown_left - dt)
        self.dodge_tail_left = max(0.0, self.dodge_tail_left - dt)
        for ghost in self.afterimages:
            ghost.age += dt
        self.afterimages = [g for g in self.afterimages if g.age < config.PLAYER_AFTERIMAGE_TIME]
        self.hit_flash_left = max(0.0, self.hit_flash_left - dt)
        self.perfect_text_left = max(0.0, self.perfect_text_left - dt)
        self._since_dodge += dt
        self.posture.update(dt)
        self.effect_clock += dt
        self.shake_requests = []
        self.fx.update(dt)
        for index, action in enumerate(ELEMENT_KEYS):
            if input_state.was_pressed(action):
                self.enchant.select(index)
        # 입력 기억: 이번 프레임에 누른 행동을 PLAYER_INPUT_BUFFER_TIME 동안 기억한다
        for action in BUFFERED_ACTIONS:
            if input_state.was_pressed(action):
                self._buffer[action] = config.PLAYER_INPUT_BUFFER_TIME
        # 공격 버튼을 누르고 있으면 콤보가 이어진다 (2026-11-18 사용자 요청). 쿨타임은 그대로.
        # 공격 중에는 보지 않고 한 타가 끝난 뒤에만 본다: 공격 중에도 보면 한 번 클릭한 짧은 순간(눌린 0.1초쯤)에
        # 다음 타가 예약돼 한 번 눌러도 2타가 나갔다 (같은 날 사용자 지적).
        if input_state.is_held(Action.ATTACK) and self.state != ATTACK:
            self._buffer[Action.ATTACK] = config.PLAYER_INPUT_BUFFER_TIME
        attack_waiting = False  # 걷던 칸을 마저 가는 중 (도착하면 공격)
        if self.state == ENCHANT and self._enchant_tail_cancelled(input_state):
            self.fsm.trigger("end_enchant")  # 아래에서 바로 그 행동을 시작한다
        if self.state in FREE_STATES:
            if self._buffered(Action.ATTACK) and self.combo.can_start and self.mover.is_moving:
                # 걷는 중 공격: 걷던 칸을 평소 속도로 마저 가서 칸에 선 뒤 공격 (2026-11-18 사용자 요청: 재빨리 가지 않음).
                # 한 칸 걷는 시간이 입력 기억보다 길 수 있어, 도착할 때까지 클릭을 기억해 둔다.
                self._buffer[Action.ATTACK] = config.PLAYER_INPUT_BUFFER_TIME
                attack_waiting = True
            elif self._buffered(Action.ATTACK) and self.combo.can_start:
                self._consume(Action.ATTACK)
                self.combo.start()
                self.fsm.trigger("attack")
            elif self._buffered(Action.PARRY):
                self._consume(Action.PARRY)
                self.combo.cancel_window()
                self.fsm.trigger("parry")
            elif self._buffered(Action.DODGE) and self.dodge_cooldown_left <= 0.0:
                self._consume(Action.DODGE)
                self._start_dodge(input_state)
            elif self._buffered(Action.ENCHANT):
                # 검 속성 입히기 (같은 속성이 이미 입혀져 있으면 동작 없이 풀림)
                self._consume(Action.ENCHANT)
                if self.enchant.press():
                    self.combo.cancel_window()
                    self.fsm.trigger("enchant")
            elif self._buffered(Action.JUMP):
                # 걷던 중이면 그 한 칸은 공중에서 마저 간다 (2026-11-17 사용자 결정: 바로 점프)
                self._consume(Action.JUMP)
                self.combo.cancel_window()
                self.fsm.trigger("jump")
        elif self.state == ATTACK and self._recovery_cancel():
            pass
        elif self.state == ATTACK and self._buffered(Action.ATTACK):
            self._consume(Action.ATTACK)
            self.combo.request_next()
        elif self.state == PARRY and self.parry_succeeded and self._buffered(Action.ATTACK) and self.combo.can_start:
            # 우선권: 패링에 성공하면 패링 동작이 끝나기 전에 바로 공격
            self._consume(Action.ATTACK)
            self.combo.start()
            self.fsm.trigger("attack")

        # 점프·패링·공격·회피·경직 중에는 새 이동을 시작하지 않고, 진행 중인 한 칸만 마저 간다.
        free = self.state in FREE_STATES and not attack_waiting
        dx, dy = input_state.move_direction() if free else (0, 0)
        self.mover.update(dt, dx, dy)

        if self.state in FREE_STATES:
            # 이동 중에는 실제로 움직이는 방향을, 멈춰 있으면 누른 방향을 바라본다.
            # (화면 끝에서 바깥쪽을 누르면 움직이지 않고 그 방향만 바라본다.)
            if self.mover.is_moving:
                dx, dy = self.mover.move_direction
            self.facing = facing_for_direction(dx, dy, self.facing)
            self.fsm.update_movement(self.mover.is_moving)

        self.animation.update(dt)
        if self.state == JUMP and self.jump.finished:
            self.fsm.trigger("land")
        elif self.state == PARRY and self.parry.finished:
            self.fsm.trigger("end_parry")
        elif self.state == ATTACK and self.combo.finished:
            self.fsm.trigger("end_attack")
            if input_state.is_held(Action.ATTACK) and self.combo.can_start:
                # 누르고 있으면 서기 그림을 한 프레임도 보이지 않고 같은 프레임에 다음 타로 (2026-11-19 사용자:
                # 흔들림 → 타 사이에 서기 그림(등에 멘 칼)이 한 프레임씩 끼어 깜빡였다)
                self._consume(Action.ATTACK)
                self.combo.start()
                self.fsm.trigger("attack")
        elif self.state == HURT and self.hurt.finished:
            self.fsm.trigger("end_hurt")
        elif self.state == ENCHANT and self.enchant.finished:
            self.fsm.trigger("end_enchant")
        elif self.state == DODGE and self.dodge.finished and not self.mover.is_moving:
            self.fsm.trigger("end_dodge")
            self.dodge_cooldown_left = 0.0 if self._perfect_this_dodge else config.PLAYER_DODGE_COOLDOWN
            self.dodge_tail_left = config.PLAYER_DODGE_TAIL_TIME
        if self.enchant.just_applied:  # 다 차오른 순간: 폭발 + 화면 흔들림
            self._pending_fx.append(("burst", self.enchant.active or ""))
            self.shake_requests.append(dict(config.PLAYER_ENCHANT_SHAKE))
            self.enchant.just_applied = False
        if (self.state == ENCHANT and not self._flicked and self.enchant.active is not None
                and frame_for_progress(self.enchant.progress, config.PLAYER_ENCHANT_FRAME_ENDS)
                >= config.PLAYER_ENCHANT_FLICK_FRAME):  # 털어 내리는 순간: 칼날의 속성이 흩뿌려짐
            self._flicked = True
            self._pending_fx.append(("flick", self.enchant.active))
        if self.state != IDLE:
            self.dodge_tail_left = 0.0  # 걷기·공격 등 다른 행동을 시작하면 멈춤 그림은 바로 끊긴다
        effect = self.sword_effect
        if effect is not None and effect[0] in config.SWORD_PROCEDURAL_ELEMENTS:
            self.procedural[effect[0]].update(dt, reach=effect[1])
        self._record_trail(dt)
        self._emit_strike()
        self._buffer = {a: t - dt for a, t in self._buffer.items() if t - dt > 0.0}

    def _recovery_cancel(self) -> bool:
        """후딜 캔슬: 이번 타의 판정이 나온 뒤 회피·점프·패링을 누르면 공격을 끊고 그 행동을 한다. 했으면 True."""
        if self._last_strike != (self.combo.strike_id, self.combo.index):
            return False  # 아직 판정 전 (선딜 중에는 끊을 수 없다)
        if self._buffered(Action.DODGE) and self.dodge_cooldown_left <= 0.0:
            self._consume(Action.DODGE)
            if not self._start_dodge(self._input):
                return False
        elif self._buffered(Action.JUMP):
            self._consume(Action.JUMP)
            self.combo.interrupt()
            self.fsm.trigger("jump")
        elif self._buffered(Action.PARRY):
            self._consume(Action.PARRY)
            self.combo.interrupt()
            self.fsm.trigger("parry")
        else:
            return False
        return True

    def _enchant_tail_cancelled(self, input_state: InputState) -> bool:
        """속성이 입혀진 뒤의 보여 주기 동작(털어내기·힘 풀기·등에 꽂기)을 이동·행동 입력으로 끊는지.
        차오르는 중(pending)에는 끊지 않는다. E 는 끊지 않는다 (다시 누르면 같은 속성이라 풀려 버림)."""
        if self.enchant.pending is not None or self.enchant.active is None:
            return False
        if input_state.move_direction() != (0, 0):
            return True
        return any(self._buffered(a) for a in (Action.ATTACK, Action.PARRY, Action.DODGE, Action.JUMP))

    def _buffered(self, action: Action) -> bool:
        return action in self._buffer

    def _consume(self, action: Action) -> None:
        self._buffer.pop(action, None)

    def receive_attack(self, attack: EnemyAttack) -> str:
        """적의 공격이 터졌다. 결과: MISSED(범위 밖) / AVOIDED(점프·회피 무적) / PARRIED / HIT.

        퍼펙트 회피: 노란색 공격(패링 불가·회피 가능)이 터지기 PLAYER_PERFECT_DODGE_WINDOW 초 안에
        그 범위 안에서 회피를 시작했으면 회피 대기 시간을 없앤다 (회피 한 번에 한 번).
        """
        self.last_perfect_dodge = self._check_perfect_dodge(attack)
        if (self.col, self.row) not in attack.tiles:
            return MISSED
        if attack.jumpable and self.state == JUMP and self.jump.is_airborne:
            return AVOIDED
        if attack.dodgeable and self.is_invincible:
            return AVOIDED
        if attack.parryable and self.state == PARRY and self.parry.is_active:
            self.parry_succeeded = True
            self.posture.relieve_by_parry()
            return PARRIED
        self.hp -= attack.damage
        if self.hp <= 0:
            self.hp = self.max_hp  # 사망은 기획 미정: 지금은 그 자리에서 다시 채운다
        self.hit_flash_left = config.PLAYER_HIT_FLASH_TIME
        self.combo.cancel_window()
        self.fsm.trigger("hurt")
        return HIT

    def _check_perfect_dodge(self, attack: EnemyAttack) -> bool:
        """퍼펙트 회피였으면 True (골렘 레이저 스택에서도 씀)."""
        yellow = not attack.parryable and attack.dodgeable
        if (yellow and self._dodge_start_tile in attack.tiles
                and self._since_dodge <= config.PLAYER_PERFECT_DODGE_WINDOW):
            self._since_dodge = float("inf")
            self._perfect_this_dodge = True
            self.dodge_cooldown_left = 0.0
            self.perfect_text_left = config.PLAYER_PERFECT_TEXT_TIME
            return True
        return False

    def _record_trail(self, dt: float) -> None:
        """회피로 움직이는 동안 PLAYER_AFTERIMAGE_INTERVAL 초마다 그 모습을 잔상으로 남긴다 (그리기 전용).
        퍼펙트든 아니든 남는다 (2026-11-18 사용자 요청). 도착한 뒤 멈춤 그림 동안은 남기지 않는다 (제자리에 겹쳐 뭉개짐)."""
        frame = self.dodge_frame if self.state == DODGE else None
        if frame is None:
            return
        self._trail_clock -= dt
        if self._trail_clock > 0.0:
            return
        self._trail_clock = config.PLAYER_AFTERIMAGE_INTERVAL
        vcol, vrow = self.mover.visual_position
        view, flip = sprite_view(self.facing)
        self.afterimages.append(Afterimage(vcol, vrow, view, flip, frame))

    def _start_dodge(self, input_state: InputState) -> bool:
        """누르고 있는 방향(없으면 바라보는 방향)으로 회피. 바로 앞이 막혀 있으면 하지 않는다 (대기 시간도 없음).

        회피했으면 True. 공격 중(후딜 캔슬)이었다면 콤보를 끊는다.
        """
        dx, dy = input_state.move_direction()
        if dx == 0 and dy == 0:
            dx, dy = self.facing.value
        start_tile = (self.col, self.row)
        if self.mover.dash(dx, dy, config.PLAYER_DODGE_DISTANCE, config.PLAYER_DODGE_DURATION) == 0:
            return False
        if self.state == ATTACK:
            self.combo.interrupt()
        self.combo.cancel_window()
        self.facing = facing_for_direction(dx, dy, self.facing)
        self._dodge_start_tile = start_tile
        self._since_dodge = 0.0
        self._perfect_this_dodge = False
        self._trail_clock = 0.0
        self.fsm.trigger("dodge")
        return True

    def _emit_strike(self) -> None:
        """지금 타가 판정 프레임에 들어섰으면 공격을 한 번 낸다 (한 타에 한 번)."""
        if self.state != ATTACK:
            return
        i = self.combo.index
        key = (self.combo.strike_id, i)
        if self.combo.frame_index >= config.PLAYER_ATTACK_HIT_FRAMES[i] and key != self._last_strike:
            self._last_strike = key
            self.strikes.append(Strike(self.col, self.row, self.facing.value,
                                       config.PLAYER_ATTACK_REACH[i], config.PLAYER_ATTACK_DAMAGE[i],
                                       config.PLAYER_ATTACK_WIDTH[i]))

    def _on_state_changed(self, state: str) -> None:
        if state == PARRY:
            self.parry_succeeded = False
        if state != ENCHANT:
            self.enchant.interrupt()  # 다 차오르기 전에 끊기면 입히지 않음
            self._pending_fx = []  # 그리기 전에 끊겼으면 다음 입히기로 넘기지 않음
        else:
            self._flicked = False
        # 새 상태의 애니메이션은 첫 프레임부터 재생한다.
        self.animations[state].reset()

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
        self._draw_body(renderer)
        self._draw_fx(renderer)  # 입히기 폭발·털어내기 입자는 늘 맨 위에 (동작이 끝난 뒤에도 날아감)

    def _draw_body(self, renderer) -> None:
        if self.perfect_text_left > 0.0:
            vcol, vrow = self.mover.visual_position
            left, bottom, right, _ = self.grid.tile_to_pixel_rect(vcol, vrow)
            rise = (1.0 - self.perfect_text_left / config.PLAYER_PERFECT_TEXT_TIME) * self.grid.tile_size * 0.4
            renderer.draw_text((left + right) / 2 - 34, bottom + config.PLAYER_RENDER_HEIGHT + 12 + rise, "PERFECT",
                               config.COLOR_POSTURE)
        self._draw_afterimages(renderer)
        if self.hit_flash_left > 0.0 and int(self.hit_flash_left / 0.05) % 2 == 0:
            return  # 맞은 직후 깜빡임: 0.05초마다 그렸다 안 그렸다
        view, flip = sprite_view(self.facing)
        vcol, vrow = self.mover.visual_position
        left, bottom, right, _ = self.grid.tile_to_pixel_rect(vcol, vrow)
        center_x = (left + right) / 2
        lift = 0.0
        if self.state == JUMP:
            lift = self.jump.height * self.grid.tile_size
            # 바닥 그림자: 중심을 칸의 발 위치에 둔다
            shadow_h = config.PLAYER_SHADOW_HEIGHT * config.RENDER_SCALE
            renderer.draw_sprite_frame(
                SHADOW_PATH, 0, config.PLAYER_SHADOW_WIDTH, config.PLAYER_SHADOW_HEIGHT,
                center_x, bottom - shadow_h / 2,
                config.PLAYER_SHADOW_WIDTH * config.RENDER_SCALE, shadow_h,
            )

        if self.state == ATTACK:
            self._draw_attack(renderer, center_x, bottom)
            return
        if self.state == PARRY and self._draw_parry(renderer, center_x, bottom):
            return
        if self.state == ENCHANT and self._draw_enchant(renderer, center_x, bottom):
            return

        if self.state == DODGE or (self.state == IDLE and self.dodge_tail_left > 0.0):
            self._draw_dodge(renderer, center_x, bottom, view, flip)
            return

        # 그림의 발끝(아래 가운데)을 칸의 아래 가운데에 맞춘다. 점프 중에는 lift 만큼 띄운다.
        sprite_state = SPRITE_FALLBACK.get(self.state, self.state)
        if self.facing == Facing.LEFT and sprite_state in LEFT_SHEET_STATES:
            view, flip = "side_left", False
        animated = sprite_state == self.state or self.state in ANIMATED_FALLBACK
        frame_index = self.animation.frame_index if animated else 0
        if sprite_state == JUMP:
            width, height = config.PLAYER_JUMP_SPRITE_WIDTH, config.PLAYER_JUMP_SPRITE_HEIGHT
        else:
            width, height = config.PLAYER_SPRITE_WIDTH, config.PLAYER_SPRITE_HEIGHT
        sword_frame = frame_index if animated else 0
        self._with_back_sword(
            renderer, sprite_view(self.facing)[0], flip, center_x, bottom + lift,
            sprite_state if animated else IDLE, sword_frame,
            lambda: renderer.draw_sprite_frame(
                sprite_sheet_path(sprite_state, view),
                frame_index,
                width,
                height,
                center_x,
                bottom + lift,
                width * config.RENDER_SCALE,
                height * config.RENDER_SCALE,
                flip_horizontal=flip,
            ))

    @property
    def dodge_frame(self) -> int | None:
        """회피 그림 번호. 이동 중에는 진행도로 앞 장들, 끝난 뒤에는 남은 멈춤 시간으로 뒤 장들. 아니면 None."""
        if self.state == DODGE:
            return self.dodge.frame_index
        if self.state == IDLE and self.dodge_tail_left > 0.0:
            tail = config.PLAYER_DODGE_FRAMES - config.PLAYER_DODGE_MOVE_FRAMES
            done = 1.0 - self.dodge_tail_left / config.PLAYER_DODGE_TAIL_TIME
            return config.PLAYER_DODGE_MOVE_FRAMES + min(tail - 1, int(done * tail))
        return None

    def _draw_afterimages(self, renderer) -> None:
        """회피 잔상: 그림자처럼 바꾼 회피 그림을 지나온 자리에, 오래된 것일수록 옅게."""
        w, h = config.PLAYER_DODGE_SPRITE_WIDTH, config.PLAYER_DODGE_SPRITE_HEIGHT
        for ghost in self.afterimages:
            left, bottom, right, _ = self.grid.tile_to_pixel_rect(ghost.col, ghost.row)
            fade = 1.0 - ghost.age / config.PLAYER_AFTERIMAGE_TIME
            renderer.draw_sprite_frame(dodge_ghost_sheet_path(ghost.view), ghost.frame, w, h, (left + right) / 2, bottom,
                                       w * config.RENDER_SCALE, h * config.RENDER_SCALE, flip_horizontal=ghost.flip,
                                       opacity=config.PLAYER_AFTERIMAGE_OPACITY * fade)

    def _draw_dodge(self, renderer, center_x: float, bottom: float, view: str, flip: bool) -> None:
        w, h = config.PLAYER_DODGE_SPRITE_WIDTH, config.PLAYER_DODGE_SPRITE_HEIGHT
        frame = self.dodge_frame
        self._with_back_sword(
            renderer, view, flip, center_x, bottom, DODGE, frame,
            lambda: renderer.draw_sprite_frame(sprite_sheet_path(DODGE, view), frame, w, h, center_x, bottom,
                                               w * config.RENDER_SCALE, h * config.RENDER_SCALE, flip_horizontal=flip))

    def _with_back_sword(self, renderer, view: str, flip: bool, center_x: float, bottom: float,
                         state: str, frame: int, draw_body) -> None:
        """몸 그림(draw_body)과 등에 멘 칼을 그린다. 후면은 칼이 등 위(몸 다음), 정면·측면은 몸 뒤(몸 전).

        칼은 그 장의 머리 꼭대기가 움직인 만큼 옮긴다 (PLAYER_BACK_SWORD_OFFSETS, 없는 상태는 서 있기 첫 장).
        왼쪽을 볼 때는 칼 그림을 뒤집고 앞쪽 옮김도 반대로.
        """
        table = config.PLAYER_BACK_SWORD_OFFSETS.get(state, config.PLAYER_BACK_SWORD_OFFSETS[IDLE])
        offsets = table.get(view, table["front"])
        dx, dy = offsets[frame] if state in config.PLAYER_BACK_SWORD_OFFSETS and frame < len(offsets) else offsets[0]
        scale = config.RENDER_SCALE
        size = config.PLAYER_BACK_SWORD_SIZE

        def draw_sword() -> None:
            sword_x = center_x + (-dx if flip else dx) * scale  # 등 칼 그림의 아래 가운데
            sword_bottom = bottom + dy * scale
            renderer.draw_sprite_frame(
                weapon_back_path(config.PLAYER_WEAPON, view), 0, size, size,
                sword_x, sword_bottom, size * scale, size * scale, flip_horizontal=flip)
            # 검 속성 이펙트: 등에 멘 맨 칼에도 같은 자리·각도로 (2026-11-20 사용자 요청)
            hx, hy, angle = config.PLAYER_BACK_SWORD_HAND[view]
            x = size - hx - 0.5 if flip else hx + 0.5
            self._draw_sword_effect(renderer, sword_x - size * scale / 2 + x * scale,
                                    sword_bottom + (size - hy - 0.5) * scale, -angle if flip else angle, flip)

        if (state, view) in config.PLAYER_BACK_SWORD_HIDDEN:
            draw_body()
            return
        in_front = view in config.PLAYER_BACK_SWORD_IN_FRONT
        if not in_front:
            draw_sword()
        draw_body()
        if in_front:
            draw_sword()

    def _draw_attack(self, renderer, center_x: float, bottom: float) -> None:
        """지금 타의 공격 그림(96×64 캔버스)을 발끝이 칸 아래 가운데에 오도록 그린다.

        아래를 보면 정면, 위를 보면 후면(2026-11-18), 오른쪽·왼쪽은 측면 그림(왼쪽은 좌우 반전)을 쓴다.
        정면 3타 찌르는 순간은 무기의 찌르기용 칼 그림을 쓴다.
        """
        view = attack_view(self.facing, self.combo.index)
        ends = ATTACK_FRAME_ENDS.get(view, (None,) * config.PLAYER_ATTACK_HITS)[self.combo.index]
        if ends is not None:
            # 타별 프레임 표로 고른다 (휘두르는 그림을 판정 시점에 맞춤)
            frame = frame_for_progress(self.combo.current.progress, ends)
            shifts = {"front": config.PLAYER_ATTACK_FRAME_SHIFTS_FRONT,
                      "back": config.PLAYER_ATTACK_FRAME_SHIFTS_BACK}.get(view, config.PLAYER_ATTACK_FRAME_SHIFTS)
            shift_x, shift_y = shifts[self.combo.index][frame]
        else:
            frame = self.combo.frame_index
            shift_x, shift_y = config.PLAYER_ATTACK_FRAME_SHIFTS[self.combo.index][frame]
        # 찌르기용 칼 그림이 있는 프레임이면 옆모습 칼을 돌리는 대신 그 그림을 몸 위에 겹친다 (없는 무기는 옆모습 칼)
        art_path = weapon_view_art_path(config.PLAYER_WEAPON, view, self.combo.hit_number)
        use_art = (frame in config.PLAYER_WEAPON_VIEW_ART.get((view, self.combo.hit_number), ())
                   and os.path.exists(art_path))
        art_effect = config.PLAYER_WEAPON_VIEW_ART_EFFECT.get((view, self.combo.hit_number), {}).get(frame)
        self._draw_sword_pose(renderer, center_x, bottom, frame, (shift_x, shift_y),
                              attack_sheet_path(self.combo.hit_number, view),
                              attack_hand_sheet_path(self.combo.hit_number, view),
                              ATTACK_SWORD_TABLES[view][self.combo.index][frame], art_path if use_art else None,
                              art_effect if use_art else None)

    def _draw_parry(self, renderer, center_x: float, bottom: float) -> bool:
        """패링 그림(공격과 같은 96×64 칸, 칼 분리)을 그린다. 이 방향 그림이 없으면 False (서 있는 그림을 쓴다)."""
        view, _ = sprite_view(self.facing)
        table = config.PLAYER_PARRY_SWORD.get(view)
        if table is None:
            return False
        frame = frame_for_progress(self.parry.progress, config.PLAYER_PARRY_FRAME_ENDS)
        self._draw_sword_pose(renderer, center_x, bottom, frame, (0, 0),
                              parry_sheet_path(view), parry_hand_sheet_path(view), table[frame])
        return True

    def _draw_enchant(self, renderer, center_x: float, bottom: float) -> bool:
        """검 속성 입히기 자세: 그 방향 그림(PLAYER_ENCHANT_SWORD)이 있으면 칼을 곧게 세우는 동작,
        없으면 패링 막기 자세(PLAYER_ENCHANT_POSE_FRAME)를 임시로 쓴다."""
        view, flip = sprite_view(self.facing)
        table = config.PLAYER_ENCHANT_SWORD.get(view)
        if table is not None:
            frame = frame_for_progress(self.enchant.progress, config.PLAYER_ENCHANT_FRAME_ENDS)
            folder = config.PLAYER_IMAGE_DIR / "enchant"

            def draw_body() -> None:
                self._draw_sword_pose(renderer, center_x, bottom, frame, (0, 0), str(folder / f"{view}.png"),
                                      str(folder / f"{view}_hand.png"), table[frame])

            if frame >= config.PLAYER_ENCHANT_SHEATHED_FROM:  # 칼을 등에 꽂은 뒤: 등 칼과 함께
                self._with_back_sword(renderer, view, flip, center_x, bottom, ENCHANT, 0, draw_body)
            else:
                draw_body()
            self._start_pending_fx(center_x, bottom, table)
            return True
        table = config.PLAYER_PARRY_SWORD.get(view)
        if table is None:
            return False
        frame = config.PLAYER_ENCHANT_POSE_FRAME
        self._draw_sword_pose(renderer, center_x, bottom, frame, (0, 0),
                              parry_sheet_path(view), parry_hand_sheet_path(view), table[frame])
        return True

    def _sword_point(self, center_x: float, bottom: float, sword: tuple, along: float) -> tuple[float, float]:
        """칼 위치표 한 줄의 칼날 위 한 점 (화면 좌표). along = 손(0) ~ 칼끝(1)."""
        width, height = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        scale = config.RENDER_SCALE
        flip = self.facing == Facing.LEFT
        hand_x, hand_y, angle = sword[:3]
        canvas_left = center_x - width * scale / 2
        canvas_top = bottom - config.PLAYER_ATTACK_FOOT_MARGIN * scale + height * scale
        x = width - hand_x - 0.5 if flip else hand_x + 0.5
        rad = math.radians(180 - angle if flip else angle)
        reach = 24 * along * scale  # 손에서 칼끝까지 24 픽셀
        return canvas_left + x * scale + math.cos(rad) * reach, canvas_top - (hand_y + 0.5) * scale + math.sin(rad) * reach

    def _start_pending_fx(self, center_x: float, bottom: float, table: tuple) -> None:
        """그릴 때 칼 자리를 알아야 하는 입자를 시작한다: 폭발은 곧게 세운 칼, 털어내기는 털어낸 끝 칼과 칼끝이 움직인 쪽."""
        scale = config.RENDER_SCALE
        hold = table[config.PLAYER_ENCHANT_FLICK_FRAME - 1]
        end = table[-1]

        def blade(sword: tuple) -> tuple[tuple[float, float], tuple[float, float]]:
            hx, hy = self._sword_point(center_x, bottom, sword, 0.0)
            tx, ty = self._sword_point(center_x, bottom, sword, 1.0)
            return (hx / scale, hy / scale), (tx / scale, ty / scale)

        for kind, element in self._pending_fx:
            if kind == "burst":
                self.fx.burst(element, blade(hold))
            else:
                ax, ay = blade(hold)[1]
                end_blade = blade(end)
                bx, by = end_blade[1]
                n = math.hypot(bx - ax, by - ay) or 1
                self.fx.flick(element, end_blade, ((bx - ax) / n, (by - ay) / n))
        self._pending_fx = []

    def _draw_fx(self, renderer) -> None:
        """입히기 폭발·털어내기 입자 (불·전기 = 색 점, 어둠 = 반투명 그림자)."""
        scale = config.RENDER_SCALE
        for px, py, colour, *alpha in self.fx.pixels():
            if colour is None:
                renderer.fill_shade(px * scale, py * scale, (px + 1) * scale, (py + 1) * scale, alpha[0])
            else:
                renderer.fill_rect(px * scale, py * scale, (px + 1) * scale, (py + 1) * scale, colour)

    @property
    def sword_effect(self) -> tuple[str, float] | None:
        """지금 칼에 그릴 속성 이펙트 (속성, 차오른 정도 0~1). 없으면 None.

        입히는 중에는 새 속성이 손잡이에서 칼끝으로 차오르고, 그 밖에는 검에 입힌 속성이 칼 전체에.
        """
        if self.state == ENCHANT and self.enchant.pending is not None:
            return self.enchant.pending, self.enchant.rise
        if self.enchant.active is not None:
            return self.enchant.active, 1.0
        return None

    def _draw_sword_effect(self, renderer, x: float, y: float, angle: float, flip: bool,
                           along: float = 1.0) -> None:
        """칼 이펙트 시트를 칼과 같은 손 위치·각도로 겹친다 (입히는 중이면 점화 시트의 그 순간 장)."""
        effect = self.sword_effect
        if effect is None:
            return
        element, rise = effect
        if rise <= 0.0:
            return
        if element in config.SWORD_PROCEDURAL_ELEMENTS:
            self._draw_procedural(renderer, element, x, y, angle, flip, SWORD_SHAPE, along, rise)
            return
        if rise < 1.0:  # 입히는 중: 점화 시트 (손잡이에서 붙은 불이 칼끝까지 번짐)
            path = config.SWORD_EFFECT_DIR / f"{element}_ignite.png"
            frame = min(config.SWORD_EFFECT_IGNITE_FRAMES - 1, int(rise * config.SWORD_EFFECT_IGNITE_FRAMES))
        else:
            path = config.SWORD_EFFECT_DIR / f"{element}.png"
            frame = int(self.effect_clock * config.SWORD_EFFECT_FPS) % config.SWORD_EFFECT_FRAMES
        w, h = config.SWORD_EFFECT_FRAME_SIZE
        scale = config.RENDER_SCALE
        if along == 1.0:
            renderer.draw_frame_rotated(str(path), frame, w, h, x, y, scale, angle, flip_horizontal=flip)
        else:  # 원근으로 짧게 그린 칼: 칼 방향으로만 줄임 (손 자리가 프레임 한가운데라 줄여도 손은 그대로)
            renderer.draw_frame_rotated(str(path), frame, w, h, x, y, scale * along, angle, flip_horizontal=flip,
                                        scale_y=scale)

    def _draw_procedural(self, renderer, element: str, x: float, y: float, angle: float, flip: bool,
                         shape: BladeShape, along: float = 1.0, reach: float = 1.0) -> None:
        """계산해 만든 이펙트(전기 LightningField, 어둠 DarkField)를 원본 픽셀 격자에 1 픽셀씩 찍는다 (RENDER_SCALE 배 네모).

        (x, y) = 화면의 손 자리, angle·flip = 칼 그림을 그릴 때와 같은 값 (뒤집으면 칼끝 방향이 반대).
        """
        scale = config.RENDER_SCALE
        sign = -1.0 if flip else 1.0
        rad = math.radians(angle)
        direction = (sign * math.cos(rad), sign * math.sin(rad))
        # 원본 픽셀 격자를 캐릭터 그림의 픽셀 격자에 맞춘다 (손은 픽셀 한가운데). 안 맞추면 네모가 그림 픽셀과
        # 반 칸씩 어긋나 겹쳐 깨져 보였음 (2026-11-20 사용자 지적).
        hx, hy = x / scale - 0.5, y / scale - 0.5
        ox, oy = hx - math.floor(hx), hy - math.floor(hy)
        hand = (math.floor(hx) + 0.5, math.floor(hy) + 0.5)
        for px, py, colour, *alpha in self.procedural[element].pixels(hand, direction, shape, along, reach):
            left, bottom = (px + ox) * scale, (py + oy) * scale
            if colour is None:  # 반투명 그림자 (어둠)
                renderer.fill_shade(left, bottom, left + scale, bottom + scale, alpha[0])
            else:
                renderer.fill_rect(left, bottom, left + scale, bottom + scale, colour)

    def _draw_sword_pose(self, renderer, center_x: float, bottom: float, frame: int, shift: tuple[int, int],
                         body_path: str, hand_path: str, sword: tuple, art_path: str | None = None,
                         art_effect: str | None = None) -> None:
        """칼을 든 자세 한 프레임 (공격·패링): 몸 → 칼 → 오른손 레이어. 칼이 몸 뒤면 칼 → 몸 → 손.

        발끝이 칸 아래 가운데에 오고, 왼쪽을 볼 때는 측면 그림을 좌우 반전한다.
        sword = (손 x, 손 y, 각도, 몸 뒤[, 칼 길이 비율]). art_path 가 있으면 칼을 돌리는 대신 그 그림을 겹친다.
        """
        width, height = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        scale = config.RENDER_SCALE
        shift_x, shift_y = shift
        flip = self.facing == Facing.LEFT
        forward = -1 if flip else 1
        canvas_x = center_x + shift_x * scale * forward  # 캔버스 아래 가운데
        canvas_bottom = bottom - config.PLAYER_ATTACK_FOOT_MARGIN * scale + shift_y * scale
        hand_x, hand_y, angle, behind, *rest = sword
        length = rest[0] if rest else 1.0

        def draw_layer(path: str) -> None:
            renderer.draw_sprite_frame(
                path, frame, width, height,
                canvas_x, canvas_bottom, width * scale, height * scale, flip_horizontal=flip,
            )

        # 두 손 잡기: 몸(두 팔, 칼 뒤의 왼손) → 칼 → 오른손 레이어 (오른손이 칼을 감싸 쥔 모습)
        if not behind:
            draw_layer(body_path)
        if art_path:
            draw_layer(art_path)
            effect = self.sword_effect
            if art_effect is not None and effect is not None and effect[0] in config.SWORD_PROCEDURAL_ELEMENTS:
                # 계산해 만드는 전기: 찌르기용 큰 칼의 손 자리·각도·모양 (PLAYER_WEAPON_VIEW_ART_SHAPE)
                ax, ay, a_angle, start, end, half_start, half_end = config.PLAYER_WEAPON_VIEW_ART_SHAPE[art_effect]
                canvas_left = canvas_x - width * scale / 2
                hx = width - ax - 0.5 if flip else ax + 0.5
                self._draw_procedural(renderer, effect[0], canvas_left + hx * scale,
                                      canvas_bottom + (height - ay - 0.5) * scale, -a_angle if flip else a_angle,
                                      flip, BladeShape(start, end, half_start, half_end))
            elif art_effect is not None and effect is not None:  # 찌르기용 칼 그림 전용 불 (그 칼날 윤곽에서 피어오름)
                frame_loop = int(self.effect_clock * config.SWORD_EFFECT_FPS) % config.SWORD_EFFECT_FRAMES
                renderer.draw_sprite_frame(str(config.SWORD_EFFECT_DIR / f"{effect[0]}_{art_effect}.png"), frame_loop,
                                           width, height, canvas_x, canvas_bottom, width * scale, height * scale,
                                           flip_horizontal=flip)
        else:
            self._draw_sword(renderer, canvas_x, canvas_bottom, hand_x, hand_y, angle, flip, length)
        if behind:
            draw_layer(body_path)
        draw_layer(hand_path)

    def _draw_sword(self, renderer, canvas_x: float, canvas_bottom: float,
                    hand_x: int, hand_y: int, angle: float, flip: bool, length: float = 1.0) -> None:
        """칼 그림 한 장을 손 위치에 놓고 각도만큼 돌려 그린다. 그림 한가운데가 손이다.

        length 는 칼 길이 비율이다. 화면 안쪽·바깥쪽으로 찌르는 칼은 원근으로 짧아 보이게 그린다.

        왼쪽을 볼 때는 캔버스처럼 손 위치를 좌우로 뒤집고, 칼은 뒤집은 뒤 반대로 돌린다 (칼끝 180 - 각도).
        """
        width, height = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        scale = config.RENDER_SCALE
        if length <= 0:
            return  # 칼이 몸에 완전히 가려지는 장 (후면)
        canvas_left = canvas_x - width * scale / 2
        canvas_top = canvas_bottom + height * scale
        x = width - hand_x - 0.5 if flip else hand_x + 0.5  # 손 픽셀의 가운데
        renderer.draw_image_rotated(
            weapon_sheet_path(config.PLAYER_WEAPON),
            canvas_left + x * scale,
            canvas_top - (hand_y + 0.5) * scale,
            round(config.PLAYER_SWORD_SPRITE_WIDTH * length) * scale,
            config.PLAYER_SWORD_SPRITE_HEIGHT * scale,
            -angle if flip else angle,
            flip_horizontal=flip,
        )
        # 원근으로 짧게 그린 칼은 이펙트도 같은 비율로 짧게
        self._draw_sword_effect(renderer, canvas_left + x * scale, canvas_top - (hand_y + 0.5) * scale,
                                -angle if flip else angle, flip, along=length)
