"""칸 맵 데이터: 칸마다 벽인지 바닥인지, 주인공 시작 칸.

글자 맵 파일 형식 (assets/maps/*.txt, D-023):
    - 한 줄 = 한 행, 한 글자 = 한 칸. 모든 줄의 길이가 같아야 한다.
    - `#` 벽, `.` 바닥, `P` 주인공 시작 칸(바닥). 빈 줄은 무시한다.
    - 파일의 **맨 위 줄이 가장 위쪽 행**이다. 게임의 칸 좌표는 (0, 0) 이 왼쪽 아래이므로
      맨 아래 줄이 row 0 이 된다.

게임 로직 모듈이라 pico2d 를 import 하지 않는다.
"""
from __future__ import annotations

from pathlib import Path

WALL = "#"
FLOOR = "."
PLAYER_START = "P"
KNOWN_TILES = {WALL, FLOOR, PLAYER_START}


class TileMap:
    def __init__(self, cols: int, rows: int, walls: set[tuple[int, int]],
                 player_start: tuple[int, int] | None = None) -> None:
        if cols <= 0 or rows <= 0:
            raise ValueError("맵 크기는 1 이상이어야 합니다.")
        self.cols = cols
        self.rows = rows
        self.walls = frozenset(walls)
        self.player_start = player_start

    @classmethod
    def from_text(cls, text: str) -> TileMap:
        """글자 맵을 읽는다. 맨 위 줄이 가장 위쪽 행(row = rows - 1)."""
        lines = [line.rstrip("\r") for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError("맵이 비어 있습니다.")
        cols = len(lines[0])
        if any(len(line) != cols for line in lines):
            raise ValueError("맵의 모든 줄은 길이가 같아야 합니다.")
        rows = len(lines)
        walls: set[tuple[int, int]] = set()
        start = None
        for i, line in enumerate(lines):
            row = rows - 1 - i
            for col, ch in enumerate(line):
                if ch not in KNOWN_TILES:
                    raise ValueError(f"알 수 없는 칸 글자 {ch!r} (줄 {i + 1}, 칸 {col + 1})")
                if ch == WALL:
                    walls.add((col, row))
                elif ch == PLAYER_START:
                    if start is not None:
                        raise ValueError("주인공 시작 칸(P)이 둘 이상입니다.")
                    start = (col, row)
        return cls(cols, rows, walls, start)

    @classmethod
    def load(cls, path: str | Path) -> TileMap:
        return cls.from_text(Path(path).read_text(encoding="utf-8"))

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def is_wall(self, col: int, row: int) -> bool:
        """벽 칸인지. 맵 밖은 벽으로 본다."""
        return not self.in_bounds(col, row) or (col, row) in self.walls
