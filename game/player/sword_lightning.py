"""검 전기 이펙트를 게임이 도는 동안 계산해 만든다 (2026-11-20 사용자: 미리 그린 24장 반복은 번개가 일정해 보임,
알고리즘으로 진짜 번개 스파크처럼).

미리 그린 시트 대신 매 순간 무작위로:
- 아크: 칼날 한쪽 가장자리의 두 점을 잇는 번개. 가운데를 양옆으로 밀어내는 방식(midpoint displacement)으로 지그재그로 꺾이고
  칼날 바깥으로 튀어나갔다 돌아온다. 0.04~0.12초만 보이고 사라진다. 절반쯤은 중간에서 짧은 갈래가 갈라진다.
- 방전: 불규칙한 간격(0.2~0.9초)으로 칼끝(입히는 중이면 번지는 앞머리)에서 크게 뻗는 번개 + 스파크 여러 개 + 칼날 번쩍.
- 스파크: 아크 끝에서 튀어 나가 속도가 줄며 날아가다 식는 점 (꼬리 1 픽셀).
좌표는 칼 기준: along = 칼날 위치 비율(0 = 칼날 시작, 1 = 칼끝), off = 칼날 가장자리에서 바깥으로 떨어진 픽셀(부호 = 칼의 어느 쪽).
그릴 때 칼마다 다른 크기(보통 칼, 짧게 그린 칼, 찌르기용 큰 칼)에 맞춰 원본 픽셀 격자로 옮겨 1 픽셀 선으로 찍는다.

pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

NOMINAL_LENGTH = 20.0  # 아크 모양을 만들 때 쓰는 칼날 길이 (픽셀). 실제 칼에 맞춰 늘이고 줄임
MAX_OFF = 4.5  # 칼날 가장자리에서 벗어나는 최대 거리 (픽셀)
MAX_ARCS = 3  # 한꺼번에 보이는 아크 수
OUTLINE_CHANCE = 0.35  # 흰 심 옆 파란 픽셀을 찍을 확률 (전부 찍으면 굵고 뭉개짐)

WHITE = (250, 254, 255)
CYAN = (140, 225, 255)
BLUE = (70, 150, 255)
DEEP = (45, 85, 220)


@dataclass
class Bolt:
    points: list[tuple[float, float]]  # (along 비율, off 픽셀)
    life: float
    core: tuple[int, int, int] = WHITE
    age: float = 0.0


@dataclass
class Spark:
    along: float
    off: float
    v_along: float  # 비율/초
    v_off: float  # 픽셀/초
    life: float
    age: float = 0.0
    trail: tuple[float, float] = (0.0, 0.0)


@dataclass
class BladeShape:
    """그릴 칼의 모양: 손에서 칼날 시작·칼끝까지 거리(원본 픽셀), 칼날 반폭(시작, 끝)."""
    start: float
    end: float
    half_start: float
    half_end: float

    def half(self, along: float) -> float:
        return self.half_start + (self.half_end - self.half_start) * along


SWORD_SHAPE = BladeShape(5.0, 24.0, 2.5, 1.5)  # weapons/<무기>.png: 손(한가운데)에서 가드 앞 5, 칼끝 24, 폭 5


@dataclass
class LightningField:
    rng: random.Random = field(default_factory=random.Random)
    bolts: list[Bolt] = field(default_factory=list)
    sparks: list[Spark] = field(default_factory=list)
    flash: float = 0.0  # 남은 번쩍임 시간
    glow_seed: int = 0
    _arc_timer: float = 0.0
    _discharge_timer: float = 0.3

    def update(self, dt: float, reach: float = 1.0) -> None:
        """dt 초 진행. reach = 전기가 번진 정도 (입히는 중이면 0~1, 그 밖에는 1)."""
        for b in self.bolts:
            b.age += dt
        self.bolts = [b for b in self.bolts if b.age < b.life]
        for s in self.sparks:
            s.trail = (s.along, s.off)
            s.age += dt
            s.along += s.v_along * dt
            s.off += s.v_off * dt * (1 if s.off >= 0 else -1)
            s.v_along *= 0.9
            s.v_off *= 0.88
        self.sparks = [s for s in self.sparks if s.age < s.life]
        self.flash = max(0.0, self.flash - dt)
        self.glow_seed = self.rng.randrange(1 << 30)
        if reach <= 0.0:
            return
        self._arc_timer -= dt
        while self._arc_timer <= 0.0:  # 아크가 불규칙하게 (평균 초당 약 20개)
            self._spawn_arc(reach)
            self._arc_timer += self.rng.expovariate(20.0)
        self._discharge_timer -= dt
        if self._discharge_timer <= 0.0 or reach < 1.0 and self.rng.random() < dt * 6:
            self._discharge(reach)
            self._discharge_timer = self.rng.uniform(0.2, 0.9)

    # ----- 만들기 -----
    def _jagged(self, a: tuple[float, float], b: tuple[float, float], rough: float, depth: int,
                outward: bool) -> list[tuple[float, float]]:
        """(along 픽셀, off) 두 점 사이를 날카롭게 꺾은 꼭짓점들. outward 면 칼날 바깥으로 치우침."""
        pts = [a, b]
        side = 1 if (a[1] + b[1]) >= 0 else -1
        for _ in range(depth):
            new = [pts[0]]
            for p, q in zip(pts, pts[1:]):
                mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                seg = math.hypot(q[0] - p[0], q[1] - p[1])
                # 양쪽으로 지그재그 (바깥으로 살짝 치우침). 한쪽으로만 밀면 납작한 고리처럼 보였음
                off = (self.rng.uniform(-1, 1) + (0.35 if outward else 0.0)) * seg * rough  # 아래 ny 가 이미 side 쪽
                # 선분에 수직으로 밀기 (칼 기준 좌표라 거의 off 방향)
                nx, ny = -(q[1] - p[1]) / (seg or 1), (q[0] - p[0]) / (seg or 1)
                if ny * side < 0:
                    nx, ny = -nx, -ny
                m_off = my + ny * off
                if abs(m_off) > MAX_OFF:  # 너무 멀면 되접어 (평평하게 잘리지 않게)
                    m_off = (2 * MAX_OFF - abs(m_off)) * (1 if m_off > 0 else -1)
                if m_off * side < 0.3:
                    m_off = 0.3 * side  # 칼날 안으로 파고들지 않게
                new += [(mx + nx * off, m_off), q]
            pts = new
        return pts

    def _to_ratio(self, pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(x / NOMINAL_LENGTH, y) for x, y in pts]

    def _spawn_arc(self, reach: float) -> None:
        rng = self.rng
        if sum(1 for b in self.bolts if b.core == WHITE) >= MAX_ARCS:
            return  # 한꺼번에 너무 많으면 엉킨 낙서처럼 보임
        side = rng.choice((-1, 1))
        top = reach * NOMINAL_LENGTH
        span = rng.uniform(4, 9)
        if top < 3:
            return
        x0 = rng.uniform(0.5, max(0.6, top - min(span, top * 0.7)))
        x1 = min(top, x0 + span)
        a, b = (x0, side * rng.uniform(0.3, 1.0)), (x1, side * rng.uniform(0.3, 1.0))
        pts = self._jagged(a, b, 0.6, rng.choice((2, 3)), True)
        self.bolts.append(Bolt(self._to_ratio(pts), rng.uniform(0.03, 0.09)))
        if rng.random() < 0.4 and len(pts) > 3:  # 갈래
            m = pts[len(pts) // 2]
            tip = (m[0] + rng.uniform(-2, 3), side * min(MAX_OFF + 1, abs(m[1]) + rng.uniform(2, 4)))
            self.bolts.append(Bolt(self._to_ratio(self._jagged(m, tip, 0.35, 2, False)), rng.uniform(0.03, 0.08), CYAN))
        for end in (a, b):
            if rng.random() < 0.35:
                self._spark(end[0] / NOMINAL_LENGTH, end[1])

    def _discharge(self, reach: float) -> None:
        rng = self.rng
        side = rng.choice((-1, 1))
        x = max(0.5, reach * NOMINAL_LENGTH - rng.uniform(0, 3))
        reach_px = rng.uniform(5, 9)
        start = (x, side * 0.5)
        tip = (x + rng.uniform(-2, 4), side * (reach_px + 1))
        pts = self._jagged(start, tip, 0.35, 3, False)
        self.bolts.append(Bolt(self._to_ratio(pts), rng.uniform(0.06, 0.12)))
        for _ in range(rng.randint(3, 6)):
            self._spark(tip[0] / NOMINAL_LENGTH, tip[1], strong=True)
        self.flash = 0.07

    def _spark(self, along: float, off: float, strong: bool = False) -> None:
        rng = self.rng
        sign = 1 if off >= 0 else -1
        speed = rng.uniform(25, 60) if strong else rng.uniform(15, 40)
        self.sparks.append(Spark(along, off if off else sign * 0.5, rng.uniform(-0.6, 0.9), speed,
                                 rng.uniform(0.12, 0.3) if strong else rng.uniform(0.08, 0.2)))

    # ----- 그리기용 픽셀 -----
    def pixels(self, hand: tuple[float, float], direction: tuple[float, float], shape: BladeShape,
               along_scale: float = 1.0, reach: float = 1.0) -> list[tuple[int, int, tuple[int, int, int]]]:
        """원본 픽셀 격자(화면 좌표 / RENDER_SCALE, y 위로)에 찍을 (x, y, 색) 목록. 그리는 순서대로 (뒤 → 앞).

        hand = 손 자리, direction = 칼끝 방향 단위 벡터, shape = 칼 모양, along_scale = 원근으로 짧게 그린 칼의 비율.
        """
        dx, dy = direction
        nx, ny = -dy, dx

        def place(along: float, off: float) -> tuple[float, float]:
            dist = (shape.start + (shape.end - shape.start) * along) * along_scale
            edge = shape.half(min(1.0, max(0.0, along)))
            o = (edge + abs(off)) * (1 if off >= 0 else -1)
            return hand[0] + dx * dist + nx * o, hand[1] + dy * dist + ny * o

        out: list[tuple[int, int, tuple[int, int, int]]] = []
        glow = random.Random(self.glow_seed)
        steps = max(2, int((shape.end - shape.start) * along_scale))
        for k in range(steps + 1):  # 칼날 둘레 얇은 빛 (깜빡임)
            a = k / steps
            if a > reach:
                break
            for side in (-1, 1):
                if glow.random() < (0.95 if self.flash > 0 else 0.5):
                    x, y = place(a, side * 0.6)
                    out.append((math.floor(x), math.floor(y), CYAN if self.flash > 0 else BLUE))
        cores = []
        for bolt in self.bolts:
            pts = [place(a, o) for a, o in bolt.points]
            line = []
            for p, q in zip(pts, pts[1:]):
                seg = _line((math.floor(p[0]), math.floor(p[1])), (math.floor(q[0]), math.floor(q[1])))
                line += seg if not line else seg[1:]
            for x, y in line:  # 바로 옆 1 픽셀 파랑을 듬성듬성
                for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if glow.random() < OUTLINE_CHANCE:
                        out.append((x + ex, y + ey, BLUE))
            cores.append((line, bolt.core))
        for line, core in cores:
            out += [(x, y, core) for x, y in line]
        for s in self.sparks:
            hot = s.age < s.life * 0.5
            tx, ty = place(*s.trail)
            out.append((math.floor(tx), math.floor(ty), BLUE if hot else DEEP))
            x, y = place(s.along, s.off)
            out.append((math.floor(x), math.floor(y), WHITE if hot else CYAN))
        return out


def _line(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    """두 점 사이 1 픽셀 선 (Bresenham)."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
