"""주인공을 따라가는 단순 카메라 (화면 스크롤).

- 맵(월드)이 화면보다 클 때, 보이는 영역의 왼쪽 아래 모서리를 월드 픽셀 좌표로 관리한다.
- 대상(주인공)을 화면 가운데에 두되, 맵 가장자리 밖은 보이지 않도록 멈춘다.
- 맵이 화면보다 작은 축은 맵을 화면 가운데에 둔다.
- 오프셋은 정수 픽셀로 맞춰 도트와 격자선이 흔들리지 않게 한다.

게임 로직(칸 좌표)과 무관한 그리기 전용 상태이며 pico2d 를 import 하지 않는다.
"""
from __future__ import annotations


class Camera:
    def __init__(self, view_width: int, view_height: int, world_width: int, world_height: int) -> None:
        if view_width <= 0 or view_height <= 0:
            raise ValueError("화면 크기는 1 이상이어야 합니다.")
        self.view_width = view_width
        self.view_height = view_height
        self.world_width = world_width
        self.world_height = world_height
        self.left = 0  # 화면 왼쪽 아래 모서리의 월드 픽셀 좌표
        self.bottom = 0

    @staticmethod
    def _clamp_axis(center: float, view: int, world: int) -> int:
        if world <= view:
            return round((world - view) / 2)  # 맵이 작으면 가운데 정렬 (음수)
        return round(min(max(center - view / 2, 0), world - view))

    def follow(self, center_x: float, center_y: float) -> None:
        """월드 픽셀 좌표 (center_x, center_y) 가 화면 가운데에 오도록 옮긴다."""
        self.left = self._clamp_axis(center_x, self.view_width, self.world_width)
        self.bottom = self._clamp_axis(center_y, self.view_height, self.world_height)
