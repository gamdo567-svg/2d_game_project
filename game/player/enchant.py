"""검 속성 입히기 (2026-11-20 사용자 결정): 1·2·3 으로 속성을 고르고 E 로 검에 입힌다.

- 고르기만 해서는 검이 바뀌지 않는다. E 를 누르면 두 손으로 검을 세우는 동작을 하며
  이펙트가 검날 아래에서 위로 차오르고, 다 차오르면 그 속성이 검에 남는다 (다른 속성을 입히거나 풀 때까지).
- 지금 입힌 것과 같은 속성을 고른 채 E 를 누르면 속성이 풀린다.
- 차오르기 전에 동작이 끊기면(맞음 등) 입히지 않고 전 속성이 그대로 남는다.
- 지금은 그림(이펙트)만 바뀐다. 피해·추가 효과는 마법석 기획(PRE-PRD 2.3)이 정해지면 붙인다.

pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

from game import config
from game.player.actions import TimedAction


class SwordEnchant(TimedAction):
    """검 속성. selected = 고른 속성, active = 검에 입힌 속성(없으면 None), pending = 입히는 중인 속성."""

    def __init__(self) -> None:
        super().__init__(config.PLAYER_ENCHANT_DURATION, 1)
        self.selected: str = config.SWORD_ELEMENTS[0]
        self.active: str | None = None
        self.pending: str | None = None
        self.just_applied = False  # 이번 update 에서 막 입혀짐 (폭발·화면 흔들림 신호)

    def select(self, index: int) -> None:
        """index 번째 속성(0 부터)을 고른다. 검은 그대로."""
        if 0 <= index < len(config.SWORD_ELEMENTS):
            self.selected = config.SWORD_ELEMENTS[index]

    def press(self) -> bool:
        """E: 고른 속성이 이미 입혀져 있으면 풀고 False, 아니면 입히는 동작을 시작하고 True."""
        if self.selected == self.active:
            self.active = None
            return False
        self.pending = self.selected
        self.reset()
        return True

    def update(self, dt: float) -> None:
        super().update(dt)
        self.just_applied = False
        if self.pending is not None and self.rise >= 1.0:
            self.active = self.pending  # 다 차오른 순간 입혀짐
            self.pending = None
            self.just_applied = True

    def interrupt(self) -> None:
        """입히는 동작이 끊김 (다 차오르기 전이면 입히지 않음)."""
        self.pending = None

    @property
    def rise(self) -> float:
        """이펙트가 검날을 따라 차오른 정도 (0 = 손잡이, 1 = 칼끝). 동작 진행도의 RISE 구간에서 차오른다."""
        start, end = config.PLAYER_ENCHANT_RISE
        return min(1.0, max(0.0, (self.progress - start) / (end - start)))
