"""검 어둠 이펙트를 게임이 도는 동안 계산해 만든다 (2026-11-20 사용자: 모든 걸 빨아들이는 블랙홀 같은 어둠).

2차 (같은 날 사용자: 보라가 많아 독 같음 → 검정, 이어서 "좀 더 그림자 같고 어둠 같은 느낌"):
불투명한 검은 덩어리 대신 **반투명한 그림자**로 그린다. 픽셀마다 어둠의 짙기(0~1)를 쌓아 단계로 끊어
(픽셀풍) 검은 반투명 네모로 찍으므로, 짙은 곳은 새까맣고 가장자리는 뒤가 비치며 바닥·몸을 어둡게 덮는다.
- 칼 그림자: 칼날 자체를 어둠이 덮어(반쯤 비침) 칼이 그림자에 먹힌 것처럼, 가장자리 둘레는 더 짙게.
- 그림자 불꽃: 칼날 가장자리에서 검은 불꽃이 바깥·칼끝 쪽으로 일렁이며 피었다 옅어진다.
- 빨려 드는 어둠: 칼 둘레 3~8 픽셀 밖에서 옅은 그림자 덩어리가 생겨 칼날 쪽으로 끌려가며(가까울수록 세게) 휘돌고,
  다가올수록 짙어지다가 칼날에 닿으면 빨려 들어가 사라진다.
- 빛 조각: 멀리서 옅은 회색 점이 꼬리를 끌며 빨려 든다 (빛까지 삼키는 느낌, 몇 개만).
- 맥동: 0.6~1.4초 무작위 간격으로 멀리서 한꺼번에 빨려 들고, 칼 둘레 어둠이 잠깐 짙고 넓어진다.
좌표는 전기(sword_lightning.py)와 같은 칼 기준. pico2d 를 쓰지 않는 순수 로직이다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game.player.sword_lightning import NOMINAL_LENGTH, BladeShape, _line

PALE = (176, 172, 184)  # 빨려 드는 빛 조각 머리
GREY = (70, 66, 76)  # 그 꼬리
SHADE_STEPS = (0.2, 0.4, 0.6, 0.8, 0.94)  # 어둠 짙기를 이 단계로 끊어 픽셀풍으로


@dataclass
class Mote:
    x: float  # 칼날 위치 (픽셀, 0 = 칼날 시작, NOMINAL_LENGTH = 칼끝)
    off: float  # 가장자리에서 떨어진 거리 (부호 = 칼의 어느 쪽)
    vx: float
    voff: float
    radius: float  # 0 이면 빛 조각 (점 + 꼬리)
    life: float
    kind: str = "inflow"  # inflow = 빨려 드는 어둠, flame = 그림자 불꽃, speck = 빛 조각
    age: float = 0.0
    trail: list[tuple[float, float]] = field(default_factory=list)  # 지난 자리들 (최근 것이 앞)


@dataclass
class DarkField:
    rng: random.Random = field(default_factory=random.Random)
    motes: list[Mote] = field(default_factory=list)
    pulse: float = 0.0  # 남은 맥동 시간
    phase: float = 0.0
    _inflow_timer: float = 0.0
    _flame_timer: float = 0.0
    _speck_timer: float = 0.0
    _pulse_timer: float = 0.8

    def update(self, dt: float, reach: float = 1.0) -> None:
        self.phase += dt
        self.pulse = max(0.0, self.pulse - dt)
        alive = []
        for m in self.motes:
            m.trail = [(m.x, m.off)] + m.trail[:2]
            m.age += dt
            side = 1 if m.off >= 0 else -1
            if m.kind == "flame":  # 그림자 불꽃: 바깥·칼끝 쪽으로 일렁이며 줄어듦
                m.x += m.vx * dt
                m.off += m.voff * dt
                m.voff *= 0.92
                if m.age < m.life:
                    alive.append(m)
                continue
            dist = max(0.4, abs(m.off))
            pull = (40 if m.kind == "inflow" else 90) * (1 + 3 / dist)  # 가까울수록 세게 (블랙홀)
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
        self._inflow_timer = self._emit(self._inflow_timer, dt, 26.0, lambda: self._spawn_inflow(top))
        self._flame_timer = self._emit(self._flame_timer, dt, 55.0, lambda: self._spawn_flame(top))
        self._speck_timer = self._emit(self._speck_timer, dt, 10.0, lambda: self._spawn_speck(top))
        self._pulse_timer -= dt
        if self._pulse_timer <= 0.0:
            for _ in range(8):
                self._spawn_inflow(top, far=True)
            for _ in range(4):
                self._spawn_speck(top, far=True)
            self.pulse = 0.2
            self._pulse_timer = self.rng.uniform(0.6, 1.4)

    def _emit(self, timer: float, dt: float, rate: float, spawn) -> float:
        timer -= dt
        while timer <= 0.0:
            spawn()
            timer += self.rng.expovariate(rate)
        return timer

    def _spawn_inflow(self, top: float, far: bool = False) -> None:
        rng = self.rng
        side = rng.choice((-1, 1))
        off = rng.uniform(8, 11) if far else rng.uniform(3, 8)
        self.motes.append(Mote(rng.uniform(-1, top + 3), side * off, rng.uniform(-6, 6), 0.0,
                               rng.uniform(1.4, 2.6), rng.uniform(0.4, 0.9)))

    def _spawn_flame(self, top: float) -> None:
        rng = self.rng
        side = rng.choice((-1, 1))
        self.motes.append(Mote(rng.uniform(0, top), side * rng.uniform(0.2, 1.0), rng.uniform(3, 10),
                               side * rng.uniform(4, 10), rng.uniform(2.0, 3.2), rng.uniform(0.25, 0.5), "flame"))

    def _spawn_speck(self, top: float, far: bool = False) -> None:
        rng = self.rng
        side = rng.choice((-1, 1))
        off = rng.uniform(10, 13) if far else rng.uniform(6, 11)
        self.motes.append(Mote(rng.uniform(-1, top + 1), side * off, rng.uniform(-10, 10), 0.0, 0.0,
                               rng.uniform(0.3, 0.7), "speck"))

    def pixels(self, hand: tuple[float, float], direction: tuple[float, float], shape: BladeShape,
               along_scale: float = 1.0, reach: float = 1.0) -> list[tuple]:
        """원본 픽셀 격자(y 위로)에 찍을 것들, 그리는 순서대로.
        (x, y, None, 짙기) = 검은 반투명 그림자, (x, y, 색) = 불투명 점 (빛 조각)."""
        dx, dy = direction
        nx, ny = -dy, dx

        def place(x: float, off: float, inside: bool = False) -> tuple[float, float]:
            along = x / NOMINAL_LENGTH
            dist = (shape.start + (shape.end - shape.start) * along) * along_scale
            edge = 0.0 if inside else shape.half(min(1.0, max(0.0, along)))
            o = (edge + abs(off)) * (1 if off >= 0 else -1)
            return hand[0] + dx * dist + nx * o, hand[1] + dy * dist + ny * o

        shade: dict[tuple[int, int], float] = {}

        def add(px: int, py: int, a: float) -> None:
            shade[(px, py)] = 1 - (1 - shade.get((px, py), 0.0)) * (1 - min(1.0, a))  # 겹칠수록 짙게

        def soft(cx: float, cy: float, r: float, strength: float) -> None:
            for y in range(math.floor(cy - r), math.floor(cy + r) + 1):
                for x in range(math.floor(cx - r), math.floor(cx + r) + 1):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d < r:
                        add(x, y, strength * (1 - d / r) ** 0.7)

        # 칼 그림자: 칼날을 덮고 둘레는 더 짙게 (맥동 때 넓고 짙게)
        steps = max(2, int((shape.end - shape.start) * along_scale))
        boost = 1.0 if self.pulse else 0.0
        for k in range(steps + 1):
            a = k / steps
            if a > reach:
                break
            wave = 0.5 + 0.5 * math.sin(self.phase * 6 + k * 0.8)
            half = shape.half(a)
            for t in range(-math.ceil(half), math.ceil(half) + 1):  # 칼날 위
                x, y = place(a * NOMINAL_LENGTH, t, inside=True)
                add(math.floor(x), math.floor(y), 0.62)
            for side in (-1, 1):
                width = 2.0 + 1.5 * wave + 1.5 * boost
                for t in range(int(width) + 1):
                    x, y = place(a * NOMINAL_LENGTH, side * (0.3 + t))
                    add(math.floor(x), math.floor(y), 0.97 * (1 - t / (width + 1.5)) ** 0.8)
        for m in self.motes:
            if m.kind == "speck":
                continue
            cx, cy = place(m.x, m.off)
            life = m.age / m.life
            if m.kind == "flame":  # 그림자 불꽃: 처음 짙고 끝으로 옅어지며 줄어듦
                soft(cx, cy, m.radius * (1 - 0.5 * life), 1.1 * (1 - life) ** 0.8)
            else:  # 빨려 드는 어둠: 멀 땐 옅고 다가올수록 짙어지며 작아짐
                near = max(0.0, 1 - abs(m.off) / 9)
                soft(cx, cy, max(0.8, m.radius * min(1.0, abs(m.off) / 4)), 0.35 + 0.65 * near)
        out: list[tuple] = []
        for (x, y), a in shade.items():
            level = max((s for s in SHADE_STEPS if s <= a), default=None)
            if level is not None:
                out.append((x, y, None, level))
        for m in self.motes:  # 빨려 드는 빛 조각 (꼬리)
            if m.kind != "speck":
                continue
            pts = [place(m.x, m.off)] + [place(*p) for p in m.trail]
            for (ax, ay), (bx, by) in zip(pts[1:], pts):
                for x, y in _line((math.floor(ax), math.floor(ay)), (math.floor(bx), math.floor(by)))[:-1]:
                    out.append((x, y, GREY))
            x, y = pts[0]
            out.append((math.floor(x), math.floor(y), PALE))
        return out
