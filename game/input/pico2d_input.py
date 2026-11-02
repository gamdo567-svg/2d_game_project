"""pico2d 이벤트를 InputState 로 변환한다.

pico2d 의 입력 이벤트를 직접 다루는 코드는 이 모듈에만 둔다.
"""
from __future__ import annotations

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDL_QUIT, SDLK_ESCAPE, get_events

from game.input.input_state import Action, InputState

# 키 코드 -> 행동. 키 배치 변경은 여기서만 한다.
KEY_BINDINGS: dict[int, Action] = {
    SDLK_ESCAPE: Action.QUIT,
}


def poll_input(state: InputState) -> None:
    """이번 프레임의 pico2d 이벤트를 읽어 state 에 반영한다."""
    state.begin_frame()
    for event in get_events():
        if event.type == SDL_QUIT:
            state.request_quit()
        elif event.type == SDL_KEYDOWN:
            action = KEY_BINDINGS.get(event.key)
            if action is not None:
                state.press(action)
        elif event.type == SDL_KEYUP:
            action = KEY_BINDINGS.get(event.key)
            if action is not None:
                state.release(action)
