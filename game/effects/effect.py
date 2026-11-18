"""스프라이트 시트 이펙트와 화면 흔들림 (delta time 기반 순수 로직, pico2d 를 쓰지 않음).

- SpriteEffect: 칸 좌표의 한 점에서 시트 이펙트를 한 번 재생한다. 몇 번째 프레임인지만 계산하고 그리기는 장면이 한다.
- ScreenShake: 카메라에 더할 화면 픽셀 오프셋. 세기가 시간에 따라 0 으로 줄고, 끝나면 (0, 0).
- loop_frame / draw_stun_stars: 반복 이펙트 (기절 별, 주인공·적 공용).
"""
from __future__ import annotations

import math
from typing import Any

from game import config


class SpriteEffect:
    """spec: config 의 이펙트 설정 (path, frame_size, columns, frames, fps, shake[선택]).

    (x, y) 는 이펙트가 터지는 점의 칸 좌표(실수). 칸 (c, r) 의 왼쪽 아래 모서리가 (c, r) 이다.
    """

    def __init__(self, spec: dict[str, Any], x: float, y: float) -> None:
        if spec["frames"] <= 0 or spec["fps"] <= 0:
            raise ValueError("frames 와 fps 는 0 보다 커야 합니다.")
        self.spec = spec
        self.x = x
        self.y = y
        self.elapsed = 0.0

    @property
    def duration(self) -> float:
        return self.spec["frames"] / self.spec["fps"]

    @property
    def finished(self) -> bool:
        return self.elapsed >= self.duration

    @property
    def frame_index(self) -> int:
        return min(self.spec["frames"] - 1, int(self.elapsed * self.spec["fps"]))

    @property
    def shake(self) -> dict[str, float] | None:
        """터질 때 함께 낼 화면 흔들림 설정 (없으면 None)."""
        return self.spec.get("shake")

    def update(self, dt: float) -> None:
        self.elapsed = min(self.duration, self.elapsed + dt)


class ScreenShake:
    """화면 흔들림. start() 로 시작하고 update(dt) 로 진행, offset 을 카메라 위치에 더한다."""

    def __init__(self) -> None:
        self.amplitude = 0.0
        self.duration = 0.0
        self.frequency = 0.0
        self.elapsed = 0.0

    @property
    def active(self) -> bool:
        return self.elapsed < self.duration

    @property
    def strength(self) -> float:
        """지금 세기 (픽셀). 시작할 때 amplitude, 끝나면 0."""
        if not self.active:
            return 0.0
        return self.amplitude * (1.0 - self.elapsed / self.duration)

    def start(self, amplitude: float, duration: float, frequency: float) -> None:
        """흔들림을 시작한다. 이미 더 세게 흔들리는 중이면 그대로 둔다."""
        if duration <= 0:
            raise ValueError("duration 은 0 보다 커야 합니다.")
        if amplitude < self.strength:
            return
        self.amplitude = amplitude
        self.duration = duration
        self.frequency = frequency
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        if self.active:
            self.elapsed = min(self.duration, self.elapsed + dt)

    @property
    def offset(self) -> tuple[int, int]:
        """카메라에 더할 (x, y) 화면 픽셀. 도트가 번지지 않게 정수로 맞춘다."""
        k = self.strength
        if k == 0.0:
            return 0, 0
        t = self.elapsed * self.frequency * 2 * math.pi
        return round(k * math.sin(t)), round(k * 0.6 * math.cos(t * 1.37))


def loop_frame(spec: dict[str, Any], elapsed: float) -> int:
    """반복 재생하는 시트 이펙트의 지금 프레임 번호."""
    return int(elapsed * spec["fps"]) % spec["frames"]


def draw_stun_stars(renderer, center_x: float, center_y: float, scale: float, elapsed: float) -> None:
    """기절 공용 이펙트: (center_x, center_y)(화면 픽셀, 머리 꼭대기 조금 위)를 링 가운데로 별이 돈다.

    scale: 원본 픽셀 한 칸을 몇 화면 픽셀로 그릴지 (골렘은 RENDER_SCALE, 주인공은 더 작게).
    """
    spec = config.STUN_STARS_EFFECT
    w, h = spec["frame_size"]
    renderer.draw_sheet_frame(str(spec["path"]), loop_frame(spec, elapsed), spec["frames"], w, h,
                              center_x, center_y, round(w * scale), round(h * scale))
