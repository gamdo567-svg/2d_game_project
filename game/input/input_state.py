"""행동(Action) 단위 입력 상태.

게임 로직은 키 코드가 아니라 Action 으로 입력을 확인한다.
키 배치는 pico2d_input.KEY_BINDINGS 에서만 정의하므로,
키 변경이 게임 로직에 영향을 주지 않는다.
"""
from __future__ import annotations

from enum import Enum, auto


class Action(Enum):
    """게임에서 사용하는 입력 행동.

    이동, 공격, 회피, 패링 등은 해당 기능을 개발할 때 추가한다.
    """

    QUIT = auto()  # 게임 종료 (현재 ESC)
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()


# 이동 행동 -> 칸 좌표 방향 (dx, dy). dy 는 위쪽이 +1.
MOVE_VECTORS: dict[Action, tuple[int, int]] = {
    Action.MOVE_UP: (0, 1),
    Action.MOVE_DOWN: (0, -1),
    Action.MOVE_LEFT: (-1, 0),
    Action.MOVE_RIGHT: (1, 0),
}


class InputState:
    """현재 프레임의 입력 상태."""

    def __init__(self) -> None:
        self._held: set[Action] = set()
        self._pressed: set[Action] = set()
        self._released: set[Action] = set()
        self._move_order: list[Action] = []  # 누르고 있는 이동 행동, 나중에 누른 것이 뒤
        self.quit_requested = False  # 창 닫기 버튼 등

    def begin_frame(self) -> None:
        """새 프레임 시작. '이번 프레임에 눌림/떼어짐' 정보를 초기화한다."""
        self._pressed.clear()
        self._released.clear()

    def press(self, action: Action) -> None:
        if action not in self._held:
            self._pressed.add(action)
            if action in MOVE_VECTORS:
                self._move_order.append(action)
        self._held.add(action)

    def release(self, action: Action) -> None:
        if action in self._held:
            self._released.add(action)
            if action in MOVE_VECTORS:
                self._move_order.remove(action)
        self._held.discard(action)

    def request_quit(self) -> None:
        self.quit_requested = True

    def release_all(self) -> None:
        """모든 키를 뗀 상태로 만든다 (창 포커스를 잃었을 때 등)."""
        self._released.update(self._held)
        self._held.clear()
        self._move_order.clear()

    def is_held(self, action: Action) -> bool:
        """현재 누르고 있는지."""
        return action in self._held

    def was_pressed(self, action: Action) -> bool:
        """이번 프레임에 새로 눌렸는지."""
        return action in self._pressed

    def was_released(self, action: Action) -> bool:
        """이번 프레임에 떼어졌는지."""
        return action in self._released

    def move_direction(self) -> tuple[int, int]:
        """누르고 있는 이동 키의 방향 (dx, dy). 상하좌우 4방향 중 하나이거나 (0, 0).

        대각선 이동은 없다. 여러 방향을 함께 누르면 가장 나중에 누른 방향을 따르고,
        그 키를 떼면 아직 누르고 있는 이전 방향으로 돌아간다.
        """
        if not self._move_order:
            return 0, 0
        return MOVE_VECTORS[self._move_order[-1]]
