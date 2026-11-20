"""불 붙음 (2026-11-20 사용자 결정): 불 속성 칼로 맞으면 불이 붙어 체력이 서서히 깎인다.

- 한 대 맞을 때마다 BURN_SECONDS_PER_HIT 초씩 길어지고, 최대 BURN_MAX_SECONDS 초까지 쌓인다 (많이 때릴수록 오래 탐).
- 타는 동안 BURN_DAMAGE_PER_SECOND 의 피해를 BURN_TICK 초마다 나눠 준다.
- 회피(대쉬)할 수 있는 캐릭터는 회피하면 불이 꺼진다 (extinguish). 골렘처럼 회피가 없으면 다 탈 때까지 탄다.
- BurnFlames: 타는 몸 위에서 피었다 사그라드는 불꽃들·불티·연기 (그림용, draw_burn 이 그린다).

pico2d 를 쓰지 않는 순수 로직이다. 주인공·적이 함께 쓴다.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from game import config


class Burn:
    """불 붙음 상태. update 가 이번에 깎을 피해(정수)를 돌려준다."""

    def __init__(self) -> None:
        self.time_left = 0.0  # 남은 타는 시간 (초)
        self._tick = 0.0  # 다음 피해까지 쌓인 시간

    @property
    def burning(self) -> bool:
        return self.time_left > 0.0

    def ignite(self) -> None:
        """불 속성 공격을 한 대 맞음: 타는 시간이 늘어난다 (최대치까지)."""
        if not self.burning:
            self._tick = 0.0
        self.time_left = min(config.BURN_MAX_SECONDS, self.time_left + config.BURN_SECONDS_PER_HIT)

    def extinguish(self) -> None:
        """불이 꺼짐 (회피, 죽음 등)."""
        self.time_left = 0.0
        self._tick = 0.0

    def update(self, dt: float) -> int:
        """시간이 흐른다. 이번에 깎을 피해를 돌려준다 (BURN_TICK 초마다 한 번)."""
        if not self.burning:
            return 0
        step = min(dt, self.time_left)
        self.time_left = max(0.0, self.time_left - dt)
        self._tick += step
        damage = 0
        while self._tick >= config.BURN_TICK - 1e-9:
            self._tick -= config.BURN_TICK
            damage += round(config.BURN_DAMAGE_PER_SECOND * config.BURN_TICK)
        if not self.burning:
            self._tick = 0.0
        return damage


@dataclass
class Spark:
    """날아오르는 불티 (1 픽셀) 또는 연기 덩어리 (size > 0)."""
    x: float  # 대상 발 밑 가운데 기준 원본 픽셀 (오른쪽 +)
    y: float  # 위쪽 +
    vx: float
    vy: float
    life: float
    size: float = 0.0
    age: float = 0.0


@dataclass
class Tongue:
    """몸 위 한 자리에서 피어나 커졌다가 사그라드는 불꽃 하나."""
    x: float
    y: float
    size: float  # 다 피었을 때 크기 (시트 배율)
    variant: str  # BURN_FLAME_SHEETS 중 하나
    flip: bool
    behind: bool  # 몸 뒤 (몸보다 먼저 그림)
    life: float
    fps: float  # 시트 재생 속도 (불꽃마다 다르게)
    offset: float  # 시트 시작 장
    age: float = 0.0

    @property
    def scale(self) -> float:
        """피어남(빠르게 커짐) → 타오름 → 사그라듦(작아짐)."""
        t = self.age / self.life
        grow = min(1.0, t / 0.2)
        fade = max(0.0, min(1.0, (1.0 - t) / 0.35))
        return self.size * (grow ** 0.6) * (fade ** 0.8)


class BurnFlames:
    """타는 대상 몸의 불 (2026-11-20 사용자: 불타는 느낌 없음 → 띄엄띄엄 → 크기·모양이 다 같아 부자연스러움, 다시 만듦).

    - 불꽃 하나하나가 몸 위 아무 데서나 피어나 커졌다가 사그라들고, 그 사이 다른 자리에서 새 불꽃이 핀다 (자리가 고정되지 않음).
    - 모양 3종(가늘고 높은 혀 / 넓은 불 / 작게 날름거리는 불)을 섞고, 크기·재생 속도·좌우·수명을 불꽃마다 다르게.
    - 몸 둘레 불꽃은 몸 뒤에서 솟아 실루엣을 감싸고, 몸 앞 불꽃은 작게. 위쪽 불꽃이 더 크다.
    - 남은 타는 시간이 길수록(많이 맞을수록) 불꽃이 많이 핀다. 꺼지면 새로 피지 않고 있던 불꽃만 사그라든다.
    - 불티: 1 픽셀 불티가 흔들리며 높이 날아올라 식음. 연기: 꼭대기 위로 옅은 그림자 덩어리.
    body = (가로, 세로) 원본 픽셀, 자리는 대상 발 밑 가운데 기준 (위쪽 +).
    """

    def __init__(self, body: tuple[float, float], rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.body = body
        self.tongues: list[Tongue] = []
        self.sparks: list[Spark] = []
        self.smoke: list[Spark] = []
        self._tongue_timer = 0.0
        self._spark_timer = 0.0
        self._smoke_timer = 0.0

    def intensity(self, time_left: float) -> float:
        """불의 세기 0~1: 한 대(2초)면 약하게, BURN_FULL_SECONDS 이상 남으면 가득."""
        if time_left <= 0.0:
            return 0.0
        rest = 1 - config.BURN_MIN_INTENSITY
        return config.BURN_MIN_INTENSITY + rest * min(1.0, time_left / config.BURN_FULL_SECONDS)

    def update(self, dt: float, time_left: float) -> None:
        for t in self.tongues:
            t.age += dt
        self.tongues = [t for t in self.tongues if t.age < t.life]
        for p in self.sparks + self.smoke:
            p.age += dt
            p.x += p.vx * dt + math.sin(p.age * 9 + p.life * 20) * 6 * dt
            p.y += p.vy * dt
        self.sparks = [p for p in self.sparks if p.age < p.life]
        self.smoke = [p for p in self.smoke if p.age < p.life]
        power = self.intensity(time_left)
        if power <= 0.0:
            return
        w, h = self.body
        rng = self.rng
        self._tongue_timer -= dt
        while self._tongue_timer <= 0.0:
            self._spawn_tongue(power)
            self._tongue_timer += rng.expovariate(config.BURN_TONGUE_RATE * w * h / 100 * power)
        self._spark_timer -= dt
        while self._spark_timer <= 0.0:
            self.sparks.append(Spark(rng.uniform(-w / 2, w / 2), rng.uniform(h * 0.3, h * 1.1), rng.uniform(-10, 10),
                                     rng.uniform(35, 75), rng.uniform(0.45, 0.9)))
            self._spark_timer += rng.expovariate(config.BURN_SPARK_RATE * power)
        self._smoke_timer -= dt
        while self._smoke_timer <= 0.0:
            self.smoke.append(Spark(rng.uniform(-w / 4, w / 4), h + rng.uniform(4, 12), rng.uniform(-4, 4),
                                    rng.uniform(14, 24), rng.uniform(0.8, 1.3), rng.uniform(2.0, 3.5)))
            self._smoke_timer += rng.expovariate(config.BURN_SMOKE_RATE * power)

    def _spawn_tongue(self, power: float) -> None:
        rng = self.rng
        w, h = self.body
        behind = rng.random() < 0.55
        # 몸 앞은 아래쪽에 조금 더, 몸 뒤는 고르게 (위쪽 불꽃이 머리 위로 솟아 이글거림)
        y = h * (rng.uniform(0.1, 0.95) if behind else rng.random() ** 1.3 * 0.9)
        up = y / h
        half = w / 2 * (1.0 - 0.25 * up)  # 위로 갈수록 몸이 좁음
        if behind:  # 몸 둘레: 가장자리에서 솟아 실루엣을 감쌈
            x = rng.choice((-1, 1)) * half * rng.uniform(0.55, 1.05)
            variant = rng.choice(("tall", "tall", "wide"))
            size = rng.uniform(0.8, 1.3)
        else:  # 몸 앞: 작은 불이 듬성듬성
            x = rng.uniform(-half * 0.8, half * 0.8)
            variant = rng.choice(("lick", "lick", "tall"))
            size = rng.uniform(0.45, 0.8)
        size *= (0.8 + 0.45 * up) * (0.75 + 0.25 * power)  # 위쪽일수록, 셀수록 크게
        self.tongues.append(Tongue(x, y, size, variant, rng.random() < 0.5, behind, rng.uniform(0.45, 1.0),
                                   rng.uniform(11, 17), rng.uniform(0, config.BURN_FLAME_FRAMES)))

    def flames(self, behind: bool) -> list[tuple[float, float, float, int, bool, str]]:
        """그릴 불꽃 (x, y, 크기, 시트 장, 좌우 뒤집기, 모양). 시트 아래 가운데(불이 붙은 줄)를 (x, y) 에. 큰 것을 먼저."""
        out = []
        for t in self.tongues:
            if t.behind != behind:
                continue
            scale = t.scale
            if scale <= 0.05:
                continue
            frame = int(t.offset + t.age * t.fps) % config.BURN_FLAME_FRAMES
            out.append((t.x, t.y, scale, frame, t.flip, t.variant))
        out.sort(key=lambda f: -f[2])
        return out

    def spark_pixels(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        """불티 (x, y, 색): 처음 노랗다가 주황 → 붉게 식는다."""
        colours = config.BURN_SPARK_COLORS
        return [(math.floor(p.x), math.floor(p.y), colours[min(len(colours) - 1, int(p.age / p.life * len(colours)))])
                for p in self.sparks]

    def smoke_puffs(self) -> list[tuple[float, float, float, float]]:
        """연기 (x, y, 반지름, 짙기): 오르며 커지고 옅어진다."""
        return [(p.x, p.y, p.size * (1 + p.age / p.life), config.BURN_SMOKE_ALPHA * (1 - p.age / p.life))
                for p in self.smoke]


def draw_burn(renderer, flames: BurnFlames, cx: float, bottom: float, behind: bool) -> None:
    """불꽃을 화면에 그린다 (cx, bottom = 대상 발 밑 가운데 화면 좌표). 몸 뒤 불꽃은 몸 전에, 나머지와 불티·연기는 몸 다음에."""
    s = config.RENDER_SCALE
    w, h = config.BURN_FLAME_SIZE
    foot = config.BURN_FLAME_BASE_MARGIN
    for x, y, size, frame, flip, variant in flames.flames(behind):
        dw, dh = max(1, round(w * s * size)), max(1, round(h * s * size))
        renderer.draw_sprite_frame(config.BURN_FLAME_SHEETS[variant], frame, w, h, cx + x * s,
                                   bottom + (y - foot * size) * s, dw, dh, flip_horizontal=flip)
    if behind:
        return
    for x, y, radius, alpha in flames.smoke_puffs():
        r = max(1, round(radius))
        for py in range(-r, r + 1):
            span = round(math.sqrt(max(0, r * r - py * py)))
            renderer.fill_shade(cx + (x - span) * s, bottom + (y + py) * s, cx + (x + span + 1) * s,
                                bottom + (y + py + 1) * s, alpha)
    for x, y, colour in flames.spark_pixels():
        renderer.fill_rect(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, colour)
