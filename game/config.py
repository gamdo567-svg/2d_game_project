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
TILE_SIZE = 32  # 한 칸이 화면에 그려지는 크기(픽셀)
GRID_COLS = SCREEN_WIDTH // TILE_SIZE  # 32
GRID_ROWS = SCREEN_HEIGHT // TILE_SIZE  # 18

# ----- 플레이어 아트 기준 크기 (렌더링 픽셀) -----
# 실제 스프라이트/애니메이션 제작 전 기준값. 충돌은 논리적 타일 좌표로 처리한다.
PLAYER_SPRITE_WIDTH = 32
PLAYER_SPRITE_HEIGHT = 48

# ----- 플레이어 이동 -----
# [임시값] PRE-PRD 2.1 [제안] 초기값 후보. 실제 플레이 후 조정한다.
PLAYER_MOVE_SPEED = 6.0  # 칸/초 (한 칸 이동 시간 = 1 / 6초)
# 시작 위치 (칸 좌표). 화면 중앙 칸.
PLAYER_START_COL = GRID_COLS // 2
PLAYER_START_ROW = GRID_ROWS // 2

# ----- 플레이어 애니메이션 -----
# 스프라이트 시트: 한 파일에 한 상태·방향의 프레임을 가로로 이어 붙인다.
PLAYER_ANIMATION_FRAMES = 5  # 상태·방향별 프레임 수 (현재 idle, walk 모두 5)
# [임시값] 프레임 하나를 보여 주는 시간(초). 실제 화면을 보며 조정한다.
PLAYER_IDLE_FRAME_DURATION = 0.18
PLAYER_WALK_FRAME_DURATION = 0.1

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
