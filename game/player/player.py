"""주인공: 칸 이동(상하좌우), 바라보는 방향, 상태 머신, 애니메이션을 묶는다.

- 논리적 위치와 충돌 영역은 칸 하나 (self.col, self.row) 이다.
- 그림 크기(32×48)는 그리기에만 쓰며 충돌 판정과 무관하다.
- 캐릭터 본체 그림만 그린다. 검 등 장비는 별도 레이어로 나중에 추가한다.
"""
from __future__ import annotations

from game import config
from game.input.input_state import InputState
from game.player.animation import LoopAnimation
from game.player.facing import Facing, facing_for_direction, sprite_view
from game.player.movement import GridMover
from game.player.state_machine import IDLE, WALK, PlayerStateMachine
from game.world.grid import Grid


def sprite_sheet_path(state: str, view: str) -> str:
    """상태·원본 방향에 해당하는 스프라이트 시트 경로. 예: idle_front.png"""
    return str(config.PLAYER_IMAGE_DIR / f"{state}_{view}.png")


class Player:
    def __init__(self, grid: Grid, col: int, row: int) -> None:
        self.grid = grid
        self.mover = GridMover(grid, col, row, speed=config.PLAYER_MOVE_SPEED)
        self.facing = Facing.DOWN
        self.animations: dict[str, LoopAnimation] = {
            IDLE: LoopAnimation(config.PLAYER_IDLE_FRAMES, config.PLAYER_IDLE_FRAME_DURATION),
            WALK: LoopAnimation(config.PLAYER_WALK_FRAMES, config.PLAYER_WALK_FRAME_DURATION),
        }
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
    def animation(self) -> LoopAnimation:
        return self.animations[self.state]

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        dx, dy = input_state.move_direction()
        self.mover.update(dt, dx, dy)
        # 이동 중에는 실제로 움직이는 방향을, 멈춰 있으면 누른 방향을 바라본다.
        # (화면 끝에서 바깥쪽을 누르면 움직이지 않고 그 방향만 바라본다.)
        if self.mover.is_moving:
            dx, dy = self.mover.move_direction
        self.facing = facing_for_direction(dx, dy, self.facing)
        self.fsm.update_movement(self.mover.is_moving)
        self.animation.update(dt)

    def _on_state_changed(self, state: str) -> None:
        # 새 상태의 애니메이션은 첫 프레임부터 재생한다.
        self.animations[state].reset()

    # ----- 그리기 -----
    def draw(self, renderer) -> None:
        view, flip = sprite_view(self.facing)
        vcol, vrow = self.mover.visual_position
        left, bottom, right, _ = self.grid.tile_to_pixel_rect(vcol, vrow)
        # 그림의 발끝(아래 가운데)을 칸의 아래 가운데에 맞춘다.
        renderer.draw_sprite_frame(
            sprite_sheet_path(self.state, view),
            self.animation.frame_index,
            config.PLAYER_SPRITE_WIDTH,
            config.PLAYER_SPRITE_HEIGHT,
            (left + right) / 2,
            bottom,
            flip_horizontal=flip,
        )
