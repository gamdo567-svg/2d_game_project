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
    white: bool = False  # 식을 때 흰 뭉게구름 연기 (만화처럼)
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

    - 불꽃 하나하나가 피어나 커졌다가 사그라들고, 그 사이 새 불꽃이 핀다 (자리가 고정되지 않음).
    - 모양 3종(가늘고 높은 혀 / 넓은 불 / 작게 날름거리는 불)을 섞고, 크기·재생 속도·좌우·수명을 불꽃마다 다르게.
    - 불타는 곳 (같은 날 사용자: 이펙트 떡칠은 싫지만 이글거림은 약해지면 안 됨): 몸 전체에 고르게 바르지 않고
      몸 위 몇 군데(hotspots)에 모여 세게 탄다. 불타는 곳은 천천히 옮겨 다니고, 오래 탈수록 늘어난다.
      둘레 쪽 불꽃은 몸 뒤에서 솟아 실루엣을 감싸고, 몸 앞 불꽃은 적고 작게.
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
        self.hotspots: list[list[float]] = []  # 불타는 곳 [x, y, 남은 시간]
        self._tongue_timer = 0.0
        self._spark_timer = 0.0
        self._smoke_timer = 0.0
        self._was_burning = False

    @property
    def max_hotspots(self) -> int:
        """몸 크기에 따른 불타는 곳 최대 수 (골렘 3, 주인공·허수아비 2)."""
        return max(2, round(self.body[1] / config.BURN_HOTSPOT_HEIGHT))

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
            if p.age < 0.0:
                continue
            p.x += p.vx * dt + math.sin(p.age * 9 + p.life * 20) * 6 * dt
            p.y += p.vy * dt
            if p.white:
                p.vy *= config.BURN_PUFF_DRAG ** (dt * 60)  # 흰 연기: 몸에서 확 솟았다가 머리 위에서 느려짐
            elif p.size:
                p.vy *= 0.985  # 연기는 오르며 느려짐
        self.sparks = [p for p in self.sparks if p.age < p.life]
        self.smoke = [p for p in self.smoke if p.age < p.life]
        power = self.intensity(time_left)
        if power <= 0.0:
            if self._was_burning:  # 막 꺼짐: 불타던 곳마다 연기가 뭉게뭉게
                self._puff_out()
            self._was_burning = False
            self.hotspots = []
            return
        self._was_burning = True
        smolder = min(1.0, time_left / config.BURN_SMOLDER_TIME)  # 1 = 한창, 0 에 가까울수록 식는 중
        self._update_hotspots(dt, power)
        rng = self.rng
        self._tongue_timer -= dt
        while self._tongue_timer <= 0.0:
            self._spawn_tongue(power, smolder)
            rate = config.BURN_TONGUE_RATE * len(self.hotspots) * (0.4 + 0.6 * smolder)
            self._tongue_timer += rng.expovariate(rate)
        self._spark_timer -= dt
        while self._spark_timer <= 0.0:
            x, y, _ = rng.choice(self.hotspots)
            self.sparks.append(Spark(x + rng.uniform(-4, 4), y + rng.uniform(6, 16), rng.uniform(-10, 10),
                                     rng.uniform(35, 70), rng.uniform(0.4, 0.8)))
            self._spark_timer += rng.expovariate(config.BURN_SPARK_RATE * power * smolder + 0.01)
        self._smoke_timer -= dt
        while self._smoke_timer <= 0.0:
            x, y, _ = rng.choice(self.hotspots)
            if smolder < 1.0 and rng.random() < 1.0 - smolder:  # 식는 중: 흰 연기가 퐁퐁
                self._add_smoke(x, y + 10 + rng.uniform(0, 8), heavy=True)
            else:
                self._add_smoke(x, y + 18 + rng.uniform(0, 8), heavy=False)
            # 식을수록 연기가 짙어짐
            rate = config.BURN_SMOKE_RATE * (1 + config.BURN_SMOLDER_SMOKE * (1 - smolder))
            self._smoke_timer += rng.expovariate(rate)

    def _update_hotspots(self, dt: float, power: float) -> None:
        """불타는 곳: 세기만큼 늘고, 저마다 시간이 다 되면 다른 자리로 옮겨 간다."""
        want = 1 + round((self.max_hotspots - 1) * (power - config.BURN_MIN_INTENSITY) / (1 - config.BURN_MIN_INTENSITY))
        for spot in self.hotspots:
            spot[2] -= dt
        self.hotspots = [spot for spot in self.hotspots if spot[2] > 0.0][:want]
        while len(self.hotspots) < want:
            self.hotspots.append(self._new_hotspot())

    def _new_hotspot(self) -> list[float]:
        rng = self.rng
        w, h = self.body
        y = h * rng.uniform(0.05, 0.8)
        x = rng.uniform(-w / 2, w / 2) * 0.8
        # 이미 있는 곳과 겹치지 않게 (몇 번 다시 뽑음)
        for _ in range(4):
            if all(abs(y - o[1]) > h * 0.22 or abs(x - o[0]) > w * 0.4 for o in self.hotspots):
                break
            y = h * rng.uniform(0.05, 0.8)
            x = rng.uniform(-w / 2, w / 2) * 0.8
        return [x, y, rng.uniform(*config.BURN_HOTSPOT_LIFE)]

    def _spawn_tongue(self, power: float, smolder: float) -> None:
        rng = self.rng
        w, h = self.body
        hx, hy, _ = rng.choice(self.hotspots)
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
        size *= (0.8 + 0.45 * up) * (0.75 + 0.25 * power) * (0.45 + 0.55 * smolder)  # 위쪽일수록·셀수록 크고, 식으면 작게
        self.tongues.append(Tongue(x, y, size, variant, rng.random() < 0.5, behind, rng.uniform(0.4, 0.85),
                                   rng.uniform(11, 17), rng.uniform(0, config.BURN_FLAME_FRAMES)))

    def _add_smoke(self, x: float, y: float, heavy: bool, delay: float = 0.0) -> None:
        rng = self.rng
        if heavy:  # 식을 때: 흰 뭉게구름이 퐁 하고 솟아오름 (delay 만큼 늦게 나타남)
            puff = Spark(x + rng.uniform(-4, 4), y, rng.uniform(-8, 8), rng.uniform(*config.BURN_PUFF_RISE),
                         rng.uniform(*config.BURN_PUFF_LIFE), rng.uniform(*config.BURN_PUFF_SIZE), white=True)
            puff.age = -delay
            self.smoke.append(puff)
        else:
            self.smoke.append(Spark(x + rng.uniform(-3, 3), y, rng.uniform(-4, 4), rng.uniform(14, 24),
                                    rng.uniform(0.8, 1.3), rng.uniform(2.0, 3.2)))

    def _puff_out(self) -> None:
        """불이 꺼진 순간: 불타던 곳(없으면 몸 가운데)에서 연기 덩어리가 뭉게뭉게 피어오른다."""
        spots = self.hotspots or [[0.0, self.body[1] * 0.5, 0.0]]
        for x, y, _ in spots:
            for k in range(config.BURN_PUFF_COUNT):
                self._add_smoke(x, y + 10, heavy=True, delay=k * config.BURN_PUFF_STAGGER)

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
        """탈 때 어두운 연기 (x, y, 반지름, 짙기): 오르며 커지고 옅어진다."""
        return [(p.x, p.y, p.size * (1 + p.age / p.life), (p.alpha or config.BURN_SMOKE_ALPHA) * (1 - p.age / p.life))
                for p in self.smoke if not p.white]

    def white_puffs(self) -> list[tuple[float, float, float]]:
        """식을 때 흰 뭉게구름 연기를 이루는 원들 (x, y, 반지름): 덩어리마다 큰 원 하나 + 양옆 작은 원 둘(구름 모양).
        퐁 하고 부풀었다가 오르며 커지고, 끝에서 작아져 사라진다 (만화처럼, 옅어지지 않음)."""
        out = []
        for p in self.smoke:
            if not p.white:
                continue
            t = p.age / p.life
            if t < 0.0:
                continue  # 아직 안 나타남 (차례로 퐁퐁)
            pop = min(1.0, t / 0.12) ** 0.5  # 퐁 하고 나타남
            vanish = 1.0 - max(0.0, (t - 0.65) / 0.35)  # 끝에서 작아져 사라짐
            r = p.size * (0.6 + 0.7 * t) * pop * vanish
            tilt = 1 if p.life * 1000 % 2 < 1 else -1  # 덩어리마다 구름 모양을 좌우로 다르게
            out.append((p.x, p.y, r))
            out.append((p.x - tilt * 0.8 * r, p.y - 0.35 * r, 0.68 * r))
            out.append((p.x + tilt * 0.75 * r, p.y - 0.2 * r, 0.55 * r))
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
    _draw_white_puffs(renderer, flames.white_puffs(), cx, bottom)
    for x, y, radius, alpha in flames.smoke_puffs():
        # 두 겹: 바깥은 옅게, 안쪽(반지름 절반)은 한 번 더 덮여 짙게 → 뭉게뭉게한 덩어리
        for r, a in ((max(1, round(radius)), alpha * 0.6), (max(1, round(radius * 0.55)), alpha * 0.5)):
            for py in range(-r, r + 1):
                span = round(math.sqrt(max(0, r * r - py * py)))
                renderer.fill_shade(cx + (x - span) * s, bottom + (y + py) * s, cx + (x + span + 1) * s,
                                    bottom + (y + py + 1) * s, a)
    for x, y, colour in flames.spark_pixels():
        renderer.fill_rect(cx + x * s, bottom + y * s, cx + (x + 1) * s, bottom + (y + 1) * s, colour)


def _disc(renderer, cx: float, bottom: float, x: float, y: float, r: float, colour) -> None:
    """원본 픽셀 격자에 맞춘 꽉 찬 원 (가로 줄씩)."""
    s = config.RENDER_SCALE
    if r < 0.5:
        return
    for py in range(math.floor(y - r), math.ceil(y + r) + 1):
        dy = py + 0.5 - y
        if abs(dy) > r:
            continue
        span = math.sqrt(r * r - dy * dy)
        x0, x1 = round(x - span), round(x + span)
        if x1 > x0:
            renderer.fill_rect(cx + x0 * s, bottom + py * s, cx + x1 * s, bottom + (py + 1) * s, colour)


def _draw_white_puffs(renderer, puffs: list[tuple[float, float, float]], cx: float, bottom: float) -> None:
    """흰 뭉게구름: 덩어리를 겹으로 나눠 그려 서로 붙은 한 구름이 되게 한다.
    회색 테두리 → 옅은 회색 그늘(아래) → 흰 몸통(조금 위) → 맨 위 밝은 빛."""
    outline, shade, body, light = config.BURN_PUFF_COLORS
    big = [(x, y, r) for x, y, r in puffs if r >= 1.0]
    for x, y, r in big:
        _disc(renderer, cx, bottom, x, y, r + 1, outline)
    for x, y, r in big:
        _disc(renderer, cx, bottom, x, y, r, shade)
    for x, y, r in big:
        _disc(renderer, cx, bottom, x - 0.4, y + 0.8, r - 0.8, body)
    for x, y, r in big:
        _disc(renderer, cx, bottom, x - 0.8, y + 1.6, r * 0.45, light)
