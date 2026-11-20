"""검 속성 입히기의 폭발과 털어내기 (2026-11-20 사용자: 이펙트가 부실함, 퀄리티가 떨어짐 / 마지막은 검을 한번 털어내는 느낌).

예전 판(enchant_burst.py)의 가는 고리·빛줄기 대신 속성마다 다른 입자 효과:
- 불: 칼 둘레에서 불덩이가 사방으로 확 피어올라 부풀며 식고(열을 쌓아 흰빛 → 노랑 → 주황 → 빨강), 불티가 멀리 튄다.
- 전기: 칼에서 사방으로 지그재그 번개가 여러 번 뻗었다 사라지고(갈래 포함), 스파크가 튄다.
- 어둠: 그림자가 사방으로 확 퍼졌다가 칼로 다시 빨려 들어간다 (반투명 그림자), 회색 빛 조각이 빨려 든다.
털어내기: 칼을 털어 내리는 순간 칼날을 따라 속성이 털어낸 쪽으로 흩뿌려진다 (불똥·스파크·검은 방울, 불·어둠은 떨어짐).
좌표는 원본 픽셀 격자(화면 / RENDER_SCALE, y 위로)의 절대 자리. 입히는 동안 주인공은 움직이지 않는다.
pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game.player.sword_lightning import _line

FIRE_HEAT = [  # 열 문턱 → 색 (높은 것부터)
    (2.0, (255, 248, 214)),
    (1.25, (255, 210, 84)),
    (0.7, (255, 142, 36)),
    (0.4, (232, 74, 28)),
    (0.2, (150, 36, 28)),
]
WHITE, CYAN, BLUE = (250, 254, 255), (140, 225, 255), (70, 150, 255)
PALE, GREY = (176, 172, 184), (70, 66, 76)
SHADE_STEPS = (0.3, 0.6, 0.9)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float  # 0 = 점 (불티·스파크·빛 조각)
    life: float
    kind: str  # fire / ember / spark / shadow / speck / drop
    age: float = 0.0
    gravity: float = 0.0
    pull: tuple[float, float] | None = None  # 어둠: 이 자리로 다시 빨려 듦
    px: float = 0.0  # 지난 자리 (꼬리)
    py: float = 0.0

    def __post_init__(self) -> None:
        self.px, self.py = self.x, self.y  # 처음 꼬리는 제자리 (안 그러면 화면 구석에서 선이 그어졌음)


@dataclass
class Bolt:
    points: list[tuple[float, float]]
    life: float
    age: float = 0.0


@dataclass
class EnchantFX:
    rng: random.Random = field(default_factory=random.Random)
    particles: list[Particle] = field(default_factory=list)
    bolts: list[Bolt] = field(default_factory=list)
    _bolt_source: tuple[float, float, float] | None = None  # 전기 폭발: (x, y, 남은 시간) 동안 번개를 계속 뻗음

    @property
    def active(self) -> bool:
        return bool(self.particles or self.bolts or self._bolt_source)

    # ----- 만들기 -----
    def burst(self, element: str, blade: tuple[tuple[float, float], tuple[float, float]]) -> None:
        """속성이 다 차오른 순간의 폭발. blade = (손, 칼끝) 원본 픽셀 좌표."""
        (hx, hy), (tx, ty) = blade
        rng = self.rng

        def on_blade() -> tuple[float, float]:
            t = rng.uniform(0.2, 1.0)
            return hx + (tx - hx) * t, hy + (ty - hy) * t

        cx, cy = hx + (tx - hx) * 0.6, hy + (ty - hy) * 0.6
        if element == "fire":
            # 불덩이가 칼에서 사방으로 확 퍼지며 피어오름 (가운데 한 덩어리로 뭉치지 않게 작고 빠르게)
            for _ in range(40):
                x, y = on_blade()
                a, sp = rng.uniform(0, 2 * math.pi), rng.uniform(55, 110)
                self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp + 10, rng.uniform(1.6, 2.8),
                                               rng.uniform(0.22, 0.4), "fire", gravity=40))
            for _ in range(30):
                x, y = on_blade()
                a, sp = rng.uniform(0, 2 * math.pi), rng.uniform(60, 130)
                self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, 0, rng.uniform(0.25, 0.5),
                                               "ember", gravity=50))
        elif element == "lightning":
            self._bolt_source = (cx, cy, 0.3)
            for _ in range(24):
                x, y = on_blade()
                a, sp = rng.uniform(0, 2 * math.pi), rng.uniform(70, 150)
                self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, 0, rng.uniform(0.15, 0.35),
                                               "spark"))
        elif element == "dark":
            for _ in range(40):
                x, y = on_blade()
                a, sp = rng.uniform(0, 2 * math.pi), rng.uniform(40, 90)
                self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, rng.uniform(2.5, 4.2),
                                               rng.uniform(0.45, 0.6), "shadow", pull=(cx, cy)))
            for _ in range(14):
                a, d = rng.uniform(0, 2 * math.pi), rng.uniform(16, 24)
                self.particles.append(Particle(cx + math.cos(a) * d, cy + math.sin(a) * d, 0, 0, 0,
                                               rng.uniform(0.35, 0.55), "speck", pull=(cx, cy)))

    def flick(self, element: str, blade: tuple[tuple[float, float], tuple[float, float]],
              direction: tuple[float, float]) -> None:
        """칼을 털어 내리는 순간 칼날에서 속성이 direction 쪽으로 흩뿌려진다."""
        (hx, hy), (tx, ty) = blade
        dx, dy = direction
        rng = self.rng
        for _ in range(26):
            t = rng.uniform(0.25, 1.0)
            x, y = hx + (tx - hx) * t, hy + (ty - hy) * t
            sp = rng.uniform(50, 120) * (0.6 + 0.6 * t)  # 칼끝 쪽이 더 멀리
            vx, vy = dx * sp + rng.uniform(-15, 15), dy * sp + rng.uniform(-15, 15)
            if element == "fire":
                self.particles.append(Particle(x, y, vx, vy, rng.choice((0, 0, 1.6)), rng.uniform(0.25, 0.5),
                                               "ember", gravity=-140))
            elif element == "lightning":
                self.particles.append(Particle(x, y, vx * 1.3, vy * 1.3, 0, rng.uniform(0.12, 0.28), "spark"))
            elif element == "dark":
                self.particles.append(Particle(x, y, vx, vy, rng.uniform(1.2, 2.2), rng.uniform(0.3, 0.55), "drop",
                                               gravity=-160))
        if element == "lightning":  # 털어낸 쪽으로 짧은 번개 몇 줄기
            for _ in range(3):
                t = rng.uniform(0.5, 1.0)
                x, y = hx + (tx - hx) * t, hy + (ty - hy) * t
                reach = rng.uniform(8, 14)
                end = (x + dx * reach + rng.uniform(-3, 3), y + dy * reach + rng.uniform(-3, 3))
                self.bolts.append(Bolt(self._jagged((x, y), end, 0.45, 3), rng.uniform(0.06, 0.12)))

    def _jagged(self, a: tuple[float, float], b: tuple[float, float], rough: float, depth: int):
        pts = [a, b]
        for _ in range(depth):
            new = [pts[0]]
            for p, q in zip(pts, pts[1:]):
                mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                seg = math.hypot(q[0] - p[0], q[1] - p[1])
                nx, ny = -(q[1] - p[1]) / (seg or 1), (q[0] - p[0]) / (seg or 1)
                off = self.rng.uniform(-1, 1) * seg * rough
                new += [(mx + nx * off, my + ny * off), q]
            pts = new
        return pts

    # ----- 진행 -----
    def update(self, dt: float) -> None:
        for p in self.particles:
            p.px, p.py = p.x, p.y
            p.age += dt
            if p.pull is not None and p.age > p.life * 0.35:  # 어둠: 퍼졌다가 다시 빨려 듦
                ax, ay = p.pull[0] - p.x, p.pull[1] - p.y
                p.vx += ax * 40 * dt
                p.vy += ay * 40 * dt
                p.vx *= 0.86
                p.vy *= 0.86
            else:
                p.vx *= 0.9 if p.kind in ("fire", "shadow") else 0.96
                p.vy *= 0.9 if p.kind in ("fire", "shadow") else 0.96
            p.vy += p.gravity * dt  # y 위로: 양수면 떠오름(불), 음수면 떨어짐(털어낸 불똥·검은 방울)
            p.x += p.vx * dt
            p.y += p.vy * dt
        self.particles = [p for p in self.particles if p.age < p.life]
        for b in self.bolts:
            b.age += dt
        self.bolts = [b for b in self.bolts if b.age < b.life]
        if self._bolt_source is not None:
            x, y, left = self._bolt_source
            left -= dt
            self._bolt_source = (x, y, left) if left > 0 else None
            if self.rng.random() < dt * 45:  # 번개를 불규칙하게 계속 뻗음
                a, reach = self.rng.uniform(0, 2 * math.pi), self.rng.uniform(12, 24)
                end = (x + math.cos(a) * reach, y + math.sin(a) * reach)
                pts = self._jagged((x, y), end, 0.4, 3)
                self.bolts.append(Bolt(pts, self.rng.uniform(0.05, 0.1)))
                if self.rng.random() < 0.6:  # 갈래
                    m = pts[len(pts) // 2]
                    b = a + self.rng.choice((-1, 1)) * self.rng.uniform(0.5, 1.0)
                    tip = (m[0] + math.cos(b) * reach * 0.4, m[1] + math.sin(b) * reach * 0.4)
                    self.bolts.append(Bolt(self._jagged(m, tip, 0.4, 2), self.rng.uniform(0.04, 0.08)))

    # ----- 그리기용 점 -----
    def pixels(self) -> list[tuple]:
        """(x, y, 색) 불투명 점, (x, y, None, 짙기) 반투명 그림자. 그리는 순서대로."""
        out: list[tuple] = []
        heat: dict[tuple[int, int], float] = {}
        shade: dict[tuple[int, int], float] = {}

        def disc(cx: float, cy: float, r: float, s: float, into: dict, mode: str) -> None:
            for y in range(math.floor(cy - r), math.floor(cy + r) + 1):
                for x in range(math.floor(cx - r), math.floor(cx + r) + 1):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d < r:
                        a = s * (1 - d / r) ** 0.7
                        if mode == "sum":
                            into[(x, y)] = into.get((x, y), 0.0) + a
                        else:
                            into[(x, y)] = 1 - (1 - into.get((x, y), 0.0)) * (1 - min(1.0, a))

        for p in self.particles:
            life = p.age / p.life
            if p.kind == "fire":
                disc(p.x, p.y, p.radius * (1 + 0.5 * life), 1.15 * (1 - life) ** 0.8, heat, "sum")
            elif p.kind == "shadow":
                disc(p.x, p.y, p.radius * (1 - 0.4 * life), 0.95 * (1 - life ** 2), shade, "over")
            elif p.kind == "drop" and p.radius:
                disc(p.x, p.y, p.radius, 0.9 * (1 - life), shade, "over")
        for (x, y), h in heat.items():
            for limit, colour in FIRE_HEAT:
                if h >= limit:
                    out.append((x, y, colour))
                    break
        for (x, y), a in shade.items():
            level = max((s for s in SHADE_STEPS if s <= a), default=None)
            if level is not None:
                out.append((x, y, None, level))
        for b in self.bolts:
            line: list[tuple[int, int]] = []
            for p, q in zip(b.points, b.points[1:]):
                seg = _line((math.floor(p[0]), math.floor(p[1])), (math.floor(q[0]), math.floor(q[1])))
                line += seg if not line else seg[1:]
            for x, y in line:
                for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if self.rng.random() < 0.4:
                        out.append((x + ex, y + ey, BLUE))
            out += [(x, y, WHITE) for x, y in line]
        for p in self.particles:  # 점: 꼬리 + 머리
            life = p.age / p.life
            if p.kind == "ember":
                head = (255, 230, 140) if life < 0.4 else (255, 150, 40) if life < 0.75 else (190, 60, 30)
                if p.radius:
                    disc_pts = [(math.floor(p.x + ox), math.floor(p.y + oy)) for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1))]
                    out += [(x, y, head) for x, y in disc_pts]
                else:
                    out.append((math.floor(p.px), math.floor(p.py), (200, 80, 30)))
                    out.append((math.floor(p.x), math.floor(p.y), head))
            elif p.kind == "spark":
                for x, y in _line((math.floor(p.px), math.floor(p.py)), (math.floor(p.x), math.floor(p.y)))[:-1]:
                    out.append((x, y, BLUE if life > 0.5 else CYAN))
                out.append((math.floor(p.x), math.floor(p.y), WHITE if life < 0.6 else CYAN))
            elif p.kind == "speck":
                out.append((math.floor(p.px), math.floor(p.py), GREY))
                out.append((math.floor(p.x), math.floor(p.y), PALE))
        return out
