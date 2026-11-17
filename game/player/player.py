"""주인공: 칸 이동(상하좌우), 바라보는 방향, 상태 머신, 애니메이션, 점프·패링·검 공격을 묶는다.

- 논리적 위치와 충돌 영역은 칸 하나 (self.col, self.row) 이다. 점프해도 칸 위치는 그대로다.
- 그림 크기(원본 32×48, 화면 표시 64×96)는 그리기에만 쓰며 충돌 판정과 무관하다.
- 캐릭터 본체 그림과 장비를 따로 그린다. 지금은 공격 중에만 검 그림 한 장을 손 위치·각도에 맞춰 겹쳐 그린다.
- 점프·패링은 서 있거나 걷는 중에만 시작한다. 점프는 진행 중인 한 칸 이동을 마친 뒤 시작하고,
  패링·공격은 바로 시작한다(진행 중인 한 칸 이동은 마저 간다). 세 행동 중에는 새 이동을 하지 않는다.
- 공격은 3단 콤보(SwordCombo). 공격 중 클릭하면 다음 타가 이어지고, 3타 뒤에는 잠시 공격만 할 수 없다.
- 공격 그림은 검이 몸 밖으로 나가므로 96×64 캔버스이고, 지금은 타별 오른쪽 측면 그림만 있다
  (위·아래는 임시로 같은 그림, 왼쪽은 좌우 반전).
"""
from __future__ import annotations

from game import config
from game.input.input_state import Action, InputState
from game.player.actions import Jump, Parry, SwordCombo
from game.player.animation import LoopAnimation
from game.player.facing import Facing, facing_for_direction, sprite_view
from game.player.movement import CanEnter, GridMover
from game.player.state_machine import ATTACK, FREE_STATES, IDLE, JUMP, PARRY, WALK, PlayerStateMachine
from game.world.grid import Grid


def sprite_sheet_path(state: str, view: str) -> str:
    """상태·원본 방향에 해당하는 스프라이트 시트 경로. 예: idle/front.png"""
    return str(config.PLAYER_IMAGE_DIR / state / f"{view}.png")


def attack_sheet_path(hit_number: int, view: str = "side") -> str:
    """콤보 타별 공격 시트 경로. 예: sword_attack/side_1.png"""
    return sprite_sheet_path(ATTACK, f"{view}_{hit_number}")


def attack_hand_sheet_path(hit_number: int, view: str = "side") -> str:
    """콤보 타별 오른손 레이어 시트 경로 (칼 위에 그리는 오른손 주먹만). 예: sword_attack/side_1_hand.png"""
    return sprite_sheet_path(ATTACK, f"{view}_{hit_number}_hand")


# 방향별 공격 칼 위치표. 후면(back)은 아직 그림이 없어 측면을 쓴다.
ATTACK_SWORD_TABLES = {"side": config.PLAYER_ATTACK_SWORD, "front": config.PLAYER_ATTACK_SWORD_FRONT}


def attack_view(facing: Facing) -> str:
    """공격 그림 방향: 아래 = front, 그 밖 = side (위는 후면 그림이 생길 때까지 임시로 측면)."""
    view, _ = sprite_view(facing)
    return view if view in ATTACK_SWORD_TABLES else "side"


def weapon_sheet_path(weapon: str) -> str:
    """무기 그림 경로 (칼 한 장). 예: weapons/old_sword.png"""
    return str(config.PLAYER_IMAGE_DIR / "weapons" / f"{weapon}.png")


SHADOW_PATH = str(config.PLAYER_IMAGE_DIR / "shadow.png")
# 전용 그림이 아직 없는 상태 -> 대신 쓸 그림 상태. 패링은 공격 모션과 함께 만들 때까지 서 있는 그림(첫 프레임).
SPRITE_FALLBACK = {PARRY: IDLE}
# 좌우가 비대칭인 상태: 왼쪽을 볼 때 측면을 뒤집지 않고 전용 그림(side_left)을 쓴다.
# 점프는 오른손으로 후드를 잡으므로 뒤집으면 왼손이 되어 버린다.
LEFT_SHEET_STATES = {JUMP}


class Player:
    def __init__(self, grid: Grid, col: int, row: int, can_enter: CanEnter | None = None) -> None:
        """can_enter(col, row): 들어갈 수 있는 칸인지 (벽 충돌). 없으면 격자 안이면 된다."""
        self.grid = grid
        self.mover = GridMover(grid, col, row, speed=config.PLAYER_MOVE_SPEED, can_enter=can_enter)
        self.facing = Facing.DOWN
        self.jump = Jump(config.PLAYER_JUMP_DURATION, config.PLAYER_JUMP_HEIGHT, config.PLAYER_JUMP_FRAME_ENDS)
        self.parry = Parry(config.PLAYER_PARRY_DURATION, config.PLAYER_PARRY_WINDOW, frame_count=1)
        self.combo = SwordCombo(
            config.PLAYER_ATTACK_DURATIONS, config.PLAYER_ATTACK_FRAME_ENDS,
            config.PLAYER_ATTACK_COMBO_WINDOW, config.PLAYER_ATTACK_COOLDOWN,
        )
        # 상태별 애니메이션. 점프·패링은 행동 진행도에 맞춰 프레임을 고른다.
        self.animations: dict[str, LoopAnimation | Jump | Parry | SwordCombo] = {
            IDLE: LoopAnimation(config.PLAYER_IDLE_FRAMES, config.PLAYER_IDLE_FRAME_DURATION),
            WALK: LoopAnimation(config.PLAYER_WALK_FRAMES, config.PLAYER_WALK_FRAME_DURATION),
            JUMP: self.jump,
            PARRY: self.parry,
            ATTACK: self.combo,
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
    def animation(self) -> LoopAnimation | Jump | Parry | SwordCombo:
        return self.animations[self.state]

    # ----- 로직 -----
    def update(self, dt: float, input_state: InputState) -> None:
        self.combo.tick(dt)
        if self.state in FREE_STATES:
            if input_state.was_pressed(Action.ATTACK) and self.combo.can_start:
                self._jump_requested = False
                self.combo.start()
                self.fsm.trigger("attack")
            elif input_state.was_pressed(Action.PARRY):
                self._jump_requested = False
                self.combo.cancel_window()
                self.fsm.trigger("parry")
            elif input_state.was_pressed(Action.JUMP):
                self._jump_requested = True
                self.combo.cancel_window()
        elif self.state == ATTACK and input_state.was_pressed(Action.ATTACK):
            self.combo.request_next()

        # 점프·패링·공격 중이거나 점프를 기다리는 중에는 새 이동을 시작하지 않고, 진행 중인 한 칸만 마저 간다.
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
        elif self.state == ATTACK and self.combo.finished:
            self.fsm.trigger("end_attack")

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

        if self.state == ATTACK:
            self._draw_attack(renderer, center_x, bottom)
            return

        # 그림의 발끝(아래 가운데)을 칸의 아래 가운데에 맞춘다. 점프 중에는 lift 만큼 띄운다.
        sprite_state = SPRITE_FALLBACK.get(self.state, self.state)
        if self.facing == Facing.LEFT and sprite_state in LEFT_SHEET_STATES:
            view, flip = "side_left", False
        frame_index = 0 if sprite_state != self.state else self.animation.frame_index
        renderer.draw_sprite_frame(
            sprite_sheet_path(sprite_state, view),
            frame_index,
            config.PLAYER_SPRITE_WIDTH,
            config.PLAYER_SPRITE_HEIGHT,
            center_x,
            bottom + lift,
            config.PLAYER_RENDER_WIDTH,
            config.PLAYER_RENDER_HEIGHT,
            flip_horizontal=flip,
        )

    def _draw_attack(self, renderer, center_x: float, bottom: float) -> None:
        """지금 타의 공격 그림(96×64 캔버스)을 발끝이 칸 아래 가운데에 오도록 그린다.

        아래를 보면 정면 그림, 오른쪽·왼쪽은 측면 그림(왼쪽은 좌우 반전)을 쓴다.
        후면 그림은 아직 없어 위를 볼 때는 임시로 측면 그림을 쓴다.
        """
        width, height = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        scale = config.RENDER_SCALE
        frame = self.combo.frame_index
        view = attack_view(self.facing)
        shifts = config.PLAYER_ATTACK_FRAME_SHIFTS_FRONT if view == "front" else config.PLAYER_ATTACK_FRAME_SHIFTS
        shift_x, shift_y = shifts[self.combo.index][frame]
        flip = self.facing == Facing.LEFT
        forward = -1 if flip else 1
        canvas_x = center_x + shift_x * scale * forward  # 캔버스 아래 가운데
        canvas_bottom = bottom - config.PLAYER_ATTACK_FOOT_MARGIN * scale + shift_y * scale
        hand_x, hand_y, angle, behind, *rest = ATTACK_SWORD_TABLES[view][self.combo.index][frame]
        length = rest[0] if rest else 1.0

        def draw_layer(path: str) -> None:
            renderer.draw_sprite_frame(
                path, frame, width, height,
                canvas_x, canvas_bottom, width * scale, height * scale, flip_horizontal=flip,
            )

        # 두 손 잡기: 몸(두 팔, 칼 뒤의 왼손) → 칼 → 오른손 레이어 (오른손이 칼을 감싸 쥔 모습)
        if not behind:
            draw_layer(attack_sheet_path(self.combo.hit_number, view))
        self._draw_sword(renderer, canvas_x, canvas_bottom, hand_x, hand_y, angle, flip, length)
        if behind:
            draw_layer(attack_sheet_path(self.combo.hit_number, view))
        draw_layer(attack_hand_sheet_path(self.combo.hit_number, view))

    def _draw_sword(self, renderer, canvas_x: float, canvas_bottom: float,
                    hand_x: int, hand_y: int, angle: float, flip: bool, length: float = 1.0) -> None:
        """칼 그림 한 장을 손 위치에 놓고 각도만큼 돌려 그린다. 그림 한가운데가 손이다.

        length 는 칼 길이 비율이다. 화면 안쪽·바깥쪽으로 찌르는 칼은 원근으로 짧아 보이게 그린다.

        왼쪽을 볼 때는 캔버스처럼 손 위치를 좌우로 뒤집고, 칼은 뒤집은 뒤 반대로 돌린다 (칼끝 180 - 각도).
        """
        width, height = config.PLAYER_ATTACK_SPRITE_WIDTH, config.PLAYER_ATTACK_SPRITE_HEIGHT
        scale = config.RENDER_SCALE
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
