"""골렘: 첫 일반 몬스터 (몬스터형: 패링당하거나 맞아도 경직 없음). 2026-11-17 사용자 결정, 수치는 임시값.

- 1×2칸(발 칸과 그 위 한 칸)을 차지한다 (2026-11-17 사용자 요청으로 2×2 → 3×3 → 1×2). 주인공이 멀면 천천히 다가오고, 거리에 따라 패턴을 고른다.
    가까우면(GOLEM_NEAR) ① 두 손 내려찍기·② 앞차기·③ 한 발 내려찍기 중 하나, 중간(GOLEM_MID)이면 ② 앞차기 또는 다가감.
    ①·②·③ 은 주인공 칸이 실제 범위에 들 때만 고르고, 닿는 것이 없으면 다가간다 (2026-11-18 사용자 지적),
    더 멀면 다가감. 걸을 때는 쉬지 않고 이어서 걷는다.
    ④ 코어 레이저는 레이저 스택(막지 못한 빨강·노랑 공격 수)이 GOLEM_LASER_STACKS 만큼 쌓였거나
    주인공이 GOLEM_LASER_FAR 칸보다 멀면 쓴다 (2026-11-18 사용자 결정). 쏘면 스택은 0.
- 패턴마다 예고(windup) → 터짐(EnemyAttack 을 attacks 에 넣음) → 자세 되돌림(recover) → 쉼(rest).
    ① 앞 3×3, 패링 가능  ② 앞 가로 3 × 앞으로 4, 패링 불가·회피 무적 가능  ③ 중심 7×7, 점프로만 피함
    범위의 기준은 발 칸(몸 맨 아래 줄 가운데)이고, 그 칸 바로 앞부터 늘린다 (2026-11-17 사용자 결정). ①·② 가로 3 은 대칭,
    짝수 너비(③ 8)는 남는 한 줄을 아래(왼쪽)에, 주인공이 위(오른쪽)에 있으면 그쪽에 붙인다.
    ④ 4초 동안 조준점이 주인공을 그대로 따라오다(발사 순간까지) 조준점에서 4×4 폭발 (벽 칸 제외), 회피 무적으로 피함.
    레이저는 벽을 통과하지 않는다: 코어에서 주인공으로 쏜 줄이 벽에 막히면 그 앞 칸이 조준점 (2026-11-18 사용자 요청)
- 패링당하면 패링 게이지가 25% 차고(경직 없음), 가득 차면 2초 기절한다 (PostureGauge). 몬스터형이라 게이지는 저절로 줄지 않는다.
- 체력이 다하면 코어가 꺼지고 돌덩이가 무너져 사라진 뒤(죽음 동작), GOLEM_RESPAWN_TIME 뒤 처음 자리에 다시 나타난다.
게임 로직은 칸 좌표로 하고, 모든 시간은 dt(초). 그리기는 draw(renderer, grid) 에서 한다: 바라보는 방향(상하좌우)의
그림(assets/images/golem, 원본 96×96 을 2배)을 발 밑이 발 칸 바닥 가운데에 오게 그리고, 그림을 못 읽으면 부위별 임시 도형.
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable

from game import config
from game.combat.enemy_attack import HIT, PARRIED, EnemyAttack
from game.physics.raycast import first_open_stop
from game.combat.posture import PostureGauge
from game.combat.training_dummy import DamagePopup
from game.effects.effect import SpriteEffect, draw_stun_stars
from game.world.grid import Grid

SLAM, KICK, STOMP, LASER = "slam", "kick", "stomp", "laser"
REST, WALK, WINDUP, RECOVER, STUNNED, DEAD = "rest", "walk", "windup", "recover", "stunned", "dead"
PATTERNS = {SLAM: config.GOLEM_SLAM, KICK: config.GOLEM_KICK, STOMP: config.GOLEM_STOMP, LASER: config.GOLEM_LASER}
# 패턴별로 피하는 방법: 패링 가능 / 회피 무적으로 피함 / 점프(공중)로 피함
PATTERN_RULES = {
    SLAM: {"parryable": True, "dodgeable": True, "jumpable": False},
    KICK: {"parryable": False, "dodgeable": True, "jumpable": False},
    STOMP: {"parryable": False, "dodgeable": False, "jumpable": True},
    LASER: {"parryable": False, "dodgeable": True, "jumpable": False},
}


def warning_kind(pattern: str) -> str:
    """예고 칸 색 종류: 패링 가능(빨강) / 패링 불가(노랑) / 점프로만 피함(하늘색)."""
    rules = PATTERN_RULES[pattern]
    if rules["parryable"]:
        return "parryable"
    if rules["jumpable"] and not rules["dodgeable"]:
        return "jump_only"
    return "unparryable"

Tile = tuple[int, int]


def _spread(low: int, high: int, total: int, toward: int) -> tuple[int, int]:
    """[low, high] 를 total 칸으로 넓힐 때 양쪽(작은 쪽, 큰 쪽)에 붙일 칸 수. 똑같이 나누고, 남는 1칸은
    기본으로 작은 쪽(아래·왼쪽)에, 주인공(toward)이 범위보다 큰 쪽(위·오른쪽)에 있을 때만 큰 쪽에 붙인다.
    (2026-11-17 사용자 요청: 주인공이 골렘과 같은 줄일 때 남는 줄이 위로 붙어 범위가 한 칸 올라가 보였음)"""
    extra = total - (high - low + 1)
    before = after = extra // 2
    if extra % 2:
        if toward > high:
            after += 1
        else:
            before += 1
    return before, after


def _lerp_color(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


class Golem:
    def __init__(self, col: int, row: int, is_wall: Callable[[int, int], bool],
                 rng: random.Random | None = None) -> None:
        self.spawn = (col, row)
        self.width, self.height = config.GOLEM_BODY  # 몸 칸 수 (가로, 세로). (col, row) 가 왼쪽 아래 = 발 칸
        self.is_wall = is_wall
        self.rng = rng or random.Random()
        self.attacks: list[EnemyAttack] = []  # 이번 프레임에 터진 공격 (장면이 주인공에게 전달)
        self.effects: list[SpriteEffect] = []  # 이번 프레임에 시작한 이펙트 (장면이 받아서 재생)
        self.popups: list[DamagePopup] = []
        self._respawn()

    def _respawn(self) -> None:
        self.col, self.row = self.spawn
        self.hp = config.GOLEM_MAX_HP
        self.posture = PostureGauge(decays=False)  # 몬스터형: 패링 게이지가 저절로 줄지 않음
        self.state = REST
        self.state_left = config.GOLEM_REST_TIME
        self.pattern: str | None = None
        self.facing: Tile = (-1, 0)
        self.target_tiles: frozenset[Tile] = frozenset()  # 예고 중인 공격 범위
        self.aim = (float(self.col), float(self.row))  # 레이저 조준점 (칸 좌표, 실수)
        self.beam_tiles: frozenset[Tile] = frozenset()
        self.beam_left = 0.0
        self.flash_left = 0.0
        self.stun_time = 0.0  # 기절한 뒤 지난 시간 (기절 별 이펙트 재생용)
        self.laser_stacks = 0  # 막지 못한 빨강·노랑 공격 수 (GOLEM_LASER_STACKS 면 다음은 레이저)
        self._move_from = (float(self.col), float(self.row))
        self._move_t = 1.0
        self.walk_distance = 0.0

    # ----- 조회 -----
    @property
    def alive(self) -> bool:
        return self.state != DEAD

    @property
    def tiles(self) -> frozenset[Tile]:
        """차지한 칸 (죽어 있으면 없음)."""
        if not self.alive:
            return frozenset()
        return frozenset((self.col + dx, self.row + dy) for dx in range(self.width) for dy in range(self.height))

    @property
    def center(self) -> tuple[float, float]:
        """몸 가운데 (칸 좌표, 실수: 칸 (c, r) 의 가운데가 (c + 0.5, r + 0.5))."""
        return self.col + self.width / 2, self.row + self.height / 2

    @property
    def visual_position(self) -> tuple[float, float]:
        t = self._move_t
        return (self._move_from[0] + (self.col - self._move_from[0]) * t,
                self._move_from[1] + (self.row - self._move_from[1]) * t)

    @property
    def recover_progress(self) -> float:
        """공격이 터진 뒤 자세 되돌림 진행도 (0~1). 되돌림 중이 아니면 0."""
        if self.state != RECOVER:
            return 0.0
        return 1.0 - max(0.0, self.state_left) / config.GOLEM_RECOVER_TIME

    @property
    def attack_anim(self) -> tuple[str, dict] | None:
        """지금 패턴의 동작 그림 (그림 이름, 설정). 그림이 있는 패턴(①·②·③)만, 없으면 None."""
        if self.pattern == STOMP:
            return "stomp", config.GOLEM_STOMP_ANIM
        if self.pattern == SLAM:
            return "slam", config.GOLEM_SLAM_ANIM
        if self.pattern == KICK:
            return "kick", config.GOLEM_KICK_ANIM
        return None

    @property
    def attack_frame(self) -> int | None:
        """공격 동작 그림 번호 (①·②·③ 의 예고·자세 되돌림 중에만). 다른 때는 None (서 있는 그림)."""
        if self.attack_anim is None:
            return None
        anim = self.attack_anim[1]
        if self.state == WINDUP:
            frames, ends, p = anim["windup_frames"], anim["windup_ends"], self.windup_progress
        elif self.state == RECOVER:
            frames, ends, p = anim["recover_frames"], anim["recover_ends"], self.recover_progress
        else:
            return None
        return frames[next(i for i, end in enumerate(ends) if p < end or end == 1.0)]

    @property
    def walk_frame(self) -> int | None:
        """걷기 그림 번호 (한 칸 옮겨 가는 중에만). 걸은 거리로 고르므로 발이 바닥에서 미끄러지지 않는다."""
        if self._move_t >= 1.0 or not self.alive:
            return None
        anim = config.GOLEM_WALK_ANIM
        return int(self.walk_distance / anim["tiles_per_cycle"] * anim["frames"]) % anim["frames"]

    @property
    def death_frame(self) -> int | None:
        """죽음 동작 그림 번호 (죽은 뒤 동작을 다 보여 줄 때까지). 다 보여 줬거나 살아 있으면 None."""
        if self.state != DEAD:
            return None
        anim = config.GOLEM_DEATH_ANIM
        index = int((config.GOLEM_RESPAWN_TIME - self.state_left) * anim["fps"])
        return index if index < anim["frames"] else None

    @property
    def stun_frame(self) -> int | None:
        """기절 동작 그림 번호 (기절 중에만): 휘청 → 무릎 → (풀리기 직전) 일어섬. 다른 때는 None."""
        if self.state != STUNNED:
            return None
        anim = config.GOLEM_STUN_ANIM
        left = self.posture.stun_left
        if left <= anim["exit_time"]:
            frames, p = anim["exit_frames"], 1.0 - left / anim["exit_time"]
        elif self.stun_time < anim["enter_time"]:
            frames, p = anim["enter_frames"], self.stun_time / anim["enter_time"]
        else:
            return anim["kneel_frame"]
        return frames[min(len(frames) - 1, int(p * len(frames)))]

    @property
    def stomp_frame(self) -> int | None:
        """③ 발 구르기 동작 그림 번호 (attack_frame 중 ③ 만)."""
        return self.attack_frame if self.pattern == STOMP else None

    @property
    def attack_squash(self) -> float:
        """착지 순간 눌림 정도 (0 = 없음). 그림을 옆으로 넓히고 위아래로 줄이는 비율."""
        if self.attack_anim is None or self.state != RECOVER:
            return 0.0
        anim = self.attack_anim[1]
        return anim["squash"] if self.recover_progress < anim["squash_until"] else 0.0

    @property
    def stomp_squash(self) -> float:
        return self.attack_squash if self.pattern == STOMP else 0.0

    @property
    def windup_progress(self) -> float:
        if self.state != WINDUP or self.pattern is None:
            return 0.0
        total = PATTERNS[self.pattern]["windup"]
        return 1.0 - self.state_left / total

    def distance_to(self, tile: Tile) -> int:
        """몸에서 칸까지의 거리 (몸에 붙은 칸 = 1). 가로·세로 중 큰 쪽."""
        c, r = tile
        dx = max(self.col - c, 0, c - (self.col + self.width - 1))
        dy = max(self.row - r, 0, r - (self.row + self.height - 1))
        return max(dx, dy)

    # ----- 맞기 -----
    def take_hit(self, damage: int, direction: Tile) -> bool:
        """주인공의 공격을 맞는다. 몬스터형이라 경직은 없다."""
        if not self.alive:
            return False
        self.hp = max(0, self.hp - damage)
        self.flash_left = config.GOLEM_HIT_FLASH_TIME
        self.popups.append(DamagePopup(damage))
        if self.hp == 0:
            self.state = DEAD
            self.state_left = config.GOLEM_RESPAWN_TIME
            self.target_tiles = frozenset()
            self.beam_tiles = frozenset()
        return True

    def on_attack_result(self, attack: EnemyAttack, result: str, perfect_dodged: bool) -> None:
        """방금 터진 공격의 결과(HIT/PARRIED/AVOIDED/MISSED)로 레이저 스택을 쌓는다 (2026-11-18 사용자 결정).

        빨강(패링 가능)은 패링으로, 노랑(패링 불가·회피 가능)은 퍼펙트 회피로 막아야 한다. 걸어서 범위 밖으로 피했거나
        그냥 회피했으면 한 스택. 맞았으면(HIT) 이미 피해를 받았으니 쌓지 않는다 (2026-11-18 사용자 요청).
        하늘색(점프로만 피함)과 레이저 자신은 세지 않는다.
        """
        if self.pattern == LASER or attack.jumpable or result == HIT:
            return
        blocked = result == PARRIED if attack.parryable else perfect_dodged
        if not blocked:
            self.laser_stacks = min(config.GOLEM_LASER_STACKS, self.laser_stacks + 1)

    @property
    def laser_charged(self) -> bool:
        return self.laser_stacks >= config.GOLEM_LASER_STACKS

    def on_perfect_dodged(self) -> None:
        """공격이 퍼펙트 회피당했다 (2026-11-18 사용자 요청): 패링당한 것처럼 게이지가 차고, 가득 차면 기절."""
        self._add_posture(config.POSTURE_PERFECT_DODGE_GAIN)

    def on_parried(self) -> None:
        """① 내려찍기가 패링당했다: 게이지 25%, 가득 차면 기절 (경직은 없음)."""
        self._add_posture(config.POSTURE_PARRIED_GAIN)

    def _add_posture(self, amount: float) -> None:
        if self.posture.add(amount):
            self.state = STUNNED
            self.stun_time = 0.0
            self.target_tiles = frozenset()

    # ----- 로직 -----
    def update(self, dt: float, player_tile: Tile, can_place: Callable[[int, int], bool]) -> None:
        """can_place(col, row): 골렘의 왼쪽 아래 칸을 그 자리에 둘 수 있는지 (몸 칸이 모두 비어 있는지)."""
        self.attacks = []
        self.effects = []
        self.flash_left = max(0.0, self.flash_left - dt)
        self.beam_left = max(0.0, self.beam_left - dt)
        if self.beam_left == 0.0:
            self.beam_tiles = frozenset()
        for popup in self.popups:
            popup.age += dt
        self.popups = [p for p in self.popups if p.age < config.DAMAGE_POPUP_TIME]
        if self._move_t < 1.0:
            before = self._move_t
            self._move_t = min(1.0, self._move_t + dt * config.GOLEM_MOVE_SPEED)
            self.walk_distance += self._move_t - before  # 걸은 칸 수 (걷기 그림 고르기용)

        if self.state == DEAD:
            self.state_left -= dt
            if self.state_left <= 0.0 and can_place(*self.spawn):
                self._respawn()
            return
        self.posture.update(dt)
        if self.state == STUNNED:
            self.stun_time += dt
            if not self.posture.is_stunned:
                self._rest()
            return

        self.state_left -= dt
        if self.state == WINDUP and self.pattern == LASER:
            self._follow_aim(dt, player_tile)
            self.target_tiles = self.laser_tiles()  # 터질 범위가 조준점을 따라다니며 예고된다
        if self.state_left > 0.0:
            return
        if self.state == WINDUP:
            self._release()
        elif self.state == RECOVER:
            self._rest()
        elif self.state in (REST, WALK) and self._move_t >= 1.0:
            self._decide(player_tile, can_place)

    def _rest(self, seconds: float = config.GOLEM_REST_TIME) -> None:
        self.state = REST
        self.state_left = seconds
        self.pattern = None
        self.target_tiles = frozenset()

    def _decide(self, player_tile: Tile, can_place: Callable[[int, int], bool]) -> None:
        dist = self.distance_to(player_tile)
        if config.GOLEM_LASER_ENABLED and (self.laser_charged or dist > config.GOLEM_LASER_FAR):
            self._windup(LASER, player_tile)
        elif dist <= config.GOLEM_NEAR and (near := [p for p in (SLAM, KICK, STOMP) if self.reaches(p, player_tile)]):
            self._windup(self.rng.choice(near), player_tile)
        elif (dist <= config.GOLEM_MID and self.reaches(KICK, player_tile)
              and self.rng.random() < config.GOLEM_KICK_CHANCE):
            self._windup(KICK, player_tile)
        elif not self._step_toward(player_tile, can_place):
            if self.reaches(KICK, player_tile):
                self._windup(KICK, player_tile)  # 길이 막혔지만 차기는 닿는다
            else:
                self._rest(0.5)  # 길이 막혀 있으면 잠깐 쉬고 다시 판단

    def reaches(self, pattern: str, player_tile: Tile) -> bool:
        """지금 이 패턴을 쓰면 주인공 칸이 범위 안에 드는지 (2026-11-18 사용자 지적: 닿지도 않는 거리에서 차기를 함).
        거리만 보지 않고 실제 범위(①·② 바라볼 쪽 앞, ③ 발 칸 둘레)를 계산해 본다."""
        facing = self.facing
        self._face(player_tile)
        if pattern == STOMP:
            tiles = self.stomp_area(player_tile)
        else:
            spec = PATTERNS[pattern]
            tiles = self.front_area(spec["width"], spec["depth"], player_tile)
        self.facing = facing
        return player_tile in tiles

    def _step_toward(self, player_tile: Tile, can_place: Callable[[int, int], bool]) -> bool:
        """주인공 쪽으로 한 칸 걷는다 (차이가 큰 축 먼저). 못 가면 False."""
        cx, cy = self.center
        dx = player_tile[0] + 0.5 - cx
        dy = player_tile[1] + 0.5 - cy
        steps = [(int(math.copysign(1, dx)), 0), (0, int(math.copysign(1, dy)))]
        if abs(dy) > abs(dx):
            steps.reverse()
        for sx, sy in steps:
            if (sx, sy) != (0, 0) and can_place(self.col + sx, self.row + sy):
                self._move_from = (float(self.col), float(self.row))
                self.col += sx
                self.row += sy
                self._move_t = 0.0
                self.facing = (sx, sy)
                self.state = WALK
                self.state_left = 1.0 / config.GOLEM_MOVE_SPEED
                return True
        return False

    def _face(self, player_tile: Tile) -> None:
        cx, cy = self.center
        dx = player_tile[0] + 0.5 - cx
        dy = player_tile[1] + 0.5 - cy
        if abs(dx) >= abs(dy):
            self.facing = (1 if dx > 0 else -1, 0)
        else:
            self.facing = (0, 1 if dy > 0 else -1)

    def _windup(self, pattern: str, player_tile: Tile) -> None:
        self.pattern = pattern
        self.state = WINDUP
        self.state_left = PATTERNS[pattern]["windup"]
        self._face(player_tile)
        if pattern in (SLAM, KICK):
            spec = PATTERNS[pattern]
            self.target_tiles = self.front_area(spec["width"], spec["depth"], player_tile)
        elif pattern == STOMP:
            self.target_tiles = self.stomp_area(player_tile)
        else:
            self.aim = self._laser_aim(player_tile)
            self.target_tiles = self.laser_tiles()

    @property
    def feet_tile(self) -> Tile:
        """공격 기준 칸: 몸 맨 아래 줄 가운데 (그림의 발 밑). 2026-11-17 사용자 결정: 범위는 이 칸 바로 앞부터."""
        return self.col + self.width // 2, self.row

    def front_area(self, width: int, depth: int, player_tile: Tile) -> frozenset[Tile]:
        """발 칸(feet_tile) 바로 앞부터 바라보는 쪽으로 (가로 width × 앞으로 depth) 칸. 가로는 발 칸을 가운데로
        양옆에 똑같이 늘리고, 짝수라 남는 한 줄은 아래(왼쪽)에, 주인공이 위(오른쪽)에 있으면 그쪽에 붙인다 (_spread).
        측면 그림이 몸 3칸보다 좁아 범위가 몸 칸과 겹칠 수 있다 (사용자 결정)."""
        fx, fy = self.facing
        foot_col, foot_row = self.feet_tile
        if fx != 0:
            first, toward = foot_row, player_tile[1]
        else:
            first, toward = foot_col, player_tile[0]
        before, after = _spread(first, first, width, toward)
        lanes = range(first - before, first + 1 + after)
        tiles = set()
        for lane in lanes:
            for k in range(depth):  # 줄마다 벽을 만나면 그 너머는 맞지 않는다
                if fx > 0:
                    tile = (foot_col + 1 + k, lane)
                elif fx < 0:
                    tile = (foot_col - 1 - k, lane)
                elif fy > 0:
                    tile = (lane, foot_row + 1 + k)
                else:
                    tile = (lane, foot_row - 1 - k)
                if self.is_wall(*tile):
                    break
                tiles.add(tile)
        return frozenset(tiles)

    def stomp_area(self, player_tile: Tile) -> frozenset[Tile]:
        """발 칸(feet_tile)을 가운데에 둔 정사각형 (GOLEM_STOMP size × size). 남는 한 줄은 아래(왼쪽),
        주인공이 위(오른쪽)이면 그쪽에 붙인다 (_spread). 벽 칸 제외."""
        n = config.GOLEM_STOMP["size"]
        fc, fr = self.feet_tile
        left, right = _spread(fc, fc, n, player_tile[0])
        down, up = _spread(fr, fr, n, player_tile[1])
        return frozenset((c, r) for c in range(fc - left, fc + 1 + right)
                         for r in range(fr - down, fr + 1 + up) if not self.is_wall(c, r))

    def _follow_aim(self, dt: float, player_tile: Tile) -> None:
        """레이저 조준점이 발사 순간까지 주인공을 그대로 따라온다 (걸어서는 못 피하고 회피 무적으로 피한다)."""
        self.aim = self._laser_aim(player_tile)
        self._face(player_tile)

    def _laser_aim(self, player_tile: Tile) -> tuple[float, float]:
        """레이저 조준점: 몸 가운데(코어)에서 주인공 칸 가운데로 쏜 줄이 벽에 막히면 그 앞 칸 가운데
        (2026-11-18 사용자 요청: 벽을 통과하지 않게, 레이캐스트). 막히지 않으면 주인공 칸 가운데."""
        target = (player_tile[0] + 0.5, player_tile[1] + 0.5)
        return first_open_stop(self.center, target, self.is_wall)[0]

    def laser_tiles(self) -> frozenset[Tile]:
        """조준점을 가운데로 한 size × size 폭발 칸. 벽 칸과, 조준점에서 보아 벽 너머인 칸은 뺀다
        (2026-11-18 사용자 요청: 레이저가 벽을 통과하지 않게. 폭발도 벽을 넘지 않는다)."""
        n = config.GOLEM_LASER["size"]
        left = math.floor(self.aim[0] - n / 2)
        bottom = math.floor(self.aim[1] - n / 2)
        return frozenset((c, r) for c in range(left, left + n) for r in range(bottom, bottom + n)
                         if not self.is_wall(c, r)
                         and not first_open_stop(self.aim, (c + 0.5, r + 0.5), self.is_wall)[1])

    def _release(self) -> None:
        spec = PATTERNS[self.pattern]
        tiles = self.target_tiles
        if self.pattern == LASER:
            tiles = self.beam_tiles = self.laser_tiles()  # 폭발 칸 (잠깐 보여 줌)
            self.beam_left = spec["beam_time"]
            self.laser_stacks = 0
            # 조준점 폭발 (흰 섬광·충격 고리·불꽃, 화면 흔들림)
            self.effects.append(SpriteEffect(config.GOLEM_LASER_BLAST_EFFECT, self.aim[0], self.aim[1]))
        self.attacks.append(EnemyAttack(tiles, spec["damage"], direction=self.facing, **PATTERN_RULES[self.pattern]))
        if self.pattern == STOMP:
            # 발 구르기: 발 칸 가운데에서 바닥이 갈라지는 이펙트 + 화면 흔들림
            fc, fr = self.feet_tile
            self.effects.append(SpriteEffect(config.GOLEM_STOMP_EFFECT, fc + 0.5, fr + 0.5))
        elif self.pattern == SLAM and tiles:
            # 두 손 내려찍기: 앞 범위 칸들의 가운데에서 금·돌 파편·먼지 + 약한 흔들림
            cx = sum(c for c, _ in tiles) / len(tiles) + 0.5
            cy = sum(r for _, r in tiles) / len(tiles) + 0.5
            self.effects.append(SpriteEffect(config.GOLEM_SLAM_EFFECT, cx, cy))
        self.state = RECOVER
        self.state_left = config.GOLEM_RECOVER_TIME
        self.target_tiles = frozenset()

    # ----- 그리기 (임시 도형: 팔·다리·몸통·코어를 나눠 그림) -----
    def draw_warning(self, renderer, grid: Grid) -> None:
        """공격 예고 칸과 레이저 (주인공·골렘보다 먼저, 바닥에 그린다)."""
        if self.state == WINDUP and self.target_tiles:
            color = self.warning_color()
            for col, row in self.target_tiles:
                renderer.fill_tile(grid, col, row, color, inset=2)
        if self.beam_tiles:
            beam = config.COLOR_WARN[warning_kind(LASER)][1]
            for col, row in self.beam_tiles:
                renderer.fill_tile(grid, col, row, beam, inset=8)

    def warning_color(self) -> tuple[int, int, int]:
        """지금 예고 중인 공격의 색 (종류별 색, 터지기 직전일수록 진하게)."""
        faint, strong = config.COLOR_WARN[warning_kind(self.pattern)]
        return _lerp_color(faint, strong, self.windup_progress)

    @property
    def view(self) -> str:
        """바라보는 방향의 그림 이름 (상하좌우만, 대각선 그림은 쓰지 않음)."""
        return {(0, -1): "south", (0, 1): "north", (1, 0): "east", (-1, 0): "west"}[self.facing]

    def sprite_path(self) -> str:
        return str(config.GOLEM_IMAGE_DIR / f"{self.view}.png")

    def draw(self, renderer, grid: Grid) -> None:
        """그림(방향별 서 있는 그림)을 그리고, 못 읽으면 부위별 임시 도형을 그린다. 그 위에 조준선·막대·글자.

        ③ 발 구르기만 동작 그림이 있다 (무릎 들기 → 쾅 → 반동). 나머지 공격은 아직 서 있는 그림을 쓰고,
        예고 칸·조준선 같은 효과만 보여 준다.
        """
        s = config.RENDER_SCALE
        tile = grid.tile_size
        vcol, vrow = self.visual_position
        left, bottom, _, _ = grid.tile_to_pixel_rect(vcol, vrow)
        cx = left + self.width * tile / 2
        if not self.alive:
            # 죽음: 코어가 꺼지고 돌덩이가 무너져 사라지는 그림만 (막대·글자 없음)
            frame = self.death_frame
            if frame is not None:
                self._draw_anim(renderer, self.attack_sprite_path("death"), config.GOLEM_DEATH_ANIM, frame, cx, bottom)
            return
        if self._draw_sprite(renderer, cx, bottom):
            core_y = bottom + 40 * s
            bar_top = bottom + (config.GOLEM_SPRITE_SIZE - config.GOLEM_SPRITE_FOOT_MARGIN[self.view]
                                - config.GOLEM_SPRITE_HEAD_ROW + 4) * s
        else:
            core_y = self._draw_shapes(renderer, cx, bottom)
            bar_top = bottom + 66 * s
        if self._draw_laser(renderer, grid, cx, bottom):
            pass
        elif self.state == WINDUP and self.pattern == LASER:
            # 그림이 없을 때(임시 도형): 조준선만
            ax, ay = grid.tile_to_pixel(self.aim[0] - 0.5, self.aim[1] - 0.5)
            renderer.draw_line(cx, core_y, ax, ay, self.warning_color())
        if self.state == STUNNED:
            # 기절: 머리 꼭대기에서 별이 돈다 (공용 이펙트). 막대는 링 위로 올린다.
            # 무릎을 꿇으면 머리가 내려간 만큼 별·막대도 내린다
            frame = self.stun_frame
            bar_top -= config.GOLEM_STUN_ANIM["head_drop"][frame] * s if frame is not None else 0
            head_top = bar_top - 4 * s
            draw_stun_stars(renderer, cx, head_top + 2 * s, s, self.stun_time)
            bar_top += config.STUN_BAR_LIFT * s
        # 체력·패링 게이지 막대 (머리 위)
        renderer.fill_rect(cx - 26 * s, bar_top, cx + 26 * s, bar_top + 3 * s, config.COLOR_BAR_BACK)
        renderer.fill_rect(cx - 26 * s, bar_top, cx - 26 * s + 52 * s * self.hp / config.GOLEM_MAX_HP, bar_top + 3 * s,
                           config.COLOR_DUMMY_HP)
        renderer.fill_rect(cx - 26 * s, bar_top - 3 * s, cx + 26 * s, bar_top - 1 * s, config.COLOR_BAR_BACK)
        renderer.fill_rect(cx - 26 * s, bar_top - 3 * s, cx - 26 * s + 52 * s * self.posture.value, bar_top - 1 * s,
                           config.COLOR_POSTURE)
        for popup in self.popups:
            rise = popup.age / config.DAMAGE_POPUP_TIME * config.DAMAGE_POPUP_RISE * tile
            renderer.draw_text(cx - 6 * s, bar_top + 18 * s + rise, str(popup.amount), config.COLOR_DAMAGE_TEXT)

    def _draw_sprite(self, renderer, cx: float, bottom: float) -> bool:
        """방향별 그림을 발 밑이 발 칸 바닥 가운데에 오도록 그린다. 맞으면 깜빡인다. 그림을 못 읽으면 False.

        ①·②·③ 예고·자세 되돌림 중에는 그 공격 동작 그림, 한 칸 걸어가는 중에는 걷기 그림을 쓰고,
        그 그림을 못 읽으면 서 있는 그림을 쓴다.
        """
        if self.flash_left > 0.0 and int(self.flash_left / 0.03) % 2 == 0:
            return True  # 맞은 직후 깜빡임: 이 순간은 그리지 않음 (그림이 있다고 보고 임시 도형도 그리지 않음)
        size, s = config.GOLEM_SPRITE_SIZE, config.RENDER_SCALE
        frame = self.stun_frame
        if frame is not None and self._draw_anim(renderer, self.attack_sprite_path("stun"), config.GOLEM_STUN_ANIM,
                                                 frame, cx, bottom):
            return True
        frame = self.attack_frame
        if frame is not None:
            name, anim = self.attack_anim
            if self._draw_anim(renderer, self.attack_sprite_path(name), anim, frame, cx, bottom, self.attack_squash):
                return True
        frame = self.walk_frame
        if frame is not None and self._draw_anim(renderer, self.walk_sprite_path(), config.GOLEM_WALK_ANIM,
                                                 frame, cx, bottom):
            return True
        return bool(renderer.draw_sprite_frame(
            self.sprite_path(), 0, size, size,
            cx, bottom - config.GOLEM_SPRITE_FOOT_MARGIN[self.view] * s, size * s, size * s,
        ))

    @property
    def laser_charge_frames(self) -> tuple[int, int] | None:
        """충전 그림 번호 (빛 알갱이, 구). ④ 예고 중에만. 빛 알갱이는 지난 시간으로 실제 속도로 돌고,
        구는 충전 진행도로 커진다 (2026-11-18 사용자 요청: 빛이 뚝뚝 끊기지 않고 자연스럽게 모이게)."""
        if not (self.state == WINDUP and self.pattern == LASER):
            return None
        spec = config.GOLEM_LASER_CHARGE
        elapsed = config.GOLEM_LASER["windup"] - max(0.0, self.state_left)
        motes = int(elapsed * spec["motes_fps"]) % spec["motes_frames"]
        orb = min(spec["orb_frames"] - 1, int(self.windup_progress * spec["orb_frames"]))
        return motes, orb

    def _draw_laser(self, renderer, grid: Grid, cx: float, bottom: float) -> bool:
        """④ 충전 구(코어)·조준선, 발사 직후 하얀 레이저 (코어 → 조준점). 그린 것이 있으면 True."""
        spec, s = config.GOLEM_LASER_CHARGE, config.RENDER_SCALE
        ox, oy = spec["core"][self.view]
        core_x, core_y = cx + ox * s, bottom + oy * s
        ax, ay = grid.tile_to_pixel(self.aim[0] - 0.5, self.aim[1] - 0.5)
        frames = self.laser_charge_frames
        if frames is not None:
            renderer.draw_line(core_x, core_y, ax, ay, self.warning_color())  # 조준선 (노랑, 발사가 가까울수록 진하게)
            motes, orb = frames
            m, o = spec["motes_size"], spec["orb_size"]
            drawn = renderer.draw_sheet_frame(str(spec["motes_path"]), motes, spec["motes_frames"], m, m,
                                              core_x, core_y, m * s, m * s)
            drawn = renderer.draw_sheet_frame(str(spec["orb_path"]), orb, spec["orb_frames"], o, o,
                                              core_x, core_y, o * s, o * s) or drawn
            return bool(drawn)
        if self.beam_left > 0.0:
            beam = config.GOLEM_LASER_BEAM
            thickness = max(2, round(beam["thickness"] * self.beam_left / config.GOLEM_LASER["beam_time"]))
            length = math.hypot(ax - core_x, ay - core_y)
            angle = math.degrees(math.atan2(ay - core_y, ax - core_x))
            renderer.draw_image_rotated(str(beam["path"]), (core_x + ax) / 2, (core_y + ay) / 2,
                                        round(length), thickness, angle)
            return True
        return False

    def attack_sprite_path(self, name: str) -> str:
        return str(config.GOLEM_IMAGE_DIR / f"{name}_{self.view}.png")

    def stomp_sprite_path(self) -> str:
        return self.attack_sprite_path("stomp")

    def walk_sprite_path(self) -> str:
        return str(config.GOLEM_IMAGE_DIR / f"walk_{self.view}.png")

    def _draw_anim(self, renderer, path: str, anim: dict, frame: int, cx: float, bottom: float,
                   k: float = 0.0) -> bool:
        """동작 그림 한 장을 발 밑 가운데(foot)가 발 칸 바닥 가운데에 오게 그린다. k 만큼 눌러 그린다 (착지 순간)."""
        s = config.RENDER_SCALE
        w, h = anim["frame_size"]
        fx, fy = anim["foot"]
        dw, dh = round(w * s * (1 + k)), round(h * s * (1 - k))
        below = (h - fy) * s * (1 - k)  # 그림 아래쪽 투명 줄 (발 밑 아래)
        left_of_foot = fx * s * (1 + k)
        # draw_sprite_frame 은 그림 아래 가운데 기준: 발 밑 가운데가 cx 에 오도록 가운데를 옮긴다
        center_x = cx - left_of_foot + dw / 2
        return bool(renderer.draw_sprite_frame(path, frame, w, h, center_x, bottom - below, dw, dh))

    def _draw_shapes(self, renderer, cx: float, bottom: float) -> float:
        """그림이 없을 때의 임시 도형 (다리·몸통·팔·코어). 코어 높이(조준선 출발점)를 돌려준다."""
        s = config.RENDER_SCALE
        white = self.flash_left > 0.0
        body = config.COLOR_WHITE if white else config.COLOR_GOLEM_BODY
        limb = config.COLOR_WHITE if white else config.COLOR_GOLEM_LIMB
        edge = config.COLOR_GOLEM_EDGE
        p = self.windup_progress
        raise_arms = 20 * s * p if self.pattern == SLAM and self.state == WINDUP else 0
        lift_leg = 14 * s * p if self.pattern in (KICK, STOMP) and self.state == WINDUP else 0
        crouch = 3 * s * p if self.pattern == STOMP and self.state == WINDUP else 0
        # 다리 두 개
        renderer.fill_rect(cx - 22 * s, bottom + 2 * s + lift_leg, cx - 6 * s, bottom + 24 * s + lift_leg, edge)
        renderer.fill_rect(cx - 21 * s, bottom + 3 * s + lift_leg, cx - 7 * s, bottom + 23 * s + lift_leg, limb)
        renderer.fill_rect(cx + 6 * s, bottom + 2 * s, cx + 22 * s, bottom + 24 * s, edge)
        renderer.fill_rect(cx + 7 * s, bottom + 3 * s, cx + 21 * s, bottom + 23 * s, limb)
        # 몸통
        top = bottom + 58 * s - crouch
        renderer.fill_rect(cx - 26 * s, bottom + 20 * s - crouch, cx + 26 * s, top, edge)
        renderer.fill_rect(cx - 25 * s, bottom + 21 * s - crouch, cx + 25 * s, top - 1 * s, body)
        # 팔 두 개 (내려찍기 예고 때 머리 위로 올라감)
        for side in (-1, 1):
            ax0 = cx + side * 26 * s
            ax1 = cx + side * 36 * s
            lo, hi = min(ax0, ax1), max(ax0, ax1)
            renderer.fill_rect(lo, bottom + 14 * s + raise_arms, hi, bottom + 50 * s + raise_arms, edge)
            renderer.fill_rect(lo + 1 * s, bottom + 15 * s + raise_arms, hi - 1 * s, bottom + 49 * s + raise_arms, limb)
        # 코어 (레이저 충전 중에는 점점 뜨거워짐)
        heat = p if self.pattern == LASER and self.state == WINDUP else 0.0
        core = _lerp_color(config.COLOR_GOLEM_CORE, config.COLOR_GOLEM_CORE_HOT, heat)
        renderer.fill_rect(cx - 7 * s, bottom + 34 * s - crouch, cx + 7 * s, bottom + 46 * s - crouch, core)
        return bottom + 40 * s - crouch
