"""주인공 상태 머신 (Python transitions 라이브러리 사용).

현재 구현한 상태는 idle, walk, jump, parry, sword_attack, dodge, hurt, enchant(검 속성 입히기) 여덟 가지다.
PRE-PRD 2.7 의 stun 은
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
ATTACK = "sword_attack"
DODGE = "dodge"
HURT = "hurt"
ENCHANT = "enchant"  # 검에 속성 입히기 (2026-11-20)

STATES: list[str] = [IDLE, WALK, JUMP, PARRY, ATTACK, DODGE, HURT, ENCHANT]
# 서 있거나 걷는 중에만 새 행동(점프, 패링, 공격)을 시작할 수 있다.
FREE_STATES: list[str] = [IDLE, WALK]

# 전환 규칙. 새 상태를 추가할 때 여기에 규칙을 함께 적는다.
TRANSITIONS: list[dict[str, str | list[str]]] = [
    {"trigger": "start_walk", "source": IDLE, "dest": WALK},
    {"trigger": "stop_walk", "source": WALK, "dest": IDLE},
    # 후딜 캔슬 (2026-11-17 사용자 결정): 판정이 나온 뒤에는 공격을 회피·점프·패링으로 끊는다. 조건 확인은 Player 가 한다.
    {"trigger": "jump", "source": FREE_STATES + [ATTACK], "dest": JUMP},
    {"trigger": "land", "source": JUMP, "dest": IDLE},
    {"trigger": "parry", "source": FREE_STATES + [ATTACK], "dest": PARRY},
    {"trigger": "end_parry", "source": PARRY, "dest": IDLE},
    # 패링에 성공하면 우선권: 패링 동작이 끝나기 전에도 바로 공격 (PRE-PRD 2.2). 조건 확인은 Player 가 한다.
    {"trigger": "attack", "source": FREE_STATES + [PARRY], "dest": ATTACK},
    {"trigger": "end_attack", "source": ATTACK, "dest": IDLE},
    {"trigger": "dodge", "source": FREE_STATES + [ATTACK], "dest": DODGE},
    {"trigger": "end_dodge", "source": DODGE, "dest": IDLE},
    # 검에 속성 입히기 (E): 서 있거나 걷는 중에만, 그동안 이동하지 않음
    {"trigger": "enchant", "source": FREE_STATES, "dest": ENCHANT},
    {"trigger": "end_enchant", "source": ENCHANT, "dest": IDLE},
    # 맞으면 짧게 경직 (회피 무적으로 피하지 못하는 공격은 회피 중에도 맞는다)
    {"trigger": "hurt", "source": [IDLE, WALK, JUMP, PARRY, ATTACK, DODGE, HURT, ENCHANT], "dest": HURT},
    {"trigger": "end_hurt", "source": HURT, "dest": IDLE},
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
