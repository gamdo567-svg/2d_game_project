"""delta time 기반 프레임 애니메이션 (반복 재생)."""
from __future__ import annotations


class LoopAnimation:
    """frame_count 장의 프레임을 frame_duration 초마다 넘기며 반복한다."""

    def __init__(self, frame_count: int, frame_duration: float) -> None:
        if frame_count <= 0:
            raise ValueError("frame_count 는 1 이상이어야 합니다.")
        if frame_duration <= 0:
            raise ValueError("frame_duration 은 0 보다 커야 합니다.")
        self.frame_count = frame_count
        self.frame_duration = frame_duration
        self._elapsed = 0.0

    @property
    def frame_index(self) -> int:
        return int(self._elapsed / self.frame_duration) % self.frame_count

    def reset(self) -> None:
        self._elapsed = 0.0

    def update(self, dt: float) -> None:
        # 한 바퀴 시간으로 나눈 나머지만 남겨 값이 끝없이 커지지 않게 한다.
        self._elapsed = (self._elapsed + dt) % (self.frame_duration * self.frame_count)
