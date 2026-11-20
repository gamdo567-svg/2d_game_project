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
    """전기 게이지와 감전 상태.

    안의 전기가 방출되는 흐름 (2026-11-20 사용자: 감전으로 안에 있던 전기가 방출된다는 느낌이 전혀 없음):
    방전(discharge) → 모임(SHOCK_GATHER_TIME 초: 굳은 채 둘레 전기가 가운데로 빨려 들고 몸이 파랗게 달아오르며 게이지 막대가 비워짐)
    → 폭발(update 가 피해를 돌려주는 순간) → 감전(안에서 바깥으로 번개가 뿜어지며 점점 잦아듦).
    """

    def __init__(self) -> None:
        self.value = 0.0  # 0~1
        self.gather_left = 0.0  # 방전 뒤 모이는 남은 시간
        self.shock_left = 0.0  # 남은 감전 시간
        self.shock_time = 0.0  # 이번 감전 전체 시간
        self.shock_power = 0.0  # 이번 감전 세기 (방전한 게이지)

    @property
    def shocked(self) -> bool:
        return self.shock_left > 0.0

    @property
    def gathering(self) -> bool:
        return self.gather_left > 0.0

    @property
    def frozen(self) -> bool:
        """모이는 동안과 감전 동안은 굳어 아무것도 하지 않는다."""
        return self.gathering or self.shocked

    @property
    def gather_progress(self) -> float:
        """모임 진행도 0 → 1 (1 이면 곧 폭발)."""
        if not self.gathering:
            return 0.0
        return 1.0 - self.gather_left / config.SHOCK_GATHER_TIME

    @property
    def release(self) -> float:
        """감전 중 남은 전기 1 → 0 (방출하며 잦아듦)."""
        return self.shock_left / self.shock_time if self.shocked and self.shock_time else 0.0

    @property
    def bar_value(self) -> float:
        """머리 위 파란 막대: 평소엔 게이지, 모이는 동안은 빠르게 비워짐."""
        if self.gathering:
            return self.shock_power * (1.0 - self.gather_progress)
        return self.value

    @property
    def glow(self) -> float:
        """몸이 파랗게 달아오른 정도 0~1: 모이며 차오르고 폭발한 뒤 빠르게 식음."""
        if self.gathering:
            return 0.25 + 0.75 * self.gather_progress
        if self.shocked:
            return max(0.0, 1.0 - self.shock_age / 0.25) * 0.8
        return 0.0

    def add(self) -> None:
        """전기 속성 공격을 한 대 맞음."""
        if not self.frozen:
            self.value = min(1.0, self.value + config.CHARGE_PER_HIT)

    def discharge(self) -> bool:
        """방전 시작: 쌓인 게이지가 모이기 시작한다 (피해는 모임이 끝나 터질 때 update 가 돌려줌). 게이지가 없으면 False."""
        power = self.value
        if power <= 0.0 or self.frozen:
            return False
        self.value = 0.0
        self.shock_power = power
        self.gather_left = config.SHOCK_GATHER_TIME
        return True

    def clear(self) -> None:
        """죽음·다시 나타남 등으로 모두 없앰."""
        self.value = 0.0
        self.gather_left = 0.0
        self.shock_left = 0.0

    def update(self, dt: float) -> int:
        """시간이 흐른다. 모임이 끝나 터지는 순간 그 피해를 돌려준다 (아니면 0)."""
        self.shock_left = max(0.0, self.shock_left - dt)
        if not self.gathering:
            return 0
        self.gather_left -= dt
        if self.gather_left > 0.0:
            return 0
        self.gather_left = 0.0
        self.shock_time = config.SHOCK_TIME_FULL * self.shock_power
        self.shock_left = self.shock_time
        return max(1, round(config.SHOCK_DAMAGE_FULL * self.shock_power))

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
        return (((k * 7 + 3) % 5 - 2), ((k * 5 + 1) % 3 - 1))  # 좌우 ±2, 위아래 ±1

    @property
    def shock_rim(self) -> bool:
        """감전 중 몸을 감싼 전기 테두리가 보이는 순간 (빠르게 깜빡임)."""
        return self.shocked and int(self.shock_age / 0.04) % 3 != 2


@dataclass
class Arc:
    points: list[tuple[int, int]]  # 원본 픽셀 꺾은선
    life: float
    weight: int = 0  # 0 = 정전기(가늘게), 1 = 감전 번개, 2 = 방전 폭발 번개 (굵고 빛이 넓게)
    age: float = 0.0


@dataclass
class Spark:
    """튀어 나가는 불티 (흰 → 하늘 → 파랑으로 식으며 짧은 꼬리)."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    age: float = 0.0


# 빛 겹 (안쪽 → 바깥): 흰 심, 하늘색, 파랑, 보라. 큰 번개일수록 바깥 겹까지 (2026-11-20 사용자: 철권 초풍처럼)
LAYERS_BY_WEIGHT = {0: (0, 1), 1: (0, 1, 2), 2: (0, 1, 2, 3)}  # 줄기에서 떨어진 거리(맨해튼) → 겹 번호 (심은 늘 1 픽셀)


@dataclass
class StaticField:
    """정전기·감전 번개 그림용. body = (가로, 세로) 원본 픽셀.

    철권 초풍 같은 전기 (2026-11-20 사용자: 감전 이펙트 퀄이 낮음): 번개마다 흰 심 둘레를 하늘색·파랑·보라 빛이 겹겹이 감싸고
    (큰 번개일수록 굵고 넓게), 마디마다 날카롭게 꺾이며 갈래를 친다. 방전하는 순간(burst) 몸에서 흰 섬광이 번쩍이고 굵은 번개가
    사방으로 터지며 불티가 튄다. 감전 중에는 몸을 감싸고 가로지르는 번개와 튀어 나가는 불티가 쉴 새 없이.
    """
    body: tuple[float, float]
    rng: random.Random = field(default_factory=random.Random)
    arcs: list[Arc] = field(default_factory=list)
    sparks: list[Spark] = field(default_factory=list)
    flash: float = 0.0  # 방전 섬광 남은 시간
    _timer: float = 0.0
    _zap_timer: float = 0.0

    def update(self, dt: float, value: float, shocked: bool, gather: float = 0.0, release: float = 1.0) -> None:
        """value = 게이지, shocked = 감전 중, gather = 모임 진행도(0 이면 모이지 않음), release = 감전 중 남은 전기."""
        for a in self.arcs:
            a.age += dt
        self.arcs = [a for a in self.arcs if a.age < a.life]
        for p in self.sparks:
            p.age += dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.9
            p.vy = p.vy * 0.9 - 60 * dt
        self.sparks = [p for p in self.sparks if p.age < p.life]
        self.flash = max(0.0, self.flash - dt)
        rng = self.rng
        if value > 0.0:  # 정전기: 게이지가 찰수록 자주·길게. 몸 안에 갇힌 전기도 파지직
            self._timer -= dt
            while self._timer <= 0.0:
                if rng.random() < 0.5:
                    self._spawn_inner(value)
                else:
                    self._spawn_static(value)
                self._timer += rng.expovariate(config.STATIC_RATE_MIN + config.STATIC_RATE_MAX * value)
        if gather > 0.0:  # 모임: 둘레의 전기가 가운데로 빨려 듦 (끝으로 갈수록 빠르게)
            self._zap_timer -= dt
            while self._zap_timer <= 0.0:
                self._spawn_gather()
                self._zap_timer += rng.expovariate(config.SHOCK_GATHER_RATE * (0.5 + gather))
        elif shocked:  # 감전: 몸 안에서 바깥으로 번개가 뿜어져 나옴 (남은 전기만큼, 점점 잦아듦)
            self._zap_timer -= dt
            while self._zap_timer <= 0.0:
                self._spawn_zap(release)
                self._zap_timer += rng.expovariate(config.SHOCK_ZAP_RATE * (0.25 + 0.75 * release))

    def burst(self, power: float) -> None:
        """방전하는 순간: 몸 가운데에서 흰 섬광 + 굵은 번개가 사방으로 터지고 불티가 튄다 (게이지가 클수록 크게)."""
        rng = self.rng
        w, h = self.body
        cx, cy = 0.0, h * 0.55
        self.flash = config.SHOCK_FLASH_TIME
        for k in range(config.SHOCK_BURST_BOLTS):
            a = 2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / config.SHOCK_BURST_BOLTS
            length = (max(w, h) * 0.3 + rng.uniform(4, 12)) * (0.6 + 0.4 * power)
            pts = self._jagged(cx, cy, cx + math.cos(a) * length, cy + math.sin(a) * length, 7, 3.5)
            life = rng.uniform(0.12, 0.22)
            self.arcs.append(Arc(pts, life, 2))
            bx, by = pts[rng.randrange(2, 6)]
            b = a + rng.choice((-1, 1)) * rng.uniform(0.5, 1.0)
            n = length * rng.uniform(0.25, 0.45)
            self.arcs.append(Arc(self._jagged(bx, by, bx + math.cos(b) * n, by + math.sin(b) * n, 4, 2), life, 1))
        for _ in range(config.SHOCK_BURST_SPARKS):
            a = rng.uniform(0, 2 * math.pi)
            v = rng.uniform(60, 160)
            self.sparks.append(Spark(cx, cy, math.cos(a) * v, math.sin(a) * v, rng.uniform(0.2, 0.45)))

    def _edge_point(self) -> tuple[float, float, float]:
        """몸 둘레(타원) 위의 한 점과 바깥 방향 각도."""
        w, h = self.body
        a = self.rng.uniform(0, 2 * math.pi)
        return w / 2 * math.cos(a), h / 2 + h / 2 * math.sin(a), a

    def _jagged(self, x0: float, y0: float, x1: float, y1: float, steps: int, wobble: float) -> list[tuple[int, int]]:
        """날카롭게 꺾이는 꺾은선 (마디마다 옆으로 번갈아 튐)."""
        rng = self.rng
        pts = []
        nx, ny = -(y1 - y0), x1 - x0
        n = math.hypot(nx, ny) or 1
        nx, ny = nx / n, ny / n
        sign = rng.choice((-1, 1))
        for k in range(steps + 1):
            t = k / steps
            off = 0 if k in (0, steps) else sign * rng.uniform(0.3, 1.0) * wobble
            sign = -sign
            pts.append((math.floor(x0 + (x1 - x0) * t + nx * off), math.floor(y0 + (y1 - y0) * t + ny * off)))
        return pts

    def _spawn_static(self, value: float) -> None:
        rng = self.rng
        x, y, a = self._edge_point()
        length = 3 + 10 * value * rng.uniform(0.5, 1.0)  # 찰수록 길게
        a += rng.uniform(-0.8, 0.8)
        x1, y1 = x + math.cos(a) * length, y + math.sin(a) * length
        self.arcs.append(Arc(self._jagged(x, y, x1, y1, max(2, round(length / 2.5)), 1.5),
                             rng.uniform(0.05, 0.11), 1 if value >= 0.7 and rng.random() < 0.4 else 0))
        if value >= 0.5 and rng.random() < value * 0.5:  # 많이 찼으면 불티도 톡톡
            self.sparks.append(Spark(x1, y1, math.cos(a) * 40, math.sin(a) * 40, rng.uniform(0.1, 0.2)))

    def _inner_point(self, spread: float = 0.35) -> tuple[float, float]:
        """몸 안쪽의 한 점 (가운데 둘레)."""
        w, h = self.body
        return self.rng.gauss(0, w * spread * 0.5), h * 0.5 + self.rng.gauss(0, h * spread * 0.5)

    def _spawn_inner(self, value: float) -> None:
        """몸 안에 갇힌 전기: 몸 안쪽 두 점 사이의 짧은 번개 (게이지가 찰수록 길고 굵게)."""
        rng = self.rng
        x0, y0 = self._inner_point()
        a = rng.uniform(0, 2 * math.pi)
        n = 3 + 7 * value
        self.arcs.append(Arc(self._jagged(x0, y0, x0 + math.cos(a) * n, y0 + math.sin(a) * n, 3, 1.5),
                             rng.uniform(0.05, 0.1), 1 if value >= 0.6 else 0))

    def _spawn_gather(self) -> None:
        """모임: 몸 둘레 바깥에서 가운데로 빨려 드는 번개 + 가운데로 날아드는 불티."""
        rng = self.rng
        w, h = self.body
        x0, y0, a = self._edge_point()
        x0, y0 = x0 + math.cos(a) * rng.uniform(3, 9), y0 + math.sin(a) * rng.uniform(3, 9)
        cx, cy = rng.gauss(0, 2), h * 0.55 + rng.gauss(0, 2)
        self.arcs.append(Arc(self._jagged(x0, y0, cx, cy, 6, 2.5), rng.uniform(0.04, 0.08), 1))
        v = rng.uniform(80, 140)
        d = math.hypot(cx - x0, cy - y0) or 1
        self.sparks.append(Spark(x0, y0, (cx - x0) / d * v, (cy - y0) / d * v + 60 * 0.12, d / v))

    def _spawn_zap(self, release: float = 1.0) -> None:
        """감전 방출: 몸 안쪽에서 시작해 몸 밖까지 뿜어져 나가는 번개 (+ 갈래·불티). 남은 전기가 적을수록 짧게."""
        rng = self.rng
        w, h = self.body
        x0, y0 = self._inner_point(0.25)
        _, _, a = self._edge_point()
        reach = (max(w, h) * 0.45 + rng.uniform(2, 10)) * (0.55 + 0.45 * release)
        x1, y1 = x0 + math.cos(a) * reach, y0 + math.sin(a) * reach
        main = self._jagged(x0, y0, x1, y1, 7, 3.0)
        life = rng.uniform(0.04, 0.09)
        self.arcs.append(Arc(main, life, 2 if release > 0.6 and rng.random() < 0.3 else 1))
        if rng.random() < 0.6:  # 갈래: 줄기 중간에서 짧게 뻗음
            bx, by = main[rng.randrange(2, len(main) - 2)]
            b = a + rng.choice((-1, 1)) * rng.uniform(0.4, 1.0)
            n = rng.uniform(4, 9)
            self.arcs.append(Arc(self._jagged(bx, by, bx + math.cos(b) * n, by + math.sin(b) * n, 3, 1.5), life))
        if rng.random() < 0.6:  # 끝에서 몸 밖으로 튀는 불티
            v = rng.uniform(60, 120)
            self.sparks.append(Spark(x1, y1, math.cos(a) * v, math.sin(a) * v, rng.uniform(0.15, 0.3)))

    def pixels(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        """그릴 점 (x, y, 색). 겹마다 바깥부터 그리도록 순서를 맞춘다 (흰 심이 맨 위)."""
        layer: dict[tuple[int, int], int] = {}

        def mark(x: int, y: int, k: int) -> None:
            if k < layer.get((x, y), 99):
                layer[(x, y)] = k

        for a in self.arcs:
            cooling = 1 if a.age > a.life * 0.6 else 0  # 끝무렵엔 흰 심이 식어 한 겹 바깥 색
            reach = LAYERS_BY_WEIGHT[a.weight]
            line = []
            for p, q in zip(a.points, a.points[1:]):
                line += _line(p, q)
            for x, y in line:
                for d, k in enumerate(reach):
                    for dx in range(-d, d + 1):
                        dy = d - abs(dx)
                        for yy in {dy, -dy}:
                            mark(x + dx, y + yy, min(3, k + cooling))
        for p in self.sparks:
            k = min(3, int(p.age / p.life * 3))
            mark(math.floor(p.x), math.floor(p.y), k)
            mark(math.floor(p.x - p.vx * 0.012), math.floor(p.y - p.vy * 0.012), min(3, k + 1))
        if self.flash > 0.0:  # 방전 섬광: 몸 가운데 작은 흰 빛이 번쩍 (하늘색 테만 두르고 바로 사그라듦)
            w, h = self.body
            t = 1 - self.flash / config.SHOCK_FLASH_TIME
            r = min(w, h) * (0.35 + 0.25 * t)
            cy = h * 0.55
            for y in range(math.floor(cy - r), math.ceil(cy + r) + 1):
                for x in range(math.floor(-r), math.ceil(r) + 1):
                    d = math.hypot(x + 0.5, y + 0.5 - cy) / r
                    if d < 1:
                        mark(x, y, 0 if d < 0.75 - t * 0.5 else 1)
        colours = config.SHOCK_LAYER_COLORS
        return [(x, y, colours[k]) for (x, y), k in sorted(layer.items(), key=lambda item: -item[1])]


def draw_static(renderer, static: StaticField, cx: float, bottom: float) -> None:
    """정전기·감전 번개를 화면에 그린다 (cx, bottom = 대상 발 밑 가운데 화면 좌표)."""
    s = config.RENDER_SCALE
    for x, y, colour in static.pixels():
        renderer.fill_rect(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, colour)


def draw_charge_glow(renderer, charge: Charge, path: str, frame: int, size: tuple[int, int], cx: float, bottom: float,
                     scale_y: float = 1.0) -> None:
    """몸이 파랗게 달아오른 그림 (모이는 동안 차오르고 폭발 뒤 식음). path = 파란 몸 그림 (아래 가운데가 (cx, bottom))."""
    glow = charge.glow
    if glow <= 0.0:
        return
    s = config.RENDER_SCALE
    flicker = 0.85 + 0.15 * math.sin(charge.gather_left * 90.0)
    w, h = size
    renderer.draw_sprite_frame(path, frame, w, h, cx, bottom, w * s, round(h * s * scale_y), opacity=glow * flicker)


def draw_charge_bar(renderer, value: float, cx: float, top: float, half_width: float) -> None:
    """파란 전기 게이지 막대 (게이지가 있을 때만). top = 막대 아래쪽 화면 y."""
    if value <= 0.0:
        return
    s = config.RENDER_SCALE
    renderer.fill_rect(cx - half_width, top, cx + half_width, top + 2 * s, config.COLOR_BAR_BACK)
    renderer.fill_rect(cx - half_width, top, cx - half_width + 2 * half_width * value, top + 2 * s,
                       config.COLOR_CHARGE_BAR)
