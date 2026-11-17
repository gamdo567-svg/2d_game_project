"""골렘: 첫 일반 몬스터 (몬스터형: 패링당하거나 맞아도 경직 없음). 2026-11-17 사용자 결정, 수치는 임시값.

- 2×2칸을 차지한다. 주인공이 멀면 천천히 다가오고, 거리에 따라 패턴을 고른다.
    가까우면(GOLEM_NEAR) ① 두 손 내려찍기·② 앞차기·③ 한 발 내려찍기 중 하나, 중간(GOLEM_MID)이면 ② 앞차기 또는 다가감,
    더 멀면 ④ 코어 레이저(GOLEM_LASER_COOLDOWN 에 한 번) 또는 다가감. 걸을 때는 쉬지 않고 이어서 걷는다.
- 패턴마다 예고(windup) → 터짐(EnemyAttack 을 attacks 에 넣음) → 자세 되돌림(recover) → 쉼(rest).
    ① 앞 3×3, 패링 가능  ② 앞 가로 3 × 앞으로 5, 패링 불가·회피 무적 가능  ③ 중심 8×8, 점프로만 피함
    범위는 몸(2×2)을 기준으로 늘린다. 홀수 너비(①·② 3)는 남는 한 줄을 아래(왼쪽)에, 주인공이 위(오른쪽)에 있으면 그쪽에 붙인다.
    ④ 4초 동안 조준점이 주인공을 그대로 따라오다(발사 순간까지) 조준점에서 4×4 폭발 (벽 칸 제외), 회피 무적으로 피함
- 패링당하면 패링 게이지가 25% 차고(경직 없음), 가득 차면 2초 기절한다 (PostureGauge). 몬스터형이라 게이지는 저절로 줄지 않는다.
- 체력이 다하면 사라졌다가 GOLEM_RESPAWN_TIME 뒤 처음 자리에 다시 나타난다.
게임 로직은 칸 좌표로 하고, 모든 시간은 dt(초). 그리기는 draw(renderer, grid) 에서 한다: 바라보는 방향(상하좌우)의
그림(assets/images/golem, 원본 96×96 을 2배)을 발 밑이 2×2칸 바닥 가운데에 오게 그리고, 그림을 못 읽으면 부위별 임시 도형.
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable

from game import config
from game.combat.enemy_attack import EnemyAttack
from game.combat.posture import PostureGauge
from game.combat.training_dummy import DamagePopup
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
        self.size = config.GOLEM_SIZE
        self.is_wall = is_wall
        self.rng = rng or random.Random()
        self.attacks: list[EnemyAttack] = []  # 이번 프레임에 터진 공격 (장면이 주인공에게 전달)
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
        self.laser_cooldown_left = 0.0
        self._move_from = (float(self.col), float(self.row))
        self._move_t = 1.0

    # ----- 조회 -----
    @property
    def alive(self) -> bool:
        return self.state != DEAD

    @property
    def tiles(self) -> frozenset[Tile]:
        """차지한 칸 (죽어 있으면 없음)."""
        if not self.alive:
            return frozenset()
        return frozenset((self.col + dx, self.row + dy) for dx in range(self.size) for dy in range(self.size))

    @property
    def center(self) -> tuple[float, float]:
        """몸 가운데 (칸 좌표, 실수: 칸 (c, r) 의 가운데가 (c + 0.5, r + 0.5))."""
        return self.col + self.size / 2, self.row + self.size / 2

    @property
    def visual_position(self) -> tuple[float, float]:
        t = self._move_t
        return (self._move_from[0] + (self.col - self._move_from[0]) * t,
                self._move_from[1] + (self.row - self._move_from[1]) * t)

    @property
    def windup_progress(self) -> float:
        if self.state != WINDUP or self.pattern is None:
            return 0.0
        total = PATTERNS[self.pattern]["windup"]
        return 1.0 - self.state_left / total

    def distance_to(self, tile: Tile) -> int:
        """몸에서 칸까지의 거리 (몸에 붙은 칸 = 1). 가로·세로 중 큰 쪽."""
        c, r = tile
        dx = max(self.col - c, 0, c - (self.col + self.size - 1))
        dy = max(self.row - r, 0, r - (self.row + self.size - 1))
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

    def on_parried(self) -> None:
        """① 내려찍기가 패링당했다: 게이지 25%, 가득 차면 기절 (경직은 없음)."""
        if self.posture.add_parried():
            self.state = STUNNED
            self.target_tiles = frozenset()

    # ----- 로직 -----
    def update(self, dt: float, player_tile: Tile, can_place: Callable[[int, int], bool]) -> None:
        """can_place(col, row): 골렘의 왼쪽 아래 칸을 그 자리에 둘 수 있는지 (2×2 모두 비어 있는지)."""
        self.attacks = []
        self.flash_left = max(0.0, self.flash_left - dt)
        self.laser_cooldown_left = max(0.0, self.laser_cooldown_left - dt)
        self.beam_left = max(0.0, self.beam_left - dt)
        if self.beam_left == 0.0:
            self.beam_tiles = frozenset()
        for popup in self.popups:
            popup.age += dt
        self.popups = [p for p in self.popups if p.age < config.DAMAGE_POPUP_TIME]
        if self._move_t < 1.0:
            self._move_t = min(1.0, self._move_t + dt * config.GOLEM_MOVE_SPEED)

        if self.state == DEAD:
            self.state_left -= dt
            if self.state_left <= 0.0 and can_place(*self.spawn):
                self._respawn()
            return
        self.posture.update(dt)
        if self.state == STUNNED:
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
        if dist <= config.GOLEM_NEAR:
            self._windup(self.rng.choice([SLAM, KICK, STOMP]), player_tile)
        elif dist <= config.GOLEM_MID:
            if self.rng.random() < config.GOLEM_KICK_CHANCE or not self._step_toward(player_tile, can_place):
                self._windup(KICK, player_tile)
        else:
            laser_ready = self.laser_cooldown_left <= 0.0
            if laser_ready and self.rng.random() < config.GOLEM_LASER_CHANCE:
                self._windup(LASER, player_tile)
            elif not self._step_toward(player_tile, can_place):
                if laser_ready:
                    self._windup(LASER, player_tile)
                else:
                    self._rest(0.5)  # 길이 막혀 있으면 잠깐 쉬고 다시 판단

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
            self.aim = (player_tile[0] + 0.5, player_tile[1] + 0.5)
            self.target_tiles = self.laser_tiles()

    def front_area(self, width: int, depth: int, player_tile: Tile) -> frozenset[Tile]:
        """바라보는 쪽 앞의 (가로 width × 앞으로 depth) 칸. 몸(2칸)보다 넓은 줄은 양옆으로 똑같이 늘리고,
        남는 한 줄은 아래(왼쪽)에, 주인공이 몸보다 위(오른쪽)에 있으면 위(오른쪽)에 붙인다 (_spread)."""
        fx, fy = self.facing
        if fx != 0:
            first, toward = self.row, player_tile[1]
        else:
            first, toward = self.col, player_tile[0]
        before, after = _spread(first, first + self.size - 1, width, toward)
        lanes = range(first - before, first + self.size + after)
        tiles = set()
        for lane in lanes:
            for k in range(depth):  # 줄마다 벽을 만나면 그 너머는 맞지 않는다
                if fx > 0:
                    tile = (self.col + self.size + k, lane)
                elif fx < 0:
                    tile = (self.col - 1 - k, lane)
                elif fy > 0:
                    tile = (lane, self.row + self.size + k)
                else:
                    tile = (lane, self.row - 1 - k)
                if self.is_wall(*tile):
                    break
                tiles.add(tile)
        return frozenset(tiles)

    def stomp_area(self, player_tile: Tile) -> frozenset[Tile]:
        """몸을 가운데에 둔 정사각형 (GOLEM_STOMP size × size). 홀수라 남는 한 줄은 주인공 쪽으로 붙인다. 벽 칸 제외."""
        n = config.GOLEM_STOMP["size"]
        left, right = _spread(self.col, self.col + self.size - 1, n, player_tile[0])
        down, up = _spread(self.row, self.row + self.size - 1, n, player_tile[1])
        return frozenset((c, r) for c in range(self.col - left, self.col + self.size + right)
                         for r in range(self.row - down, self.row + self.size + up) if not self.is_wall(c, r))

    def _follow_aim(self, dt: float, player_tile: Tile) -> None:
        """레이저 조준점이 발사 순간까지 주인공을 그대로 따라온다 (걸어서는 못 피하고 회피 무적으로 피한다)."""
        self.aim = (player_tile[0] + 0.5, player_tile[1] + 0.5)
        self._face(player_tile)

    def laser_tiles(self) -> frozenset[Tile]:
        """조준점을 가운데로 한 size × size 폭발 칸 (벽 칸은 제외). 관통하는 일직선이 아니다."""
        n = config.GOLEM_LASER["size"]
        left = math.floor(self.aim[0] - n / 2)
        bottom = math.floor(self.aim[1] - n / 2)
        return frozenset((c, r) for c in range(left, left + n) for r in range(bottom, bottom + n)
                         if not self.is_wall(c, r))

    def _release(self) -> None:
        spec = PATTERNS[self.pattern]
        tiles = self.target_tiles
        if self.pattern == LASER:
            tiles = self.beam_tiles = self.laser_tiles()  # 폭발 칸 (잠깐 보여 줌)
            self.beam_left = spec["beam_time"]
            self.laser_cooldown_left = config.GOLEM_LASER_COOLDOWN
        self.attacks.append(EnemyAttack(tiles, spec["damage"], direction=self.facing, **PATTERN_RULES[self.pattern]))
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

        공격 애니메이션은 아직 없어 공격 중에도 서 있는 그림을 쓰고, 예고 칸·조준선 같은 효과만 보여 준다.
        """
        if not self.alive:
            return
        s = config.RENDER_SCALE
        tile = grid.tile_size
        vcol, vrow = self.visual_position
        left, bottom, _, _ = grid.tile_to_pixel_rect(vcol, vrow)
        cx = left + self.size * tile / 2
        if self._draw_sprite(renderer, cx, bottom):
            core_y = bottom + 40 * s
            bar_top = bottom + (config.GOLEM_SPRITE_SIZE - config.GOLEM_SPRITE_FOOT_MARGIN[self.view]
                                - config.GOLEM_SPRITE_HEAD_ROW + 4) * s
        else:
            core_y = self._draw_shapes(renderer, cx, bottom)
            bar_top = bottom + 66 * s
        if self.state == WINDUP and self.pattern == LASER:
            # 조준선: 레이저도 패링 불가 공격이라 노란색 (발사가 가까울수록 진하게)
            ax, ay = grid.tile_to_pixel(self.aim[0] - 0.5, self.aim[1] - 0.5)
            renderer.draw_line(cx, core_y, ax, ay, self.warning_color())
        # 체력·패링 게이지 막대 (머리 위)
        renderer.fill_rect(cx - 26 * s, bar_top, cx + 26 * s, bar_top + 3 * s, config.COLOR_BAR_BACK)
        renderer.fill_rect(cx - 26 * s, bar_top, cx - 26 * s + 52 * s * self.hp / config.GOLEM_MAX_HP, bar_top + 3 * s,
                           config.COLOR_DUMMY_HP)
        renderer.fill_rect(cx - 26 * s, bar_top - 3 * s, cx + 26 * s, bar_top - 1 * s, config.COLOR_BAR_BACK)
        renderer.fill_rect(cx - 26 * s, bar_top - 3 * s, cx - 26 * s + 52 * s * self.posture.value, bar_top - 1 * s,
                           config.COLOR_POSTURE)
        if self.state == STUNNED:
            renderer.draw_text(cx - 18 * s, bar_top + 10 * s, "STUN", config.COLOR_POSTURE)
        for popup in self.popups:
            rise = popup.age / config.DAMAGE_POPUP_TIME * config.DAMAGE_POPUP_RISE * tile
            renderer.draw_text(cx - 6 * s, bar_top + 18 * s + rise, str(popup.amount), config.COLOR_DAMAGE_TEXT)

    def _draw_sprite(self, renderer, cx: float, bottom: float) -> bool:
        """방향별 그림을 발 밑이 2×2칸 바닥 가운데에 오도록 그린다. 맞으면 깜빡인다. 그림을 못 읽으면 False."""
        if self.flash_left > 0.0 and int(self.flash_left / 0.03) % 2 == 0:
            return True  # 맞은 직후 깜빡임: 이 순간은 그리지 않음 (그림이 있다고 보고 임시 도형도 그리지 않음)
        size, s = config.GOLEM_SPRITE_SIZE, config.RENDER_SCALE
        return bool(renderer.draw_sprite_frame(
            self.sprite_path(), 0, size, size,
            cx, bottom - config.GOLEM_SPRITE_FOOT_MARGIN[self.view] * s, size * s, size * s,
        ))

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
