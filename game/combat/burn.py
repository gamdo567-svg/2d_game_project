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
    alpha: float = 0.0  # 연기 짙기 (0 이면 BURN_SMOKE_ALPHA)
    white: bool = False  # 식을 때 흰 김 (증기)
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


@dataclass
class Hotspot:
    """불타는 곳: 몸 위를 천천히 떠돌며, 그 자리에 꺼지지 않는 큰 불길이 숨 쉬듯 일렁인다 (끊기지 않게)."""
    x: float
    y: float
    vx: float
    vy: float
    edge: int  # 몸 뒤 불길이 솟는 가장자리 쪽 (-1 왼쪽 / 1 오른쪽)
    phase: float  # 일렁임 박자
    flip: bool
    offset: float  # 시트 시작 장
    zone: tuple[float, float]  # 이 불타는 곳이 떠도는 세로 구역 (아래, 위)
    heat: float = 0.0  # 0 → 1 피어남


class BurnFlames:
    """타는 대상 몸의 불 (2026-11-20 사용자: 불타는 느낌 없음 → 띄엄띄엄 → 크기·모양이 다 같아 부자연스러움, 다시 만듦).

    - 불꽃 하나하나가 피어나 커졌다가 사그라들고, 그 사이 새 불꽃이 핀다 (자리가 고정되지 않음).
    - 모양 3종(가늘고 높은 혀 / 넓은 불 / 작게 날름거리는 불)을 섞고, 크기·재생 속도·좌우·수명을 불꽃마다 다르게.
    - 불타는 곳 (같은 날 사용자: 이펙트 떡칠은 싫지만 이글거림은 약해지면 안 됨): 몸 전체에 고르게 바르지 않고
      몸 위 몇 군데(hotspots)에 모여 세게 탄다. 불타는 곳은 천천히 옮겨 다니고, 오래 탈수록 늘어난다.
      둘레 쪽 불꽃은 몸 뒤에서 솟아 실루엣을 감싸고, 몸 앞 불꽃은 적고 작게.
    - 끊기지 않게 (같은 날 사용자: 띄엄띄엄 나와 불타는 느낌이 안 남): 불타는 곳마다 꺼지지 않는 큰 불길(몸 앞 하나,
      가장자리 몸 뒤 하나)이 숨 쉬듯 일렁이고, 둘레에 작은 불꽃이 피었다 사그라든다. 불타는 곳은 순간이동하지 않고 천천히 떠돈다.
    - 많이 맞을수록 더 (같은 날 사용자): 남은 시간(최대 10초)에 비례해 불길 크기·작은 불꽃·불티가 늘어난다.
    - 늘 몸 전체 (같은 날 사용자: 특정 위치에만 불이 타오르니 이상함): 몸을 세로 구역으로 나눠 구역마다 불타는 곳이 하나씩,
      한 대만 맞아도 발부터 머리까지 고르게 탄다 (세기는 크기·양으로만). 구역 안에서 좌우를 번갈아 두고 천천히 떠돈다.
    - 식을 때 (같은 날 사용자: 불이 식을 때 연기): 꺼지기 전 BURN_SMOLDER_TIME 초 동안 불꽃이 작아지고 연기가 짙어지며,
      꺼지는 순간 불타던 곳마다 연기가 뭉게뭉게 피어올라 천천히 흩어진다 (다 타서 꺼질 때도, 회피·죽음으로 꺼질 때도).
    - 불티: 1 픽셀 불티가 흔들리며 날아올라 식음. 연기: 불타는 곳 위로 옅은 그림자 덩어리.
    body = (가로, 세로) 원본 픽셀, 자리는 대상 발 밑 가운데 기준 (위쪽 +).
    """

    def __init__(self, body: tuple[float, float], rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.body = body
        self.tongues: list[Tongue] = []
        self.sparks: list[Spark] = []
        self.smoke: list[Spark] = []
        self.hotspots: list[Hotspot] = []  # 불타는 곳
        self._tongue_timer = 0.0
        self._spark_timer = 0.0
        self._smoke_timer = 0.0
        self._was_burning = False
        self._clock = 0.0
        self._last_power = 0.0
        self._last_smolder = 0.0
        self._side_start = 1

    @staticmethod
    def _grow(power: float) -> float:
        """세기에 따른 불길 크기 배율 (한 대면 작게, 가득이면 BURN_GROW_MAX 배)."""
        return config.BURN_GROW_MIN + (config.BURN_GROW_MAX - config.BURN_GROW_MIN) * power

    @property
    def max_hotspots(self) -> int:
        """몸 크기에 따른 불타는 곳 수 (골렘 4, 주인공·허수아비 3). 세로 구역마다 하나."""
        return max(3, round(self.body[1] / config.BURN_HOTSPOT_HEIGHT))

    def intensity(self, time_left: float) -> float:
        """불의 세기 0~1: 남은 타는 시간에 비례 (한 대 2초면 약하게, 최대 BURN_FULL_SECONDS 면 가득)."""
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
            if p.age < 0.0:
                continue
            p.x += p.vx * dt + math.sin(p.age * 9 + p.life * 20) * 6 * dt
            p.y += p.vy * dt
            if p.white:
                p.vy *= config.BURN_PUFF_DRAG ** (dt * 60)  # 김: 몸에서 솟았다가 머리 위에서 느려짐
                p.x += math.sin(p.age * 5 + p.life * 30) * 10 * dt  # 하늘하늘 흔들림
            elif p.size:
                p.vy *= 0.985  # 연기는 오르며 느려짐
        self.sparks = [p for p in self.sparks if p.age < p.life]
        self.smoke = [p for p in self.smoke if p.age < p.life]
        power = self.intensity(time_left)
        self._clock += dt
        self._last_power = power
        self._last_smolder = 0.45 + 0.55 * min(1.0, time_left / config.BURN_SMOLDER_TIME) if power > 0 else 0.0
        if power <= 0.0:
            if self._was_burning:  # 막 꺼짐: 불타던 곳마다 연기가 뭉게뭉게
                self._puff_out()
            self._was_burning = False
            self.hotspots = []
            return
        self._was_burning = True
        smolder = min(1.0, time_left / config.BURN_SMOLDER_TIME)  # 1 = 한창, 0 에 가까울수록 식는 중
        self._update_hotspots(dt, power)
        live = self.hotspots
        rng = self.rng
        self._tongue_timer -= dt
        while self._tongue_timer <= 0.0:
            self._spawn_tongue(power, smolder, rng.choice(live))
            rate = config.BURN_TONGUE_RATE * len(live) * power * (0.4 + 0.6 * smolder)
            self._tongue_timer += rng.expovariate(rate)
        self._spark_timer -= dt
        while self._spark_timer <= 0.0:
            h = rng.choice(live)
            x, y = h.x, h.y
            self.sparks.append(Spark(x + rng.uniform(-4, 4), y + rng.uniform(6, 16), rng.uniform(-10, 10),
                                     rng.uniform(35, 70), rng.uniform(0.4, 0.8)))
            self._spark_timer += rng.expovariate(config.BURN_SPARK_RATE * power * smolder + 0.01)
        self._smoke_timer -= dt
        while self._smoke_timer <= 0.0:
            h = rng.choice(live)
            x, y = h.x, h.y
            if smolder < 1.0 and rng.random() < 1.0 - smolder:  # 식는 중: 흰 연기가 퐁퐁
                self._add_smoke(x, y + 10 + rng.uniform(0, 8), heavy=True)
            else:
                self._add_smoke(x, y + 18 + rng.uniform(0, 8), heavy=False)
            # 식을수록 연기가 짙어짐
            rate = config.BURN_SMOKE_RATE * (1 + config.BURN_SMOLDER_SMOKE * (1 - smolder))
            self._smoke_timer += rng.expovariate(rate)

    def _update_hotspots(self, dt: float, power: float) -> None:
        """불타는 곳: 몸의 세로 구역마다 하나씩 (처음 불이 붙을 때 한꺼번에 피어남). 저마다 제 구역 안을 천천히 떠돈다."""
        w, h = self.body
        if not self.hotspots:
            n = self.max_hotspots
            self._side_start = self.rng.choice((-1, 1))
            for k in range(n):
                self.hotspots.append(self._new_hotspot(k, n))
        rng = self.rng
        for spot in self.hotspots:
            spot.heat = min(1.0, spot.heat + dt / config.BURN_HOTSPOT_BLOOM)
            spot.vx += rng.uniform(-1, 1) * config.BURN_HOTSPOT_WANDER * dt
            spot.vy += rng.uniform(-1, 1) * config.BURN_HOTSPOT_WANDER * dt
            spot.vx *= 0.97
            spot.vy *= 0.97
            # 제 쪽(edge) 안에서만 떠돎: 가운데를 조금 넘을 수는 있지만 반대쪽 끝까지 가지 않음
            if spot.edge > 0:
                spot.x = max(-w * 0.1, min(w * 0.4, spot.x + spot.vx * dt))
            else:
                spot.x = max(-w * 0.4, min(w * 0.1, spot.x + spot.vx * dt))
            low, high = spot.zone
            spot.y = max(low, min(high, spot.y + spot.vy * dt))
            if spot.y in (low, high):
                spot.vy = -spot.vy * 0.5

    def _new_hotspot(self, k: int, n: int) -> Hotspot:
        """k 번째 세로 구역의 불타는 곳 (아래부터, 좌우 번갈아)."""
        rng = self.rng
        w, h = self.body
        low, high = h * 0.9 * k / n, h * 0.9 * (k + 1) / n
        side = (1 if k % 2 == 0 else -1) * self._side_start  # 좌우 번갈아 (한쪽으로 쏠리지 않게)
        x = side * w * rng.uniform(0.05, 0.3)
        return Hotspot(x, rng.uniform(low, high), 0.0, 0.0, side, rng.uniform(0, 6.28), rng.random() < 0.5,
                       rng.uniform(0, config.BURN_FLAME_FRAMES), (low, high))

    def _spawn_tongue(self, power: float, smolder: float, spot: Hotspot) -> None:
        rng = self.rng
        w, h = self.body
        hx, hy = spot.x, spot.y
        y = max(0.0, min(h * 0.95, hy + rng.gauss(0, config.BURN_HOTSPOT_SPREAD[1])))
        up = y / h
        half = w / 2 * (1.0 - 0.25 * up)  # 위로 갈수록 몸이 좁음
        behind = rng.random() < 0.4
        if behind:  # 몸 뒤: 불타는 곳 쪽 가장자리에서 실루엣 밖으로 솟아 핥음 (안쪽이면 몸에 가려 안 보임)
            side = 1 if hx > 0 else -1 if hx < 0 else rng.choice((-1, 1))
            if rng.random() < 0.3:
                side = -side
            x = side * half * rng.uniform(0.85, 1.2)
            variant = rng.choice(("tall", "tall", "wide"))
            size = rng.uniform(0.75, 1.25)
        else:  # 몸 앞: 불타는 곳에 모여 타는 불
            x = max(-half, min(half, hx + rng.gauss(0, config.BURN_HOTSPOT_SPREAD[0])))
            variant = rng.choice(("lick", "tall", "tall", "wide"))
            size = rng.uniform(0.5, 0.95)
        size *= (0.8 + 0.45 * up) * self._grow(power) * (0.45 + 0.55 * smolder)  # 위쪽일수록·셀수록 크고, 식으면 작게
        self.tongues.append(Tongue(x, y, size, variant, rng.random() < 0.5, behind, rng.uniform(0.4, 0.85),
                                   rng.uniform(11, 17), rng.uniform(0, config.BURN_FLAME_FRAMES)))

    def _add_smoke(self, x: float, y: float, heavy: bool, delay: float = 0.0) -> None:
        rng = self.rng
        if heavy:  # 식을 때: 흰 김이 피어오름 (delay 만큼 늦게 나타남)
            puff = Spark(x + rng.uniform(-4, 4), y, rng.uniform(-8, 8), rng.uniform(*config.BURN_PUFF_RISE),
                         rng.uniform(*config.BURN_PUFF_LIFE), rng.uniform(*config.BURN_PUFF_SIZE), white=True)
            puff.age = -delay
            self.smoke.append(puff)
        else:
            self.smoke.append(Spark(x + rng.uniform(-3, 3), y, rng.uniform(-4, 4), rng.uniform(14, 24),
                                    rng.uniform(0.8, 1.3), rng.uniform(2.0, 3.2)))

    def _puff_out(self) -> None:
        """불이 꺼진 순간: 불타던 곳(없으면 몸 가운데)에서 연기 덩어리가 뭉게뭉게 피어오른다."""
        spots = [(spot.x, spot.y) for spot in self.hotspots] or [(0.0, self.body[1] * 0.5)]
        for x, y in spots:
            for k in range(config.BURN_PUFF_COUNT):
                self._add_smoke(x, y + 10, heavy=True, delay=k * config.BURN_PUFF_STAGGER)

    def flames(self, behind: bool) -> list[tuple[float, float, float, int, bool, str]]:
        """그릴 불꽃 (x, y, 크기, 시트 장, 좌우 뒤집기, 모양). 시트 아래 가운데(불이 붙은 줄)를 (x, y) 에. 큰 것을 먼저."""
        out = []
        w, h = self.body
        clock_power = self._last_power
        for spot in self.hotspots:  # 꺼지지 않는 중심 불길 (숨 쉬듯 일렁임)
            if spot.heat <= 0.05:
                continue
            breath = 1.0 + 0.12 * math.sin(self._clock * 5.0 + spot.phase) + 0.06 * math.sin(self._clock * 13.0 + spot.phase)
            up = spot.y / h
            base = config.BURN_CORE_SIZE * (0.8 + 0.45 * up) * self._grow(clock_power) * self._last_smolder
            frame = int(spot.offset + self._clock * 14) % config.BURN_FLAME_FRAMES
            if behind:  # 가장자리에서 몸 뒤로 솟는 불길
                half = w / 2 * (1.0 - 0.25 * up)
                out.append((spot.edge * half * 0.95, spot.y, base * 1.1 * spot.heat * breath, (frame + 5) % config.BURN_FLAME_FRAMES,
                            spot.edge < 0, "tall"))
            else:
                out.append((spot.x, spot.y, base * 0.8 * spot.heat * breath, frame, spot.flip, "wide"))
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
        """탈 때 어두운 연기 (x, y, 반지름, 짙기): 오르며 커지고 옅어진다."""
        return [(p.x, p.y, p.size * (1 + p.age / p.life), (p.alpha or config.BURN_SMOKE_ALPHA) * (1 - p.age / p.life))
                for p in self.smoke if not p.white]

    def steam_pixels(self) -> list[tuple[int, int, float]]:
        """식을 때 김 (같은 날 사용자: 흰 연기가 너무 불투명하고 부자연스러움 → 증기 느낌).
        원본 픽셀마다 (x, y, 짙기): 덩어리마다 가운데가 짙고 가장자리로 옅은 김을 쌓아 BURN_STEAM_STEPS 로 끊는다
        (픽셀풍). 덩어리는 퐁 하고 피어나 오르며 넓게 퍼지고 옅어져 사라진다."""
        field: dict[tuple[int, int], float] = {}
        for p in self.smoke:
            if not p.white or p.age < 0.0:
                continue
            t = p.age / p.life
            r = p.size * (0.7 + 1.1 * t)  # 오르며 퍼짐
            strength = 1.5 * min(1.0, t / 0.1) * (1 - t) ** 1.2  # 피어났다가 옅어짐
            for py in range(math.floor(p.y - r), math.floor(p.y + r) + 1):
                for px in range(math.floor(p.x - r), math.floor(p.x + r) + 1):
                    d = math.hypot(px + 0.5 - p.x, (py + 0.5 - p.y) * 1.15) / r
                    if d < 1:
                        field[(px, py)] = field.get((px, py), 0.0) + strength * (1 - d * d)
        out = []
        for (px, py), v in field.items():
            alpha = 0.0
            for limit, a in config.BURN_STEAM_STEPS:
                if v >= limit:
                    alpha = a
            if alpha:
                out.append((px, py, alpha))
        return out


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
    for x, y, alpha in flames.steam_pixels():  # 식을 때 김 (뒤가 비치는 흰 증기)
        renderer.fill_mist(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, alpha)
    for x, y, radius, alpha in flames.smoke_puffs():
        # 두 겹: 바깥은 옅게, 안쪽(반지름 절반)은 한 번 더 덮여 짙게 → 뭉게뭉게한 덩어리
        for r, a in ((max(1, round(radius)), alpha * 0.6), (max(1, round(radius * 0.55)), alpha * 0.5)):
            for py in range(-r, r + 1):
                span = round(math.sqrt(max(0, r * r - py * py)))
                renderer.fill_shade(cx + (x - span) * s, bottom + (y + py) * s, cx + (x + span + 1) * s,
                                    bottom + (y + py + 1) * s, a)
    for x, y, colour in flames.spark_pixels():
        renderer.fill_rect(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, colour)

