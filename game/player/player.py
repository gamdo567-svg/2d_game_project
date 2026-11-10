"""주인공: 칸 이동(상하좌우), 바라보는 방향, 상태 머신, 애니메이션, 점프·패링을 묶는다.

- 논리적 위치와 충돌 영역은 칸 하나 (self.col, self.row) 이다. 점프해도 칸 위치는 그대로다.
- 그림 크기(원본 32×48, 화면 표시 64×96)는 그리기에만 쓰며 충돌 판정과 무관하다.
- 본체와 무기는 별도 레이어다. 무기(검)는 지금은 패링 중에만 그린다.
- 점프·패링은 서 있거나 걷는 중에만 시작한다. 점프는 진행 중인 한 칸 이동을 마친 뒤 시작하고,
  패링은 바로 시작한다(진행 중인 한 칸 이동은 마저 간다). 두 행동 중에는 새 이동을 하지 않는다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import Action, InputState
from game.player.actions import Jump, Parry
from game.player.animation import LoopAnimation
from game.player.facing import Facing, facing_for_direction, sprite_view
from game.player.movement import GridMover
from game.player.state_machine import FREE_STATES, IDLE, JUMP, PARRY, WALK, PlayerStateMachine
from game.world.grid import Grid


def sprite_sheet_path(state: str, view: str) -> str:
    """상태·원본 방향에 해당하는 스프라이트 시트 경로. 예: idle/front.png"""
    return str(config.PLAYER_IMAGE_DIR / state / f"{view}.png")


def weapon_sheet_path(state: str, view: str) -> str:
    """상태·원본 방향에 해당하는 무기 레이어 시트 경로. 예: weapon/parry/front.png"""
    return str(config.PLAYER_IMAGE_DIR / "weapon" / state / f"{view}.png")


SHADOW_PATH = str(config.PLAYER_IMAGE_DIR / "shadow.png")
# 무기를 몸 뒤에 그리는 원본 방향 (뒷모습에서는 검이 몸에 가려진다)
WEAPON_BEHIND_VIEWS = {"back"}


class Player:
    def __init__(self, grid: Grid, col: int, row: int) -> None:
        self.grid = grid
        self.mover = GridMover(grid, col, row, speed=config.PLAYER_MOVE_SPEED)
        self.facing = Facing.DOWN
        self.jump = Jump(config.PLAYER_JUMP_DURATION, config.PLAYER_JUMP_HEIGHT, config.PLAYER_JUMP_FRAMES)
        self.parry = Parry(config.PLAYER_PARRY_DURATION, config.PLAYER_PARRY_WINDOW, config.PLAYER_PARRY_FRAMES)
        # 상태별 애니메이션. 점프·패링은 행동 진행도에 맞춰 프레임을 고른다.
        self.animations: dict[str, LoopAnimation | Jump | Parry] = {
            IDLE: LoopAnimation(config.PLAYER_IDLE_FRAMES, config.PLAYER_IDLE_FRAME_DURATION),
            WALK: LoopAnimation(config.PLAYER_WALK_FRAMES, config.PLAYER_WALK_FRAME_DURATION),
            JUMP: self.jump,
            PARRY: self.parry,
        }
        self._jump_requested = False  # 이동 중에 누른 점프: 한 칸 이동을 마치면 시작
        self.fsm = PlayerStateMachine(on_state_changed=self._on_state_changed)

    # ----- 상태 조회 -----
    @property
    def col(self) -> int:
        return self.mover.col

    @property
    def row(self) -> int:
        return self.mover.row

    @property
    def state(self) -> str:
        return self.fsm.state

    @property
    def animation(self) -> LoopAnimation | Jump | Parry:
        return self.animations[self.state]

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        if self.state in FREE_STATES:
            if input_state.was_pressed(Action.PARRY):
                self._jump_requested = False
                self.fsm.trigger("parry")
            elif input_state.was_pressed(Action.JUMP):
                self._jump_requested = True

        # 점프·패링 중이거나 점프를 기다리는 중에는 새 이동을 시작하지 않고, 진행 중인 한 칸만 마저 간다.
        free = self.state in FREE_STATES and not self._jump_requested
        dx, dy = input_state.move_direction() if free else (0, 0)
        self.mover.update(dt, dx, dy)
        if self._jump_requested and not self.mover.is_moving:
            self._jump_requested = False
            self.fsm.trigger("jump")

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

    def _on_state_changed(self, state: str) -> None:
        # 새 상태의 애니메이션은 첫 프레임부터 재생한다.
        self.animations[state].reset()

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
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

        layers = [sprite_sheet_path(self.state, view)]
        if self.state == PARRY:
            weapon = weapon_sheet_path(self.state, view)
            layers = [weapon] + layers if view in WEAPON_BEHIND_VIEWS else layers + [weapon]
        # 그림의 발끝(아래 가운데)을 칸의 아래 가운데에 맞춘다. 점프 중에는 lift 만큼 띄운다.
        for path in layers:
            renderer.draw_sprite_frame(
                path,
                self.animation.frame_index,
                config.PLAYER_SPRITE_WIDTH,
                config.PLAYER_SPRITE_HEIGHT,
                center_x,
                bottom + lift,
                config.PLAYER_RENDER_WIDTH,
                config.PLAYER_RENDER_HEIGHT,
                flip_horizontal=flip,
            )
