"""주인공 상태 머신 (Python transitions 라이브러리 사용).

현재 구현한 상태는 idle, walk, jump, parry 네 가지다.
PRE-PRD 2.7 의 dodge / sword_attack / hurt / stun 은
해당 기능을 개발할 때 STATES 와 TRANSITIONS 에 추가한다.

상태 머신은 '지금 어떤 상태인가'와 '어떤 전환이 허용되는가'만 관리한다.
이동 계산, 애니메이션 프레임, 그리기는 각각 다른 모듈이 맡는다.
"""
from __future__ import annotations

from collections.abc import Callable

from transitions import Machine

IDLE = "idle"
WALK = "walk"
JUMP = "jump"
PARRY = "parry"

STATES: list[str] = [IDLE, WALK, JUMP, PARRY]
# 서 있거나 걷는 중에만 새 행동(점프, 패링)을 시작할 수 있다.
FREE_STATES: list[str] = [IDLE, WALK]

# 전환 규칙. 새 상태를 추가할 때 여기에 규칙을 함께 적는다.
TRANSITIONS: list[dict[str, str | list[str]]] = [
    {"trigger": "start_walk", "source": IDLE, "dest": WALK},
    {"trigger": "stop_walk", "source": WALK, "dest": IDLE},
    {"trigger": "jump", "source": FREE_STATES, "dest": JUMP},
    {"trigger": "land", "source": JUMP, "dest": IDLE},
    {"trigger": "parry", "source": FREE_STATES, "dest": PARRY},
    {"trigger": "end_parry", "source": PARRY, "dest": IDLE},
]


class PlayerStateMachine:
    """주인공 상태. transitions.Machine 이 이 객체에 state 속성과 트리거 메서드를 붙인다."""

    state: str

    def __init__(self, on_state_changed: Callable[[str], None] | None = None) -> None:
        self._on_state_changed = on_state_changed
        self.machine = Machine(
            model=self,
            states=STATES,
            transitions=TRANSITIONS,
            initial=IDLE,
            auto_transitions=False,  # to_<state>() 같은 임의 전환 메서드를 만들지 않는다
            after_state_change="_notify_state_changed",
        )

    def _notify_state_changed(self) -> None:
        if self._on_state_changed is not None:
            self._on_state_changed(self.state)

    def update_movement(self, is_moving: bool) -> None:
        """이동 여부에 맞춰 idle <-> walk 를 전환한다."""
        if is_moving and self.state == IDLE:
            self.trigger("start_walk")
        elif not is_moving and self.state == WALK:
            self.trigger("stop_walk")
