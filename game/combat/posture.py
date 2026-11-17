"""패링 게이지 (PRE-PRD 2.2, 2026-11-17 사용자 결정).

- 패링당하면 전체의 25% 가 찬다 (add_parried).
- 가득 차면 POSTURE_STUN_TIME 동안 기절한다. 기절이 끝나면 게이지는 0 이 된다.
- 시간이 지나면 천천히 줄어든다 (기절 중에는 줄지 않음). 단 몬스터형은 저절로 줄지 않는다 (decays=False,
  2026-11-17 사용자 결정).
- 이 게이지를 가진 쪽이 패링에 성공하면 50% 줄어든다 (relieve_by_parry).
주인공과 적이 모두 쓴다. 모든 시간은 dt(초).
"""
from __future__ import annotations

from game import config


class PostureGauge:
    def __init__(self, decays: bool = True) -> None:
        self.value = 0.0  # 0.0 ~ 1.0
        self.stun_left = 0.0
        self.decays = decays  # 시간이 지나면 저절로 줄어드는지 (사람형 True, 몬스터형 False)

    @property
    def is_stunned(self) -> bool:
        return self.stun_left > 0.0

    def add_parried(self) -> bool:
        """패링당했다. 가득 차서 기절이 시작되면 True."""
        if self.is_stunned:
            return False
        self.value = min(1.0, self.value + config.POSTURE_PARRIED_GAIN)
        if self.value >= 1.0:
            self.stun_left = config.POSTURE_STUN_TIME
            return True
        return False

    def relieve_by_parry(self) -> None:
        """패링에 성공했다."""
        self.value = max(0.0, self.value - config.POSTURE_PARRY_RELIEF)

    def update(self, dt: float) -> None:
        if self.is_stunned:
            self.stun_left = max(0.0, self.stun_left - dt)
            if not self.is_stunned:
                self.value = 0.0
            return
        if self.decays:
            self.value = max(0.0, self.value - config.POSTURE_DECAY_PER_SECOND * dt)
