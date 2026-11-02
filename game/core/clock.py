"""프레임 간 경과 시간(delta time) 계산.

pico2d 에 의존하지 않는 순수 로직이므로 단위 테스트가 가능하다.
게임 로직의 모든 시간 기반 변화(이동, 쿨다운, 애니메이션 등)는
이 클래스가 돌려주는 dt(초)를 기준으로 계산한다.
"""
from __future__ import annotations


class FrameClock:
    """매 프레임 호출하여 직전 프레임 이후 경과 시간(초)을 돌려준다."""

    def __init__(self, max_dt: float) -> None:
        if max_dt <= 0:
            raise ValueError("max_dt 는 0보다 커야 합니다.")
        self.max_dt = max_dt
        self.total_time = 0.0  # clamp 가 반영된 누적 게임 시간(초)
        self._last_time: float | None = None

    def tick(self, now: float) -> float:
        """현재 시각 now(초)를 받아 dt 를 반환한다.

        - 첫 호출은 기준 시각만 기록하고 0 을 반환한다.
        - 시각이 거꾸로 흐르면 0 을 반환한다.
        - dt 가 max_dt 보다 크면 max_dt 로 제한한다.
        """
        if self._last_time is None:
            self._last_time = now
            return 0.0

        dt = now - self._last_time
        self._last_time = now

        if dt < 0.0:
            dt = 0.0
        elif dt > self.max_dt:
            dt = self.max_dt

        self.total_time += dt
        return dt
