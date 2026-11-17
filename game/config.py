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

# ----- 맵 -----
# 글자 맵 파일 (D-023): # 벽, . 바닥, P 주인공 시작 칸. 크기는 GRID_COLS × GRID_ROWS 와 같아야 한다.
MAP_DIR = PROJECT_ROOT / "assets" / "maps"
FIELD_MAP_PATH = MAP_DIR / "test_room.txt"

# ----- 플레이어 그림 크기 -----
# 스프라이트 시트 원본 프레임 크기 (에셋 픽셀). 충돌은 논리적 칸 좌표로 처리한다.
PLAYER_SPRITE_WIDTH = 32
PLAYER_SPRITE_HEIGHT = 48
# 화면에 그리는 크기 (렌더링 픽셀) = 원본 × RENDER_SCALE
PLAYER_RENDER_WIDTH = PLAYER_SPRITE_WIDTH * RENDER_SCALE  # 64
PLAYER_RENDER_HEIGHT = PLAYER_SPRITE_HEIGHT * RENDER_SCALE  # 96

# ----- 플레이어 이동 -----
# [임시값] PRE-PRD 2.1 [제안] 초기값 후보. 실제 플레이 후 조정한다.
PLAYER_MOVE_SPEED = 4.0  # 칸/초 (한 칸 이동 시간 = 0.25초). 2026-11-17 사용자 요청으로 6 → 4 (골렘 예고 중 걸어서 쉽게 빠져나가서)
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
# [임시값] 2026-11-10 사용자 승인.
# 패링은 애니메이션 없이 서 있는 그림을 쓴다 (공격 모션을 만들 때 함께 제작).
PLAYER_JUMP_DURATION = 0.6  # 초
PLAYER_JUMP_HEIGHT = 1.0  # 칸. 그림만 띄우며 논리적 칸 위치는 그대로 (2026-11-10 높게 뛰도록 0.5 -> 1.0)
PLAYER_PARRY_DURATION = 0.4  # 초. 이 동안 이동 불가
PLAYER_PARRY_WINDOW = 0.15  # 초. 누른 순간부터 막기 판정
# 점프 5프레임이 끝나는 진행도: 웅크림 ~15%, 도약 ~30%, 무릎을 상반신까지 당김 ~68%(최고점 포함),
# 다리 펴며 착지 준비 ~85%, 착지 ~100%. 웅크림이 끝나면 떠오르고 착지 프레임이 시작될 때 땅에 닿는다.
PLAYER_JUMP_FRAME_ENDS = (0.15, 0.3, 0.68, 0.85, 1.0)
PLAYER_JUMP_FRAMES = len(PLAYER_JUMP_FRAME_ENDS)
# ----- 플레이어 회피 -----
# [임시값] 2026-11-17 사용자 결정: Q, 누르고 있는 방향(없으면 바라보는 방향)으로 3칸을 0.25초에, 회피 중 내내 무적,
# 끝난 뒤 1초 동안 다시 쓸 수 없음. 도중에 벽·허수아비가 있으면 그 앞에서 멈춘다. 그림은 걷기 그림.
# (처음 5칸·0.25초 → 3칸·0.5초 → 느려서 3칸·0.25초. 모두 같은 날 사용자 요청)
PLAYER_DODGE_DISTANCE = 2  # 칸 (2026-11-17 사용자 요청으로 3 → 2)
PLAYER_DODGE_DURATION = 0.25  # 초
PLAYER_DODGE_COOLDOWN = 8.0  # 초 (회피가 끝난 뒤부터). 2026-11-17 사용자 요청으로 1 → 8
# 퍼펙트 회피 (2026-11-17 사용자 결정): 노란색 공격(패링 불가·회피 가능)이 터지기 이 시간 안에 그 범위 안에서 회피를 시작했으면
# 성공 → 회피 대기 시간을 없앤다. 타이밍은 넉넉하게.
PLAYER_PERFECT_DODGE_WINDOW = 0.4  # 초
PLAYER_PERFECT_TEXT_TIME = 0.6  # 초. 머리 위 "PERFECT" 표시

# ----- 플레이어 공격 (검 3단 콤보) -----
# [임시값] 2026-11-16 사용자 결정: 마우스 왼쪽 클릭, 제자리 공격, 공격 중 이동 불가,
# 3단 콤보(1타 사선 내려베기, 2타 올려베기, 3타 찌르기), 3타 후 약 1초 동안 공격 불가. 공격 판정은 몬스터 개발 때.
# 타마다 5프레임. 마지막 프레임은 복귀(서 있는 자세 + 검)이며, 다음 타로 이어질 때는 건너뛴다.
PLAYER_ATTACK_HITS = 3
PLAYER_ATTACK_FRAMES = 5
PLAYER_ATTACK_DURATIONS = (0.45, 0.45, 0.6)  # 초, 타별
# 타별 프레임이 끝나는 진행도. 준비는 길게, 휘두르는 순간(잔상 프레임)은 짧게, 벤·찌른 자세는 잠깐 멈춘다.
PLAYER_ATTACK_FRAME_ENDS = (
    (0.25, 0.4, 0.6, 0.8, 1.0),     # 1타: 준비 → 내디딤 → 런지 베기(잔상) → 마무리 → 복귀
    (0.15, 0.32, 0.55, 0.85, 1.0),  # 2타: 아래에서 휘두름(잔상) → 위로 치켜 올림(잔상) → 머리 위로 뻗음 → 멈춤 → 복귀
    (0.2, 0.37, 0.5, 0.85, 1.0),    # 3타: 몸을 뒤로 빼며 당김 → 더 당김 → 찌름(순간, 속도선) → 멈춤 → 복귀
)
# 타별·프레임별로 그림을 옮기는 양 (원본 픽셀, (앞쪽 +, 위쪽 +)). 칸 위치는 바뀌지 않는다.
# 2026-11-16 ChatGPT 참고 시트 그림은 몸 이동이 그림에 들어 있어 모두 0. 연출이 더 필요하면 여기서 조정한다.
PLAYER_ATTACK_FRAME_SHIFTS = tuple(((0, 0),) * PLAYER_ATTACK_FRAMES for _ in range(PLAYER_ATTACK_HITS))
# 정면(아래를 볼 때) 내딛기 연출: 베고 찌르는 순간 그림을 화면 아래(공격 방향)로 옮긴다. (가로 +, 위 +) 원본 픽셀.
# 정면 그림은 몸이 앞으로 나가는 움직임이 잘 안 보여서 2026-11-17 추가. 칸 위치는 그대로.
PLAYER_ATTACK_FRAME_SHIFTS_FRONT = (
    ((0, 1), (0, 1), (0, -1), (0, -3), (0, 0)),   # 1타: 치켜들며 살짝 뒤로 → 내려베며 앞으로
    ((0, 0), (0, 1), (0, 2), (0, 1), (0, 0)),     # 2타: 올려치며 몸이 위로 솟음
    ((0, 1), (0, 2), (0, -3), (0, -4), (0, 0)),   # 3타: 뒤로 당겼다가 아래로 깊게 찌름
)
# 공격 중에 클릭해 두면 이어지고, 한 타가 끝난 뒤 이 시간(초) 안에 클릭해도 다음 타로 이어진다.
PLAYER_ATTACK_COMBO_WINDOW = 0.3
# 공격 판정 (2026-11-17 사용자 결정, D-024): 칸 단위, 바라보는 방향으로 타별 칸 수, 휘두르는 프레임에 들어설 때 한 번.
PLAYER_ATTACK_REACH = (1, 1, 2)  # 1·2타 앞 1칸, 3타(찌르기) 앞 2칸
PLAYER_ATTACK_HIT_FRAMES = (2, 1, 2)  # 판정 프레임 (0부터): 1타 ③ 베기, 2타 ② 올려침, 3타 ③ 찌름
PLAYER_ATTACK_DAMAGE = (10, 12, 20)  # [임시값] 타별 피해량
PLAYER_ATTACK_COOLDOWN = 1.0  # 초. 3타가 끝난 뒤 공격만 막는다 (이동·점프·패링은 가능)
# 공격 그림은 검과 찌르기가 몸 밖으로 나가므로 96×64 캔버스를 쓴다 (몸은 Idle 과 같은 32×48 크기, 가로 가운데).
PLAYER_ATTACK_SPRITE_WIDTH = 96
PLAYER_ATTACK_SPRITE_HEIGHT = 64
PLAYER_ATTACK_FOOT_MARGIN = 8  # 캔버스 맨 아래 줄과 발끝 사이의 빈 줄 수 (원본 픽셀)
# 칼은 몸 그림과 따로, 칼 그림 한 장을 위치·각도만 바꿔 겹쳐 그린다 (PRE-PRD 2.6 장비 분리, 무기 교체 가능).
# 타별·프레임별 (손 x, 손 y, 각도, 몸 뒤에 그리기). 손은 96×64 공격 캔버스의 픽셀(왼쪽 위 원점, y 아래로),
# 각도는 칼끝 방향(도, 오른쪽 0 / 위 90). 오른쪽을 볼 때 기준이며 왼쪽은 좌우 반전한다.
PLAYER_ATTACK_SWORD = (
    ((32, 19, 66, False), (45, 13, 148, False), (62, 42, -45, False), (62, 47, -29, False), (49, 42, -60, False)),
    ((41, 44, -130, False), (61, 31, 51, False), (54, 14, 57, False), (62, 23, 57, False), (49, 42, -60, False)),
    ((36, 40, 180, False), (38, 40, -179, False), (69, 38, 0, False), (69, 38, -1, False), (49, 42, -60, False)),
)
# 정면(아래를 볼 때) 칼 위치표 (build_attack_view.py 가 참고 시트 front_v1 에서 뽑음). 다섯 번째 값은 칼 길이 비율:
# 화면 아래쪽(보는 사람 쪽)으로 찌르는 칼은 원근으로 짧아 보이게 그린다.
PLAYER_ATTACK_SWORD_FRONT = (
    ((37, 26, 59, False, 0.78), (42, 17, 125, False, 0.57), (60, 48, -54, False, 0.67), (54, 52, -39, False, 0.59), (39, 41, -100, False, 0.7)),
    ((39, 51, -135, False, 0.62), (41, 24, 131, False, 0.67), (53, 16, 84, False, 0.56), (53, 24, 58, False, 0.69), (39, 41, -100, False, 0.7)),
    ((37, 35, -90, False, 0.88), (37, 38, -91, False, 0.8), (55, 41, -90, False, 1.0), (55, 49, -90, False, 0.89), (39, 41, -100, False, 0.7)),
)
# 2026-11-17 두 손 잡기: 참고 시트 v2(칼 = 파란 단색)에서 build_attack_v3.py 가 자동으로 뽑은 값 (손 = 오른손, 가드 바로 아래).
# (8칸 시트 v3 를 build_attack_v4.py 로 시험했으나 사용자 판단으로 v2 유지: 덜 역동적이고 프레임이 많아 빨라 보임)
# 게임은 몸 → 칼 → 오른손 레이어(sword_attack/side_N_hand.png) 순서로 그려 오른손이 칼 앞, 왼손이 칼 뒤에 보인다.
# 칼 그림: assets/images/player/weapons/<무기>.png 한 장. 칼끝이 오른쪽(0도)을 향하고,
# 손(손잡이를 쥔 곳)이 그림 한가운데에 있다 → 그림 중심을 손에 두고 돌리면 된다.
PLAYER_SWORD_SPRITE_WIDTH = 56
PLAYER_SWORD_SPRITE_HEIGHT = 10
PLAYER_WEAPON = "old_sword"  # 시작 장비: 낡은 검
# 지금은 오른쪽 측면 그림만 있다. 다른 방향도 이 그림을 쓰고 왼쪽은 좌우 반전한다 (임시).

# ----- 연습용 허수아비 (공격 판정 확인용) -----
# [임시값] 2026-11-17. 맞으면 깜빡임·흔들림·피해 숫자, 체력이 다하면 쓰러졌다가 다시 선다.
DUMMY_MAX_HP = 60
DUMMY_FLASH_TIME = 0.12  # 초. 하얗게 깜빡이는 시간
DUMMY_SHAKE_TIME = 0.15  # 초. 맞은 방향으로 밀렸다 돌아오는 시간
DUMMY_SHAKE_PIXELS = 3  # 원본 픽셀. 처음 밀리는 거리 (칸 위치는 그대로)
DUMMY_DOWN_TIME = 2.0  # 초. 쓰러져 있는 시간
DAMAGE_POPUP_TIME = 0.6  # 초. 피해 숫자가 떠 있는 시간
DAMAGE_POPUP_RISE = 0.5  # 칸. 그동안 떠오르는 높이

# ----- 주인공 체력·피격 -----
# [임시값] 2026-11-17 사용자 결정: 체력 100, 맞으면 짧게 경직 + 깜빡임. 체력이 0 이 되면 (사망은 기획 미정) 그 자리에서 다시 채운다.
PLAYER_MAX_HP = 100
PLAYER_HURT_TIME = 0.3  # 초. 맞았을 때 경직
PLAYER_HIT_FLASH_TIME = 0.15  # 초

# ----- 패링 게이지 (PRE-PRD 2.2, 2026-11-17 사용자 결정) -----
POSTURE_PARRIED_GAIN = 0.25  # 패링당하면 전체의 25% 참
POSTURE_PARRY_RELIEF = 0.5  # 패링에 성공하면 50% 줄어듦 (패링당해 차는 양의 2배)
POSTURE_DECAY_PER_SECOND = 0.05  # [임시값] 시간이 지나면 초당 5%씩 줄어듦
POSTURE_STUN_TIME = 2.0  # 초. 가득 차면 기절

# ----- 골렘 (첫 일반 몬스터, 몬스터형: 경직 없음) -----
# [임시값] 2026-11-17 사용자 결정 (패턴 4종) + Claude 제안 수치. 2×2칸을 차지한다. 그림은 팔·다리를 나눈 임시 도형.
GOLEM_MAX_HP = 300
GOLEM_SIZE = 2  # 칸 (정사각형)
GOLEM_MOVE_SPEED = 1.5  # 칸/초
GOLEM_REST_TIME = 1.5  # 초. 공격이 끝나고 다음 행동까지 쉼
GOLEM_RECOVER_TIME = 0.6  # 초. 공격이 터진 뒤 자세를 되돌리는 시간 (때리기 좋은 틈)
GOLEM_NEAR = 2  # 칸. 이 거리 안이면 ①·②·③ 중 하나 (2026-11-17 사용자 요청으로 ② 추가)
GOLEM_MID = 5  # 칸. 이 거리 안이면 ② 또는 다가감, 더 멀면 ④ 또는 다가감
GOLEM_KICK_CHANCE = 0.5  # 중간 거리에서 ② 를 쓸 확률 (나머지는 다가감)
GOLEM_LASER_CHANCE = 0.5  # 멀 때 ④ 를 쓸 확률 (쓸 수 있을 때만, 나머지는 다가감)
GOLEM_LASER_COOLDOWN = 8.0  # 초. ④ 를 쓰고 나서 다시 쓸 수 있을 때까지 (레이저만 쏘며 제자리에 있지 않게)
GOLEM_RESPAWN_TIME = 3.0  # 초. 죽으면 이 시간 뒤 처음 자리에 다시 나타남
GOLEM_HIT_FLASH_TIME = 0.1
# 패턴: 예고 시간(초), 피해, 범위. 앞쪽 범위는 (가로 칸 수, 앞으로 칸 수).
# 2026-11-17 사용자 요청: 예고가 길어 걸어서 쉽게 빠져나가서 ① 0.8 → 0.35, ② 0.6 → 0.3, ③ 1.2 → 0.55초
GOLEM_SLAM = {"windup": 0.35, "damage": 20, "width": 3, "depth": 3}  # ① 두 손 모아 내려찍기: 패링 가능
GOLEM_KICK = {"windup": 0.6, "damage": 15, "width": 3, "depth": 5}  # 2026-11-17 사용자 요청으로 예고 0.3 → 0.6초  # ② 뒤로 들었다 앞차기: 패링 불가, 회피 무적 가능
GOLEM_STOMP = {"windup": 0.55, "damage": 30, "size": 6}  # ③ 한 발 내려찍기: 중심 6×6, 점프로만 피함
# ④ 코어 레이저: 4초 조준(조준점이 발사 순간까지 주인공을 따라옴) 후 조준점에서 4×4 폭발 (벽 칸은 제외).
#   일직선으로 관통하지 않는다 (2026-11-17 사용자 결정). 패링 불가, 회피 무적으로 피함
GOLEM_LASER = {"windup": 4.0, "damage": 40, "beam_time": 0.3, "size": 4}

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
# 벽 칸 임시 표시 (타일 그림이 생기기 전). 안쪽 면과 테두리.
COLOR_WALL = (64, 54, 78)
COLOR_WALL_EDGE = (40, 34, 52)
COLOR_WHITE = (255, 255, 255)
# 허수아비 임시 도형 색
COLOR_DUMMY_WOOD = (120, 84, 52)
COLOR_DUMMY_STRAW = (196, 164, 96)
COLOR_DUMMY_SHADOW = (20, 16, 26)
COLOR_DUMMY_HP = (200, 70, 60)
COLOR_DAMAGE_TEXT = (255, 236, 160)
# 골렘 임시 도형·공격 예고 색
COLOR_GOLEM_BODY = (98, 92, 104)
COLOR_GOLEM_LIMB = (78, 72, 86)
COLOR_GOLEM_EDGE = (44, 40, 52)
COLOR_GOLEM_CORE = (90, 200, 220)
COLOR_GOLEM_CORE_HOT = (255, 120, 90)
# 공격 예고 칸(히트박스) 색: 공격 종류별로 (처음 색, 터지기 직전 색). 2026-11-17 사용자 결정.
COLOR_WARN = {
    "parryable": ((90, 36, 44), (215, 50, 50)),  # 패링 가능한 일반 공격: 빨강
    "unparryable": ((92, 82, 30), (235, 205, 50)),  # 패링 불가 (회피로 피함): 노랑
    "jump_only": ((30, 72, 92), (100, 205, 245)),  # 점프로만 피함: 하늘색
}
COLOR_POSTURE = (230, 200, 90)
COLOR_PLAYER_HP = (90, 200, 110)
COLOR_BAR_BACK = (30, 26, 38)
COLOR_TEXT = (232, 232, 240)
COLOR_TEXT_DIM = (150, 146, 170)
