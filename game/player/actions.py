"""정해진 시간 동안 이어지는 주인공 행동: 점프, 패링, 검 공격 (delta time 기반 순수 로직).

모든 행동이 frame_count 장의 애니메이션 프레임을 행동 진행도에 맞춰 고른다 (진행도를 프레임 수로 등분).
LoopAnimation 과 같은 reset() / update(dt) / frame_index 를 제공해 Player 가 같은 방식으로 다룬다.
"""
from __future__ import annotations

import math


def frame_for_progress(progress: float, frame_ends: tuple[float, ...]) -> int:
    """진행도(0~1)에 해당하는 프레임 번호. frame_ends 는 각 프레임이 끝나는 진행도 (마지막 1.0)."""
    return next(i for i, end in enumerate(frame_ends) if progress < end or end == 1.0)


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


class Dodge(TimedAction):
    """회피: duration 초 동안 미끄러지듯 이동한다 (이동 자체는 GridMover.dash). 그동안 무적.

    그림은 아직 없어 걷기 그림 frame_count 장을 회피 시간 동안 한 번 재생한다.
    """


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


class SwordAttack(TimedAction):
    """검 공격 1타. frame_ends 는 각 프레임이 끝나는 진행도 (마지막 프레임은 마무리 자세).

    제자리 공격이라 논리적 칸 위치는 바뀌지 않는다. 공격 판정은 몬스터를 개발할 때 연결한다.
    """

    def __init__(self, duration: float, frame_ends: tuple[float, ...]) -> None:
        super().__init__(duration, len(frame_ends))
        if list(frame_ends) != sorted(frame_ends) or frame_ends[-1] != 1.0:
            raise ValueError("frame_ends 는 오름차순이고 마지막 값이 1.0 이어야 합니다.")
        self.frame_ends = frame_ends

    @property
    def frame_index(self) -> int:
        return frame_for_progress(self.progress, self.frame_ends)


class SwordCombo:
    """검 3단 콤보. 지금 타(SwordAttack)의 진행, 다음 타 예약, 콤보 유예 시간, 3타 후 쿨타임을 관리한다.

    - start(): 공격 시작. 유예 시간 안이면 다음 타, 아니면 1타부터.
    - request_next(): 공격 중 클릭. 마지막 타가 아니면 다음 타를 예약한다.
    - update(dt): 지금 타를 진행한다. 예약이 있으면 마지막(마무리) 프레임에 들어가는 순간 다음 타로 넘어간다.
    - tick(dt): 유예·쿨타임 시간을 줄인다 (상태와 상관없이 매 프레임).
    Player 의 애니메이션처럼 frame_index / finished / reset() 을 제공한다.
    """

    def __init__(self, durations: tuple[float, ...], frame_ends: tuple[tuple[float, ...], ...],
                 combo_window: float, cooldown: float) -> None:
        if len(durations) != len(frame_ends) or not durations:
            raise ValueError("durations 와 frame_ends 는 타 수만큼 있어야 합니다.")
        self.hits = [SwordAttack(d, ends) for d, ends in zip(durations, frame_ends)]
        self.combo_window = combo_window
        self.cooldown = cooldown
        self.index = 0  # 지금(또는 마지막) 타. 0 = 1타
        self.queued = False
        self.window_left = 0.0
        self.cooldown_left = 0.0
        self.strike_id = 0  # 타가 새로 시작할 때마다 1씩 늘어난다 (공격 판정을 한 타에 한 번만 내기 위함)

    @property
    def current(self) -> SwordAttack:
        return self.hits[self.index]

    @property
    def hit_number(self) -> int:
        """1타 = 1"""
        return self.index + 1

    @property
    def is_last_hit(self) -> bool:
        return self.index == len(self.hits) - 1

    @property
    def can_start(self) -> bool:
        return self.cooldown_left <= 0.0

    @property
    def frame_index(self) -> int:
        return self.current.frame_index

    @property
    def finished(self) -> bool:
        return self.current.finished

    def reset(self) -> None:
        """상태 전환 때 호출된다. 타 선택은 start() 가 하므로 여기서는 아무것도 하지 않는다."""

    def start(self) -> None:
        if self.window_left > 0.0 and not self.is_last_hit:
            self.index += 1
        else:
            self.index = 0
        self.window_left = 0.0
        self.queued = False
        self.strike_id += 1
        self.current.reset()

    def request_next(self) -> None:
        if not self.is_last_hit:
            self.queued = True

    def cancel_window(self) -> None:
        """다른 행동(점프·패링)을 하면 콤보가 끊긴다."""
        self.window_left = 0.0

    def update(self, dt: float) -> None:
        hit = self.current
        hit.update(dt)
        if self.queued and hit.progress >= hit.frame_ends[-2]:
            # 마지막(마무리) 프레임을 건너뛰고 다음 타로
            self.index += 1
            self.queued = False
            self.strike_id += 1
            self.current.reset()
        elif hit.finished:
            if self.is_last_hit:
                self.cooldown_left = self.cooldown
                self.window_left = 0.0
            else:
                self.window_left = self.combo_window

    def tick(self, dt: float) -> None:
        self.window_left = max(0.0, self.window_left - dt)
        self.cooldown_left = max(0.0, self.cooldown_left - dt)
