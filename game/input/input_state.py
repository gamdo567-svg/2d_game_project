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


class InputState:
    """현재 프레임의 입력 상태."""

    def __init__(self) -> None:
        self._held: set[Action] = set()
        self._pressed: set[Action] = set()
        self._released: set[Action] = set()
        self.quit_requested = False  # 창 닫기 버튼 등

    def begin_frame(self) -> None:
        """새 프레임 시작. '이번 프레임에 눌림/떼어짐' 정보를 초기화한다."""
        self._pressed.clear()
        self._released.clear()

    def press(self, action: Action) -> None:
        if action not in self._held:
            self._pressed.add(action)
        self._held.add(action)

    def release(self, action: Action) -> None:
        if action in self._held:
            self._released.add(action)
        self._held.discard(action)

    def request_quit(self) -> None:
        self.quit_requested = True

    def release_all(self) -> None:
        """모든 키를 뗀 상태로 만든다 (창 포커스를 잃었을 때 등)."""
        self._released.update(self._held)
        self._held.clear()

    def is_held(self, action: Action) -> bool:
        """현재 누르고 있는지."""
        return action in self._held

    def was_pressed(self, action: Action) -> bool:
        """이번 프레임에 새로 눌렸는지."""
        return action in self._pressed

    def was_released(self, action: Action) -> bool:
        """이번 프레임에 떼어졌는지."""
        return action in self._released
