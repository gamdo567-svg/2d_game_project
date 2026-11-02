"""게임 전역 설정 값.

현재 수치 대부분은 초기 환경 구성용 임시값이다.
값을 바꾸면 docs/DECISIONS.md 의 관련 항목도 함께 갱신한다.
"""

# ----- 화면 (픽셀) -----
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640

# ----- 칸(타일) -----
TILE_SIZE = 32  # 한 칸이 화면에 그려지는 크기(픽셀)
GRID_COLS = SCREEN_WIDTH // TILE_SIZE  # 30
GRID_ROWS = SCREEN_HEIGHT // TILE_SIZE  # 20

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
