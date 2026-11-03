"""pico2d 캔버스 수명 주기와 메인 루프.

프레임 순서: 시간(dt) 계산 -> 입력 -> 로직 갱신 -> 그리기
"""
from __future__ import annotations

import time

import pico2d

from game import config
from game.core.clock import FrameClock
from game.input.input_state import Action, InputState
from game.input.pico2d_input import poll_input
from game.render.renderer import Renderer
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid


def run(max_frames: int | None = None) -> int:
    """게임을 실행하고, 실행된 프레임 수를 반환한다.

    max_frames 를 지정하면 그 프레임 수만큼 실행한 뒤 종료한다 (자동 테스트용).
    """
    pico2d.open_canvas(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, sync=config.VSYNC)
    try:
        pico2d.hide_lattice()  # pico2d 기본 격자 배경 끄기

        grid = Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE)
        renderer = Renderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        input_state = InputState()
        clock = FrameClock(config.MAX_DELTA_TIME)
        scene = FieldScene(grid)

        frames = 0
        while True:
            dt = clock.tick(time.perf_counter())

            poll_input(input_state)
            if input_state.quit_requested or input_state.was_pressed(Action.QUIT):
                break

            scene.update(dt, input_state)

            pico2d.clear_canvas()
            scene.draw(renderer)
            pico2d.update_canvas()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
    finally:
        pico2d.close_canvas()

    return frames
