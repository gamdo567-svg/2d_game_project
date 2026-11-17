"""적의 공격 한 번 (EnemyAttack). 터지는 순간 장면이 주인공에게 전달한다.

- tiles: 맞는 칸들. 주인공이 이 칸에 있으면 맞는다.
- parryable: 패링 판정 중이면 막을 수 있다.
- dodgeable: 회피 무적으로 피할 수 있다.
- jumpable: 공중(점프)에 있으면 맞지 않는다 (땅을 울리는 하단 공격).
"""
from __future__ import annotations

from dataclasses import dataclass

# 주인공이 공격을 받은 결과
HIT = "hit"
PARRIED = "parried"
AVOIDED = "avoided"  # 회피 무적·점프로 피함
MISSED = "missed"  # 범위 밖


@dataclass(frozen=True)
class EnemyAttack:
    tiles: frozenset[tuple[int, int]]
    damage: int
    parryable: bool = False
    dodgeable: bool = True
    jumpable: bool = False
    direction: tuple[int, int] = (0, 0)  # 공격 방향 (흔들림 연출용)
