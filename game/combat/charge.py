"""전기 능력 (2026-11-20 사용자 결정): 전기를 입힌 검으로 때리면 상대에게 파란 게이지가 차고(때릴 때는 효과 없음),
E 로 검의 번개를 끄면(방전) 쌓인 게이지만큼 상대가 감전된다.

- 게이지: 한 대에 CHARGE_PER_HIT 씩, 최대 1. 방전할 때까지 줄지 않는다.
- 방전: 피해 = SHOCK_DAMAGE_FULL × 게이지, 감전 시간 = SHOCK_TIME_FULL × 게이지. 감전되는 동안 상대는 멈춘다 (장면·대상이 처리).
- 감전 그림: 만화처럼 검은 그림자 → 흰 그림 → 원래 그림을 빠르게 번갈아(shock_look), 몸이 파르르 떨리고(shock_jitter),
  몸 위로 번개가 찌릿찌릿 튄다.
- 정전기: 게이지가 찰수록 몸 둘레에서 작은 번개가 더 자주·더 길게 튄다.

StaticField 의 좌표는 대상 발 밑 가운데 기준 원본 픽셀 (위쪽 +). pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game import config
from game.player.sword_lightning import _line

BLACK, WHITE, NORMAL = "black", "white", "normal"


class Charge:
    """전기 게이지와 감전 상태."""

    def __init__(self) -> None:
        self.value = 0.0  # 0~1
        self.shock_left = 0.0  # 남은 감전 시간
        self.shock_time = 0.0  # 이번 감전 전체 시간
        self.shock_power = 0.0  # 이번 감전 세기 (방전한 게이지)

    @property
    def shocked(self) -> bool:
        return self.shock_left > 0.0

    def add(self) -> None:
        """전기 속성 공격을 한 대 맞음."""
        self.value = min(1.0, self.value + config.CHARGE_PER_HIT)

    def discharge(self) -> int:
        """방전: 쌓인 게이지만큼 감전된다. 이번에 받을 피해를 돌려준다 (게이지가 없으면 0, 감전도 없음)."""
        power = self.value
        self.value = 0.0
        if power <= 0.0:
            return 0
        self.shock_power = power
        self.shock_time = config.SHOCK_TIME_FULL * power
        self.shock_left = self.shock_time
        return max(1, round(config.SHOCK_DAMAGE_FULL * power))

    def clear(self) -> None:
        """죽음·다시 나타남 등으로 모두 없앰."""
        self.value = 0.0
        self.shock_left = 0.0

    def update(self, dt: float) -> None:
        self.shock_left = max(0.0, self.shock_left - dt)

    @property
    def shock_age(self) -> float:
        return self.shock_time - self.shock_left

    @property
    def shock_look(self) -> str:
        """감전 중 지금 보여 줄 그림: 검은 그림자 → 흰 그림 → 원래 그림을 SHOCK_FLASH 초씩 돌아가며 (만화처럼)."""
        if not self.shocked:
            return NORMAL
        cycle = (BLACK, WHITE, BLACK, WHITE, NORMAL)
        return cycle[int(self.shock_age / config.SHOCK_FLASH) % len(cycle)]

    @property
    def shock_jitter(self) -> tuple[int, int]:
        """감전 중 몸이 파르르 떨리는 정도 (원본 픽셀, 장마다 다름)."""
        if not self.shocked:
            return (0, 0)
        k = int(self.shock_age / 0.035)
        return ((k * 7 + 3) % 3 - 1, (k * 5 + 1) % 3 - 1)


@dataclass
class Arc:
    points: list[tuple[int, int]]  # 원본 픽셀 꺾은선
    life: float
    big: bool = False  # 감전 번개 (굵고 밝게)
    age: float = 0.0


@dataclass
class StaticField:
    """정전기·감전 번개 그림용. body = (가로, 세로) 원본 픽셀."""
    body: tuple[float, float]
    rng: random.Random = field(default_factory=random.Random)
    arcs: list[Arc] = field(default_factory=list)
    _timer: float = 0.0
    _zap_timer: float = 0.0

    def update(self, dt: float, value: float, shocked: bool) -> None:
        for a in self.arcs:
            a.age += dt
        self.arcs = [a for a in self.arcs if a.age < a.life]
        rng = self.rng
        if value > 0.0:  # 정전기: 게이지가 찰수록 자주·길게
            self._timer -= dt
            while self._timer <= 0.0:
                self._spawn_static(value)
                self._timer += rng.expovariate(config.STATIC_RATE_MIN + config.STATIC_RATE_MAX * value)
        if shocked:  # 감전: 몸을 가로지르는 큰 번개가 쉴 새 없이
            self._zap_timer -= dt
            while self._zap_timer <= 0.0:
                self._spawn_zap()
                self._zap_timer += rng.expovariate(config.SHOCK_ZAP_RATE)

    def _edge_point(self) -> tuple[float, float, float]:
        """몸 둘레(타원) 위의 한 점과 바깥 방향 각도."""
        w, h = self.body
        a = self.rng.uniform(0, 2 * math.pi)
        return w / 2 * math.cos(a), h / 2 + h / 2 * math.sin(a), a

    def _jagged(self, x0: float, y0: float, x1: float, y1: float, steps: int, wobble: float) -> list[tuple[int, int]]:
        rng = self.rng
        pts = []
        nx, ny = -(y1 - y0), x1 - x0
        n = math.hypot(nx, ny) or 1
        nx, ny = nx / n, ny / n
        for k in range(steps + 1):
            t = k / steps
            off = 0 if k in (0, steps) else rng.uniform(-wobble, wobble)
            pts.append((math.floor(x0 + (x1 - x0) * t + nx * off), math.floor(y0 + (y1 - y0) * t + ny * off)))
        return pts

    def _spawn_static(self, value: float) -> None:
        rng = self.rng
        x, y, a = self._edge_point()
        length = 3 + 10 * value * rng.uniform(0.5, 1.0)  # 찰수록 길게
        a += rng.uniform(-0.8, 0.8)
        x1, y1 = x + math.cos(a) * length, y + math.sin(a) * length
        self.arcs.append(Arc(self._jagged(x, y, x1, y1, max(2, round(length / 2.5)), 1.5),
                             rng.uniform(0.05, 0.11)))

    def _spawn_zap(self) -> None:
        rng = self.rng
        x0, y0, _ = self._edge_point()
        x1, y1, _ = self._edge_point()
        main = self._jagged(x0, y0, x1, y1, 7, 3.5)
        life = rng.uniform(0.04, 0.09)
        self.arcs.append(Arc(main, life, big=True))
        if rng.random() < 0.6:  # 갈래: 줄기 중간에서 짧게 뻗음
            bx, by = main[rng.randrange(2, len(main) - 2)]
            a = rng.uniform(0, 2 * math.pi)
            n = rng.uniform(4, 9)
            self.arcs.append(Arc(self._jagged(bx, by, bx + math.cos(a) * n, by + math.sin(a) * n, 3, 1.5), life))

    def pixels(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        """그릴 점 (x, y, 색): 번개 꺾은선을 픽셀로. 큰 번개는 흰 심 + 하늘색 둘레."""
        out = []
        for a in self.arcs:
            core = config.STATIC_CORE_COLOR if a.age < a.life * 0.6 else config.STATIC_GLOW_COLOR
            line = []
            for p, q in zip(a.points, a.points[1:]):
                line += _line(p, q)
            # 둘레 하늘색 빛: 큰 번개는 사방, 정전기는 양옆만 (가늘게)
            around = ((1, 0), (-1, 0), (0, 1), (0, -1)) if a.big else ((1, 0), (-1, 0))
            for x, y in line:
                for dx, dy in around:
                    out.append((x + dx, y + dy, config.STATIC_GLOW_COLOR))
            out += [(x, y, core) for x, y in line]
        return out


def draw_static(renderer, static: StaticField, cx: float, bottom: float) -> None:
    """정전기·감전 번개를 화면에 그린다 (cx, bottom = 대상 발 밑 가운데 화면 좌표)."""
    s = config.RENDER_SCALE
    for x, y, colour in static.pixels():
        renderer.fill_rect(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, colour)


def draw_charge_bar(renderer, value: float, cx: float, top: float, half_width: float) -> None:
    """파란 전기 게이지 막대 (게이지가 있을 때만). top = 막대 아래쪽 화면 y."""
    if value <= 0.0:
        return
    s = config.RENDER_SCALE
    renderer.fill_rect(cx - half_width, top, cx + half_width, top + 2 * s, config.COLOR_BAR_BACK)
    renderer.fill_rect(cx - half_width, top, cx - half_width + 2 * half_width * value, top + 2 * s,
                       config.COLOR_CHARGE_BAR)
