"""게임 전역 설정 값.

현재 수치 대부분은 초기 환경 구성용 임시값이다.
값을 바꾸면 docs/DECISIONS.md 의 관련 항목도 함께 갱신한다.
"""
from pathlib import Path

# ----- 경로 -----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAYER_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "player"

# ----- 화면 (픽셀) -----
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576

# ----- 칸(타일) -----
# 논리 칸 크기: 도트 원본(에셋) 기준 한 칸의 픽셀 크기. 게임 로직은 칸 좌표만 쓴다.
LOGICAL_TILE_SIZE = 32
# 화면 표시 배율. 이 값만 바꾸면 타일·주인공 표시 크기가 함께 바뀐다 (확대/축소).
# 도트가 흐려지지 않도록 정수 배율을 권장한다.
RENDER_SCALE = 2
RENDER_TILE_SIZE = LOGICAL_TILE_SIZE * RENDER_SCALE  # 64: 한 칸이 화면에 그려지는 크기(픽셀)

# 맵(월드) 크기 (칸). 표시 배율과 무관하다.
GRID_COLS = 32
GRID_ROWS = 18
# 한 화면에 보이는 칸 수 (참고용). 1024×576 / 64 = 16×9
VIEW_COLS = SCREEN_WIDTH / RENDER_TILE_SIZE
VIEW_ROWS = SCREEN_HEIGHT / RENDER_TILE_SIZE

# ----- 플레이어 그림 크기 -----
# 스프라이트 시트 원본 프레임 크기 (에셋 픽셀). 충돌은 논리적 칸 좌표로 처리한다.
PLAYER_SPRITE_WIDTH = 32
PLAYER_SPRITE_HEIGHT = 48
# 화면에 그리는 크기 (렌더링 픽셀) = 원본 × RENDER_SCALE
PLAYER_RENDER_WIDTH = PLAYER_SPRITE_WIDTH * RENDER_SCALE  # 64
PLAYER_RENDER_HEIGHT = PLAYER_SPRITE_HEIGHT * RENDER_SCALE  # 96

# ----- 플레이어 이동 -----
# [임시값] PRE-PRD 2.1 [제안] 초기값 후보. 실제 플레이 후 조정한다.
PLAYER_MOVE_SPEED = 6.0  # 칸/초 (한 칸 이동 시간 = 1 / 6초)
# 시작 위치 (칸 좌표). 맵 중앙 칸.
PLAYER_START_COL = GRID_COLS // 2
PLAYER_START_ROW = GRID_ROWS // 2

# ----- 플레이어 애니메이션 -----
# 스프라이트 시트: assets/images/player/<상태>/<front|back|side>.png 한 파일에 프레임을 가로로 이어 붙인다.
# 상태별 프레임 수 (방향마다 같음). 시트 가로 크기 = 프레임 수 × PLAYER_SPRITE_WIDTH
PLAYER_IDLE_FRAMES = 4  # 몸은 고정, 망토 끝만 흔들림
PLAYER_WALK_FRAMES = 4  # 오른발 디딤 → 모음 → 왼발 디딤 → 모음
# [임시값] 프레임 하나를 보여 주는 시간(초). 실제 화면을 보며 조정한다.
PLAYER_IDLE_FRAME_DURATION = 0.2
PLAYER_WALK_FRAME_DURATION = 0.1

# ----- 플레이어 점프 / 패링 -----
# [임시값] 2026-11-10 사용자 승인. 4프레임은 행동 시간을 4등분해 재생한다.
PLAYER_JUMP_DURATION = 0.45  # 초 (웅크림 1/4, 공중 1/2, 착지 1/4)
PLAYER_JUMP_HEIGHT = 0.5  # 칸. 그림만 띄우며 논리적 칸 위치는 그대로
PLAYER_PARRY_DURATION = 0.4  # 초. 이 동안 이동 불가
PLAYER_PARRY_WINDOW = 0.15  # 초. 누른 순간부터 막기 판정
PLAYER_JUMP_FRAMES = 4
PLAYER_PARRY_FRAMES = 4
# 점프 그림자 원본 크기 (assets/images/player/shadow.png)
PLAYER_SHADOW_WIDTH = 24
PLAYER_SHADOW_HEIGHT = 6

# ----- 시간 -----
# 한 프레임 delta time 의 상한(초).
# 창을 드래그하거나 잠시 멈춘 뒤 큰 dt 가 들어와 로직이 튀는 것을 막는다.
MAX_DELTA_TIME = 0.1
VSYNC = True

# ----- 색상 (R, G, B) -----
COLOR_BACKGROUND = (24, 20, 32)
COLOR_GRID_LINE = (52, 46, 68)
COLOR_ORIGIN_TILE = (88, 62, 138)
COLOR_MARKER = (232, 196, 92)
COLOR_TEXT = (232, 232, 240)
COLOR_TEXT_DIM = (150, 146, 170)
