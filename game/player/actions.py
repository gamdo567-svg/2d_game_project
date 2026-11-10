"""정해진 시간 동안 이어지는 주인공 행동: 점프, 패링 (delta time 기반 순수 로직).

두 행동 모두 frame_count 장의 애니메이션 프레임을 행동 진행도에 맞춰 고른다 (진행도를 프레임 수로 등분).
LoopAnimation 과 같은 reset() / update(dt) / frame_index 를 제공해 Player 가 같은 방식으로 다룬다.
"""
from __future__ import annotations

import math


class TimedAction:
    """duration 초 동안 진행되는 행동. 끝나면 finished 가 True."""

    def __init__(self, duration: float, frame_count: int) -> None:
        if duration <= 0:
            raise ValueError("duration 은 0 보다 커야 합니다.")
        if frame_count <= 0:
            raise ValueError("frame_count 는 1 이상이어야 합니다.")
        self.duration = duration
        self.frame_count = frame_count
        self.elapsed = 0.0

    @property
    def progress(self) -> float:
        """0.0(시작) ~ 1.0(끝)"""
        return min(1.0, self.elapsed / self.duration)

    @property
    def finished(self) -> bool:
        return self.elapsed >= self.duration

    @property
    def frame_index(self) -> int:
        return min(self.frame_count - 1, int(self.progress * self.frame_count))

    def reset(self) -> None:
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed = min(self.duration, self.elapsed + dt)


class Jump(TimedAction):
    """제자리 점프. frame_ends 는 각 프레임이 끝나는 진행도 (예: 웅크림 0.2, 도약 0.35, 공중 0.8, 착지 1.0).

    첫 프레임(웅크림)이 끝나면 떠오르고, 마지막 프레임(착지)이 시작될 때 땅에 닿는다.
    height 는 그림을 띄우는 높이(칸 단위)이며 논리적 칸 위치는 바뀌지 않는다.
    """

    def __init__(self, duration: float, max_height: float, frame_ends: tuple[float, ...]) -> None:
        super().__init__(duration, len(frame_ends))
        if list(frame_ends) != sorted(frame_ends) or frame_ends[-1] != 1.0 or len(frame_ends) < 3:
            raise ValueError("frame_ends 는 3개 이상, 오름차순, 마지막 값 1.0 이어야 합니다.")
        self.max_height = max_height
        self.frame_ends = frame_ends
        self._lift_off = frame_ends[0]
        self._touch_down = frame_ends[-2]

    @property
    def frame_index(self) -> int:
        p = self.progress
        return next(i for i, end in enumerate(self.frame_ends) if p < end or end == 1.0)

    @property
    def height(self) -> float:
        t = (self.progress - self._lift_off) / (self._touch_down - self._lift_off)  # 공중 구간 0~1
        if not 0.0 < t < 1.0:
            return 0.0
        return self.max_height * math.sin(math.pi * t)

    @property
    def is_airborne(self) -> bool:
        """공중에 떠 있는지 (나중에 하단 공격 회피 판정에 쓴다)."""
        return self.height > 0.0


class Parry(TimedAction):
    """패링. 누른 순간부터 window 초 동안 막기 판정, 나머지는 복귀 동작."""

    def __init__(self, duration: float, window: float, frame_count: int) -> None:
        super().__init__(duration, frame_count)
        if not 0 < window <= duration:
            raise ValueError("window 는 0 보다 크고 duration 이하여야 합니다.")
        self.window = window

    @property
    def is_active(self) -> bool:
        """막기 판정 중인지 (적 공격 연결은 몬스터 개발 때)."""
        return self.elapsed < self.window
