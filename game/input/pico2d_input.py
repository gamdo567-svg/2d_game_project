"""pico2d 이벤트를 InputState 로 변환한다.

pico2d 의 입력 이벤트를 직접 다루는 코드는 이 모듈에만 둔다.
"""
from __future__ import annotations

from pico2d import (
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDL_QUIT,
    SDLK_DOWN,
    SDLK_ESCAPE,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_SPACE,
    SDLK_UP,
    SDLK_a,
    SDLK_d,
    SDLK_f,
    SDLK_s,
    SDLK_w,
    get_events,
)

from game.input.input_state import Action, InputState

# 키 코드 -> 행동. 키 배치 변경은 여기서만 한다.
KEY_BINDINGS: dict[int, Action] = {
    SDLK_ESCAPE: Action.QUIT,
    SDLK_UP: Action.MOVE_UP,
    SDLK_DOWN: Action.MOVE_DOWN,
    SDLK_LEFT: Action.MOVE_LEFT,
    SDLK_RIGHT: Action.MOVE_RIGHT,
    SDLK_w: Action.MOVE_UP,
    SDLK_s: Action.MOVE_DOWN,
    SDLK_a: Action.MOVE_LEFT,
    SDLK_d: Action.MOVE_RIGHT,
    SDLK_SPACE: Action.JUMP,
    SDLK_f: Action.PARRY,
}

# 지금 눌려 있는 키 코드. 한 행동에 키가 여러 개(예: W 와 ↑)일 때,
# 둘 중 하나를 떼어도 다른 키가 눌려 있으면 행동을 유지하기 위해 쓴다.
_held_keys: set[int] = set()


def poll_input(state: InputState) -> None:
    """이번 프레임의 pico2d 이벤트를 읽어 state 에 반영한다."""
    state.begin_frame()
    for event in get_events():
        if event.type == SDL_QUIT:
            state.request_quit()
        elif event.type == SDL_KEYDOWN:
            action = KEY_BINDINGS.get(event.key)
            if action is not None:
                _held_keys.add(event.key)
                state.press(action)
        elif event.type == SDL_KEYUP:
            action = KEY_BINDINGS.get(event.key)
            if action is not None:
                _held_keys.discard(event.key)
                if not any(KEY_BINDINGS[key] is action for key in _held_keys):
                    state.release(action)
