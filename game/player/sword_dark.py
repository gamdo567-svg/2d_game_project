"""검 어둠 이펙트를 게임이 도는 동안 계산해 만든다 (2026-11-20 사용자: 모든 걸 빨아들이는 블랙홀 같은 어둠).

전기(sword_lightning.py)와 같은 칼 기준 좌표·그리기 방식:
- 연기: 칼 둘레 3~8 픽셀 밖에서 검보라 연기 덩어리가 생겨 칼날 쪽으로 끌려가며(가까울수록 세게) 옆으로 휘돌고(소용돌이),
  가까워질수록 작고 검어지다가 칼날에 닿으면 빨려 들어가 사라진다. 덩어리끼리 붙은 바깥 윤곽만 보라 테두리.
- 빛 알갱이: 더 멀리(6~11 픽셀)서 옅은 보라 점이 빠르게 끌려 들어가며 긴 꼬리(지난 세 자리)를 남긴다
  (칼로 모여드는 줄무늬, 빛까지 빨아들이는 느낌). 처음 판은 연기가 많아 몸을 덮는 보라 덩어리처럼 보여 연기를 줄이고 줄무늬를 늘림.
- 칼날: 새까만 기운이 칼날을 감싸고 두께가 출렁이며, 바깥 픽셀은 군데군데 보라.
- 맥동: 0.6~1.4초 무작위 간격으로 둘레 멀리서 알갱이가 한꺼번에 생겨 빨려 들고 칼날 기운이 잠깐 두꺼워진다.
pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game.player.sword_lightning import NOMINAL_LENGTH, BladeShape, _line

BLACK = (12, 6, 18)
SHADOW = (30, 14, 44)
DUSK = (56, 24, 84)
VIOLET = (120, 60, 190)
PALE = (196, 150, 255)


@dataclass
class Mote:
    x: float  # 칼날 위치 (픽셀, 0 = 칼날 시작, NOMINAL_LENGTH = 칼끝)
    off: float  # 가장자리에서 떨어진 거리 (부호 = 칼의 어느 쪽)
    vx: float
    voff: float
    radius: float  # 0 이면 빛 알갱이 (점 + 꼬리)
    life: float
    age: float = 0.0
    trail: list[tuple[float, float]] = field(default_factory=list)  # 지난 자리들 (최근 것이 앞)


@dataclass
class DarkField:
    rng: random.Random = field(default_factory=random.Random)
    motes: list[Mote] = field(default_factory=list)
    pulse: float = 0.0  # 남은 맥동 시간
    phase: float = 0.0
    glow_seed: int = 0
    _smoke_timer: float = 0.0
    _speck_timer: float = 0.0
    _pulse_timer: float = 0.8

    def update(self, dt: float, reach: float = 1.0) -> None:
        self.phase += dt
        self.pulse = max(0.0, self.pulse - dt)
        self.glow_seed = self.rng.randrange(1 << 30)
        alive = []
        for m in self.motes:
            m.trail = [(m.x, m.off)] + m.trail[:2]
            m.age += dt
            side = 1 if m.off >= 0 else -1
            dist = max(0.4, abs(m.off))
            pull = (40 if m.radius else 90) * (1 + 3 / dist)  # 가까울수록 세게 (블랙홀)
            m.voff -= side * pull * dt
            m.vx += side * 18 * dt  # 한쪽으로 휘돌기
            m.voff *= 0.9
            m.vx *= 0.94
            m.x += m.vx * dt
            m.off += m.voff * dt
            if m.off * side > 0.5 and m.age < m.life:  # 칼날에 닿으면 빨려 들어가 사라짐
                alive.append(m)
        self.motes = alive
        if reach <= 0.0:
            return
        top = reach * NOMINAL_LENGTH
        self._smoke_timer -= dt
        while self._smoke_timer <= 0.0:
            self._spawn(top, smoke=True)
            self._smoke_timer += self.rng.expovariate(22.0)
        self._speck_timer -= dt
        while self._speck_timer <= 0.0:
            self._spawn(top, smoke=False)
            self._speck_timer += self.rng.expovariate(40.0)
        self._pulse_timer -= dt
        if self._pulse_timer <= 0.0:
            for _ in range(12):
                self._spawn(top, smoke=False, far=True)
            self.pulse = 0.18
            self._pulse_timer = self.rng.uniform(0.6, 1.4)

    def _spawn(self, top: float, smoke: bool, far: bool = False) -> None:
        rng = self.rng
        side = rng.choice((-1, 1))
        x = rng.uniform(-1, top + (3 if smoke else 1))
        if smoke:
            off = rng.uniform(3, 8)
            self.motes.append(Mote(x, side * off, rng.uniform(-6, 6), 0.0, rng.uniform(0.8, 1.6), rng.uniform(0.4, 0.8)))
        else:
            off = rng.uniform(10, 13) if far else rng.uniform(6, 11)
            self.motes.append(Mote(x, side * off, rng.uniform(-10, 10), 0.0, 0.0, rng.uniform(0.3, 0.7)))

    def pixels(self, hand: tuple[float, float], direction: tuple[float, float], shape: BladeShape,
               along_scale: float = 1.0, reach: float = 1.0) -> list[tuple[int, int, tuple[int, int, int]]]:
        """원본 픽셀 격자(y 위로)에 찍을 (x, y, 색), 그리는 순서대로."""
        dx, dy = direction
        nx, ny = -dy, dx

        def place(x: float, off: float) -> tuple[float, float]:
            along = x / NOMINAL_LENGTH
            dist = (shape.start + (shape.end - shape.start) * along) * along_scale
            edge = shape.half(min(1.0, max(0.0, along)))
            o = (edge + abs(off)) * (1 if off >= 0 else -1)
            return hand[0] + dx * dist + nx * o, hand[1] + dy * dist + ny * o

        out: list[tuple[int, int, tuple[int, int, int]]] = []
        smoke = [m for m in self.motes if m.radius]
        discs = []
        for m in smoke:
            cx, cy = place(m.x, m.off)
            r = max(0.6, m.radius * min(1.0, abs(m.off) / 4))  # 가까워질수록 작게
            near = abs(m.off) < 2.5
            discs.append((cx, cy, r, BLACK if near else SHADOW if abs(m.off) < 5 else DUSK))
        for cx, cy, r, _ in discs:  # 덩어리들 바깥 윤곽만 보라 (먼저 넓게 칠하고 안을 덮음)
            out += [(x, y, VIOLET) for x, y in _disc(cx, cy, r + 1)]
        for cx, cy, r, c in discs:
            out += [(x, y, c) for x, y in _disc(cx, cy, r)]
        # 칼날을 감싸는 새까만 기운 (두께가 출렁임, 맥동 때 두꺼움)
        glow = random.Random(self.glow_seed)
        steps = max(2, int((shape.end - shape.start) * along_scale))
        for k in range(steps + 1):
            a = k / steps
            if a > reach:
                break
            for side in (-1, 1):
                thick = 1.0 + 0.8 * (0.5 + 0.5 * math.sin(self.phase * 7 + k * 0.9 + side)) + (1.2 if self.pulse else 0)
                for t in range(int(thick) + 1):
                    x, y = place(a * NOMINAL_LENGTH, side * (0.3 + t))
                    out.append((math.floor(x), math.floor(y), BLACK))
                if glow.random() < 0.45:
                    x, y = place(a * NOMINAL_LENGTH, side * (1.3 + thick))
                    out.append((math.floor(x), math.floor(y), VIOLET))
        for m in self.motes:  # 빨려 드는 빛 알갱이: 꼬리를 길게 끌어 칼로 모여드는 줄무늬처럼
            if m.radius:
                continue
            pts = [place(m.x, m.off)] + [place(*p) for p in m.trail]
            for (ax, ay), (bx, by), c in zip(pts[1:], pts, (VIOLET, DUSK, DUSK)):
                for x, y in _line((math.floor(ax), math.floor(ay)), (math.floor(bx), math.floor(by)))[:-1]:
                    out.append((x, y, c))
            x, y = pts[0]
            out.append((math.floor(x), math.floor(y), PALE))
        return out


def _disc(cx: float, cy: float, r: float) -> list[tuple[int, int]]:
    out = []
    for y in range(math.floor(cy - r), math.floor(cy + r) + 1):
        for x in range(math.floor(cx - r), math.floor(cx + r) + 1):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                out.append((x, y))
    return out
