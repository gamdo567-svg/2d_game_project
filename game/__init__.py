"""2D 액션 RPG 게임 패키지.

패키지 구성 (책임 분리):
    core     - 메인 루프, 시간(delta time) 관리
    input    - 입력 상태 관리, pico2d 이벤트 변환
    world    - 칸(타일) 좌표계, 맵 관련 로직
    physics  - 충돌 판정 (해당 기능 개발 시 구현)
    render   - pico2d 그리기 호출
    scenes   - 장면 단위 게임 흐름
"""
