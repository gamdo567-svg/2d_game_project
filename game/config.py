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
# 걷기: 예전 그림 유지 (2026-11-17 PixelLab 그림 두 가지와 비교한 뒤 사용자 결정: 픽셀 느낌에 더 잘 맞음)
PLAYER_WALK_FRAMES = 4  # 오른발 디딤 → 모음 → 왼발 디딤 → 모음
# [임시값] 프레임 하나를 보여 주는 시간(초). 실제 화면을 보며 조정한다.
PLAYER_IDLE_FRAME_DURATION = 0.2
PLAYER_WALK_FRAME_DURATION = 0.1

# ----- 플레이어 점프 / 패링 -----
# [임시값] 2026-11-10 사용자 승인.
# 패링은 애니메이션 없이 서 있는 그림을 쓴다 (공격 모션을 만들 때 함께 제작).
PLAYER_JUMP_DURATION = 0.7  # 초 (2026-11-17 착지 두 장을 넣으며 0.6 → 0.7, 공중 시간은 거의 그대로)
PLAYER_JUMP_HEIGHT = 1.0  # 칸. 그림만 띄우며 논리적 칸 위치는 그대로 (2026-11-10 높게 뛰도록 0.5 -> 1.0)
PLAYER_PARRY_DURATION = 0.4  # 초. 이 동안 이동 불가
PLAYER_PARRY_WINDOW = 0.15  # 초. 누른 순간부터 막기 판정
# 패링 그림 (2026-11-17 사용자 요청, 측면만): PixelLab 그림을 공격과 같은 96×64 칸 5장으로 (칼 분리).
# 칼을 가슴 쪽으로 당김 → 위로 쳐올림(잔상) → 막기 자세 ×2 → 당김(복귀). 각 장이 끝나는 진행도 (막기 판정 0.15초 안에 막기 자세).
PLAYER_PARRY_FRAME_ENDS = (0.08, 0.18, 0.55, 0.85, 1.0)
# 방향별 칼 위치표 (손 x, 손 y, 각도, 몸 뒤). export_to_game.py 가 뽑은 값. 없는 방향은 서 있는 그림.
PLAYER_PARRY_SWORD = {
    "side": ((57, 28, 108, True), (60, 38, 60, False), (58, 35, 48, False), (58, 35, 48, False), (57, 28, 108, True)),
}
# 점프 그림: 2026-11-17 PixelLab 으로 다시 그림 (사용자 결정: 정면 v7, 측면 v19, 후면 v14, 후드를 잡지 않음).
# 10프레임이 끝나는 진행도: 웅크림 → 깊게 웅크림 → 도약 → 공중 ×4 → 다리 폄 → 착지(깊게 웅크림) → 일어섬.
# 처음 PLAYER_JUMP_TAKEOFF_FRAMES 장이 끝나면 떠오르고, 마지막 PLAYER_JUMP_LANDING_FRAMES 장이 시작될 때 땅에 닿는다.
PLAYER_JUMP_FRAME_ENDS = (0.07, 0.15, 0.26, 0.37, 0.47, 0.57, 0.66, 0.76, 0.88, 1.0)
PLAYER_JUMP_TAKEOFF_FRAMES = 2
PLAYER_JUMP_LANDING_FRAMES = 2
# 점프 그림은 펄럭이는 망토가 잘리지 않게 가로 48, 공중에서 머리가 잘리지 않게 세로 56
PLAYER_JUMP_SPRITE_WIDTH = 48
PLAYER_JUMP_SPRITE_HEIGHT = 56  # 공중에서 머리가 잘리지 않게 위로 8줄 여유 (발 아래 기준으로 그림)
PLAYER_JUMP_FRAMES = len(PLAYER_JUMP_FRAME_ENDS)
# ----- 입력 기억 (조작감) -----
# 공격·점프·패링·회피를 지금 할 수 없는 순간(공격이 끝나기 직전, 경직, 착지 직전 등)에 눌러도
# 이 시간 동안 기억했다가 할 수 있게 되는 순간 실행한다. 2026-11-17 사용자 결정.
PLAYER_INPUT_BUFFER_TIME = 0.15  # 초

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
# 측면 공격: 2026-11-17 PixelLab 으로 다시 그림. 타마다 8프레임을 같은 간격으로 재생한다 (사용자 결정).
# 마지막 프레임은 마무리 자세이며, 다음 타로 이어질 때는 건너뛴다.
PLAYER_ATTACK_HITS = 3
PLAYER_ATTACK_FRAMES = 8
# 초, 타별. 2026-11-17 사용자 요청: 새 그림 기준 1.5배 느리게 (0.45, 0.45, 0.6) → 3타만 다시 1.2배 빠르게 0.9 → 0.75
PLAYER_ATTACK_DURATIONS = (0.675, 0.675, 0.75)
# 타별 프레임이 끝나는 진행도: 같은 간격 (선딜 = 판정 프레임 번호 / 8 × 한 타 시간)
PLAYER_ATTACK_FRAME_ENDS = tuple(
    tuple((i + 1) / PLAYER_ATTACK_FRAMES for i in range(PLAYER_ATTACK_FRAMES)) for _ in range(PLAYER_ATTACK_HITS)
)
# 타별·프레임별로 그림을 옮기는 양 (원본 픽셀, (앞쪽 +, 위쪽 +)). 칸 위치는 바뀌지 않는다.
# 모든 방향 그림에 몸 이동이 들어 있어 모두 0. 연출이 더 필요하면 여기서 조정한다.
PLAYER_ATTACK_FRAME_SHIFTS = tuple(((0, 0),) * PLAYER_ATTACK_FRAMES for _ in range(PLAYER_ATTACK_HITS))
# 공격 중에 클릭해 두면 이어지고, 한 타가 끝난 뒤 이 시간(초) 안에 클릭해도 다음 타로 이어진다.
PLAYER_ATTACK_COMBO_WINDOW = 0.3
# 걷는 중에 공격하면 걷던 칸을 이 시간(초) 안에 마저 가서 칸에 선 뒤 공격한다 (2026-11-17 사용자 결정: 미끄러지며 공격하지 않게)
PLAYER_ATTACK_STEP_FINISH_TIME = 0.05
# 공격 판정 (2026-11-17 사용자 결정, D-024): 칸 단위, 바라보는 방향으로 타별 칸 수, 휘두르는 프레임에 들어설 때 한 번.
PLAYER_ATTACK_REACH = (1, 1, 2)  # 1·2타 앞 1칸, 3타(찌르기) 앞 2칸
# 가로 칸 수 (2026-11-17 사용자 결정): 1·2타는 앞 1칸 × 가로 3칸, 3타는 앞 2칸 × 가로 1칸
PLAYER_ATTACK_WIDTH = (3, 3, 1)
# 판정 프레임 (0부터, 측면 8프레임 기준): 1타 ⑤ 내려벤 순간, 2타 ③ 아래에서 쳐올림, 3타 ⑤ 찌른 순간.
# 선딜: 1타 4/8 × 0.675 ≈ 0.34초, 2타 2/8 × 0.675 ≈ 0.17초, 3타 4/8 × 0.75 = 0.375초
PLAYER_ATTACK_HIT_FRAMES = (4, 2, 4)
PLAYER_ATTACK_DAMAGE = (10, 12, 20)  # [임시값] 타별 피해량
PLAYER_ATTACK_COOLDOWN = 1.0  # 초. 3타가 끝난 뒤 공격만 막는다 (이동·점프·패링은 가능)
# 공격 그림은 검과 찌르기가 몸 밖으로 나가므로 96×64 캔버스를 쓴다 (몸은 Idle 과 같은 32×48 크기, 가로 가운데).
PLAYER_ATTACK_SPRITE_WIDTH = 96
PLAYER_ATTACK_SPRITE_HEIGHT = 64
PLAYER_ATTACK_FOOT_MARGIN = 8  # 캔버스 맨 아래 줄과 발끝 사이의 빈 줄 수 (원본 픽셀)
# 칼은 몸 그림과 따로, 칼 그림 한 장을 위치·각도만 바꿔 겹쳐 그린다 (PRE-PRD 2.6 장비 분리, 무기 교체 가능).
# 타별·프레임별 (손 x, 손 y, 각도, 몸 뒤에 그리기). 손은 96×64 공격 캔버스의 픽셀(왼쪽 위 원점, y 아래로),
# 각도는 칼끝 방향(도, 오른쪽 0 / 위 90). 오른쪽을 볼 때 기준이며 왼쪽은 좌우 반전한다.
# 2026-11-17 PixelLab 측면 그림에서 export_to_game.py 가 뽑은 값 (assets/concepts/pixellab/player_import).
PLAYER_ATTACK_SWORD = (
    ((62, 37, 24, False), (61, 41, -22, False), (37, 27, 125, False), (39, 27, 127, False),
     (69, 46, -40, False), (69, 46, -33, False), (69, 46, -27, False), (67, 44, -30, False)),
    ((38, 41, -162, False), (39, 42, -164, False), (70, 38, -65, False), (54, 22, 110, True),
     (51, 16, 155, True), (51, 17, 155, True), (51, 19, 135, True), (51, 19, 135, True)),
    ((48, 40, 179, False), (40, 38, -180, False), (39, 38, 180, False), (41, 38, -179, False),
     (64, 36, 0, False), (64, 36, 0, False), (64, 36, 0, False), (65, 36, 0, False)),
)
# 정면(아래를 볼 때) 칼 위치표. 1·2·3타 모두 2026-11-17 PixelLab 그림(8프레임, export_to_game.py 가 뽑은 값.
# 2타 v9 와 3타 찌르기는 시작·끝 자세를 지정해 만듦). 다섯 번째 값은 칼 길이 비율:
# 3타는 칼이 보는 사람 쪽으로 기울어 짧아 보이게 그린다. 찌르는 6~8번째는 무기의 찌르기용 칼 그림
# (PLAYER_WEAPON_VIEW_ART)을 쓰고, 그 그림이 없는 무기는 이 표대로 옆모습 칼을 짧게 그린다. 후면은 보류 (사용자 결정).
PLAYER_ATTACK_SWORD_FRONT = (
    ((40, 37, 137, False), (45, 34, 126, False), (61, 32, 117, True), (66, 28, 113, False),
     (64, 38, -40, False), (50, 41, -146, False), (39, 43, -138, False), (38, 41, -135, False)),
    ((40, 45, -129, False), (40, 43, -131, False), (39, 44, -132, False), (39, 44, -132, False),
     (58, 27, 62, False), (61, 26, 140, True), (63, 27, 142, True), (61, 27, 139, True)),
    ((39, 36, -129, False, 0.6), (38, 32, -52, False, 0.6), (38, 31, -55, False, 0.6), (39, 31, -59, False, 0.6),
     (40, 31, -61, False, 0.6), (48, 30, -90, False, 0.55), (48, 30, -90, False, 0.55), (48, 30, -90, False, 0.55)),
)
# 정면 타별 프레임 표와 그림 옮김 (같은 진행도에서 고른다). None = 측면과 같은 8프레임 같은 간격.
# 정면 1·2타는 크게 휘두르는 그림이 측면보다 늦게 나와(1타 6번째, 2타 5번째) 판정 시점에 그 그림이 시작되도록
# 준비 프레임을 빨리 넘긴다 (2026-11-17 사용자 지적: 정면 1타가 측면보다 느려 보임). 3타는 찌르는 6번째가 0.5 에.
PLAYER_ATTACK_FRAME_ENDS_FRONT = (
    (0.1, 0.2, 0.3, 0.4, 0.5, 0.62, 0.81, 1.0),     # 1타: 들어 올림(빠르게) → 0.5 에 크게 내려벰
    (0.06, 0.12, 0.19, 0.25, 0.4, 0.6, 0.8, 1.0),   # 2타: 칼 내림(빠르게) → 0.25 에 크게 쳐올림 → 어깨 위
    # 3타: 칼 당김(길게) → 2~4번째는 거의 같은 자세라 빨리 넘김 → 찌르기 직전 → 0.5 에 두 손으로 찌름 → 멈춤
    # (2026-11-17 사용자 지적: 같은 간격이면 찌르기 직전에 약 0.22초 멈칫해 보임)
    (0.18, 0.25, 0.29, 0.33, 0.5, 0.7, 0.85, 1.0),
)
PLAYER_ATTACK_FRAME_SHIFTS_FRONT = (
    ((0, 0),) * 8,
    ((0, 0),) * 8,
    ((0, -6),) * 8,  # 3타: 발 아래로 길게 내민 칼이 잘리지 않게 시트에 6픽셀 올려 담은 것을 되돌림
)
# 후면(위를 볼 때) 칼 위치표: 그림이 없어 모두 None → 위를 볼 때는 측면 그림을 쓴다.
PLAYER_ATTACK_SWORD_BACK = (None, None, None)
# 두 손 잡기: 게임은 몸 → 칼 → 손 레이어(sword_attack/<방향>_N_hand.png) 순서로 그려 손이 칼을 쥔 모습이 된다.
# 칼이 몸 뒤인 프레임(네 번째 값 True)은 칼 → 몸 순서로 그린다 (2타에서 칼을 머리 뒤로 넘길 때).
# 칼 그림: assets/images/player/weapons/<무기>.png 한 장. 칼끝이 오른쪽(0도)을 향하고,
# 손(손잡이를 쥔 곳)이 그림 한가운데에 있다 → 그림 중심을 손에 두고 돌리면 된다.
PLAYER_SWORD_SPRITE_WIDTH = 56
PLAYER_SWORD_SPRITE_HEIGHT = 10
PLAYER_WEAPON = "old_sword"  # 시작 장비: 낡은 검
# 찌르기용 칼 그림을 쓰는 프레임 (2026-11-17 사용자 결정): (방향, 타 번호) → 프레임 번호(0부터).
# 보는 사람 쪽으로 튀어나오는 칼은 옆모습 칼 한 장을 돌려서는 그릴 수 없어 무기마다 그림을 따로 둔다:
# weapons/<무기>_<방향>_<타>.png (공격 시트와 같은 96×64 칸, 몸 위에 그대로 겹침). 칼을 바꾸면 이 그림도 바뀐다.
PLAYER_WEAPON_VIEW_ART = {("front", 3): (5, 6, 7)}

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
# [임시값] 2026-11-17 사용자 결정 (패턴 4종) + Claude 제안 수치. 1×2칸을 차지한다 (2026-11-17 사용자 요청으로 2×2 → 3×3 → 1×2). 그림은 팔·다리를 나눈 임시 도형.
GOLEM_MAX_HP = 300
GOLEM_BODY = (1, 2)  # (가로, 세로) 칸. 맞는 칸·지나갈 수 없는 칸·이동. 2026-11-17 사용자 요청: 2×2 → 3×3 → 1×2 (발 칸과 그 위 한 칸)
GOLEM_MOVE_SPEED = 1.5  # 칸/초
GOLEM_REST_TIME = 1.5  # 초. 공격이 끝나고 다음 행동까지 쉼
GOLEM_RECOVER_TIME = 0.6  # 초. 공격이 터진 뒤 자세를 되돌리는 시간 (때리기 좋은 틈)
GOLEM_NEAR = 2  # 칸. 이 거리 안이면 ①·②·③ 중 하나 (2026-11-17 사용자 요청으로 ② 추가)
GOLEM_MID = 5  # 칸. 이 거리 안이면 ② 또는 다가감, 더 멀면 ④ 또는 다가감
GOLEM_KICK_CHANCE = 0.5  # 중간 거리에서 ② 를 쓸 확률 (나머지는 다가감)
# ④ 레이저를 패턴으로 고를지. 2026-11-17 사용자 요청: 시험을 위해 잠시 뺌 (나중에 다시 넣음, 코드는 그대로)
GOLEM_LASER_ENABLED = False
GOLEM_LASER_CHANCE = 0.5  # 멀 때 ④ 를 쓸 확률 (쓸 수 있을 때만, 나머지는 다가감)
GOLEM_LASER_COOLDOWN = 8.0  # 초. ④ 를 쓰고 나서 다시 쓸 수 있을 때까지 (레이저만 쏘며 제자리에 있지 않게)
GOLEM_RESPAWN_TIME = 3.0  # 초. 죽으면 이 시간 뒤 처음 자리에 다시 나타남
GOLEM_HIT_FLASH_TIME = 0.1
# 골렘 그림 (2026-11-17, PixelLab 생성 그림 assets/images/golem/<south|north|east|west>.png, 원본 96×96, 투명 배경).
# 판정·충돌은 몸 칸(1×2) 그대로이고 그림은 RENDER_SCALE 로 nearest 확대해 칸보다 크게(위·양옆으로 넘쳐) 그린다.
# 발 밑(가장 아래 불투명 줄)을 몸 바닥(발 칸) 가운데에 맞추기 위해, 방향별로 그림 아래 투명 줄 수를 적어 둔다.
GOLEM_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "golem"
GOLEM_SPRITE_SIZE = 96  # 원본 픽셀
GOLEM_SPRITE_FOOT_MARGIN = {"south": 7, "north": 6, "east": 5, "west": 5}  # 발 밑 아래 투명 줄 수 (원본 픽셀)
GOLEM_SPRITE_HEAD_ROW = 5  # 그림 위쪽 투명 줄 수 (머리 꼭대기, 체력 막대를 그 위에 둔다)
# ③ 발 구르기 동작 그림 (2026-11-17, PixelLab, assets/images/golem/stomp_<방향>.png). 가로 한 줄 19장, 한 장 176×152.
#   구간: 들기 0~6, 위 7, 떨어짐 8, 착지 9, 반동·일어섬 10~18 (12 는 착지와 같은 그림이라 쓰지 않음).
#   모든 장의 발 밑 가운데가 foot (그림 왼쪽 위 기준 픽셀) 에 맞춰져 있다 (align_stomp_frames.py).
#   예고(windup) 동안: 무릎을 들고 → 위에서 잠깐 멈췄다가 → 마지막 순간 한 장 만에 떨어짐.
#   자세 되돌림(recover) 동안: 착지 그림을 잠깐 붙잡고(멈칫) 옆으로 눌렸다가(squash) 반동하며 일어섬.
#   *_ends 는 각 그림이 끝나는 진행도 (0~1, 마지막 1.0). 2026-11-17 사용자 확인 (C 버전 + 미리보기 B 타이밍).
# 걷기 그림 (2026-11-17, PixelLab skeleton-v3 walking-8-frames, assets/images/golem/walk_<방향>.png).
#   가로 한 줄 8장, 한 장 128×128, 발 밑 가운데 foot. 걸은 거리로 그림을 고른다: 8장 한 주기에 tiles_per_cycle 칸
#   (발이 바닥에서 미끄러지지 않게). 멈춰 있으면 서 있는 그림.
GOLEM_WALK_ANIM = {"frame_size": (128, 128), "foot": (64, 118), "frames": 8, "tiles_per_cycle": 2.0}
GOLEM_STOMP_ANIM = {
    "frame_size": (176, 152),
    "foot": (88, 140),
    "windup_frames": (0, 1, 2, 3, 4, 5, 6, 7, 8),
    "windup_ends": (0.09, 0.18, 0.27, 0.36, 0.45, 0.55, 0.64, 0.91, 1.0),
    "recover_frames": (9, 10, 11, 13, 14, 15, 16, 17, 18),
    "recover_ends": (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
    "squash": 0.06,       # 착지 순간 옆으로 넓어지고 위아래로 줄어드는 비율
    "squash_until": 0.15,  # 자세 되돌림 진행도가 이만큼 될 때까지 눌림
}
# ① 두 손 내려찍기 동작 그림 (2026-11-17, PixelLab, assets/images/golem/slam_<방향>.png). 가로 한 줄 14장, 한 장 144×176.
#   들기 0~6 (두 주먹을 머리 위로, 발 고정) → 착지 7 (숙여 주먹을 앞 땅에) → 일어섬 8~13. 발 밑 가운데 foot.
#   예고 동안 빠르게 들고 위에서 멈춤, 터진 순간 한 장 만에 착지(사이 장은 PixelLab 섬광이 그려져 있어 쓰지 않음).
#   후면 일어섬은 팔이 먼저 돌아가는 문제가 남아 있다 (2026-11-17 사용자: 시간이 없어 일단 적용).
GOLEM_SLAM_ANIM = {
    "frame_size": (144, 176),
    "foot": (72, 166),
    "windup_frames": (0, 1, 2, 3, 4, 5, 6),
    "windup_ends": (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1.0),
    "recover_frames": (7, 8, 9, 10, 11, 12, 13),
    "recover_ends": (0.25, 0.38, 0.5, 0.63, 0.75, 0.88, 1.0),
    "squash": 0.05,
    "squash_until": 0.12,
}
# 패턴: 예고 시간(초), 피해, 범위. 앞쪽 범위는 (가로 칸 수, 앞으로 칸 수).
# 2026-11-17 사용자 요청: 예고가 길어 걸어서 쉽게 빠져나가서 ① 0.8 → 0.35, ② 0.6 → 0.3, ③ 1.2 → 0.55초
GOLEM_SLAM = {"windup": 0.35, "damage": 20, "width": 3, "depth": 3}  # ① 두 손 모아 내려찍기: 패링 가능
# 2026-11-17 사용자 요청으로 예고 0.3 → 0.6 → 0.55초, 범위 가로 3 → 5 → 4 → 3 (가로 3 × 앞으로 5)
GOLEM_KICK = {"windup": 0.55, "damage": 15, "width": 3, "depth": 5}  # ② 뒤로 들었다 앞차기: 패링 불가, 회피 무적 가능
# 2026-11-17 사용자 요청으로 6×6 → 7×7 → 8×8 → 7×7 (범위 기준이 발 칸이 되어, 발 칸 둘레로 3칸씩 대칭)
GOLEM_STOMP = {"windup": 0.55, "damage": 30, "size": 7}  # ③ 한 발 내려찍기: 발 칸 가운데 7×7 (대칭), 점프로만 피함
# ④ 코어 레이저: 4초 조준(조준점이 발사 순간까지 주인공을 따라옴) 후 조준점에서 4×4 폭발 (벽 칸은 제외).
#   일직선으로 관통하지 않는다 (2026-11-17 사용자 결정). 패링 불가, 회피 무적으로 피함
GOLEM_LASER = {"windup": 4.0, "damage": 40, "beam_time": 0.3, "size": 4}

# ----- 이펙트 (그리기 전용, 판정과 무관) -----
# 스프라이트 시트: frame_size × frame_size 원본 프레임을 columns 개씩 줄지어 놓은 그림 (왼쪽 위부터 오른쪽으로).
# 프레임 가운데가 이펙트가 터지는 지점이고, RENDER_SCALE 로 nearest 확대해 그린다.
EFFECT_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "effects"
# 화면 흔들림: 카메라에 더하는 화면 픽셀 오프셋. amplitude(픽셀)에서 duration(초) 동안 0 으로 줄고 frequency(번/초)로 떨림
# ③ 발 구르기 (2026-11-17 사용자 요청): 바닥이 거미줄로 갈라지고 둘레 바닥 판이 솟았다 가라앉으며 돌이 튐, 화면 흔들림.
#   생성 스크립트: assets/concepts/vfx/stomp/build_golem_stomp.py (288×288, 30프레임, 12fps = 2.5초)
GOLEM_STOMP_EFFECT = {
    "path": EFFECT_IMAGE_DIR / "golem_stomp.png",
    "frame_size": 288,
    "columns": 6,
    "frames": 30,
    "fps": 12,
    "shake": {"amplitude": 8, "duration": 0.45, "frequency": 18},
    # 화면에 그리는 크기(칸). 없으면 frame_size × RENDER_SCALE. ③ 범위(7×7)에 맞춘다 (2026-11-17 사용자 요청)
    "draw_tiles": GOLEM_STOMP["size"],
}
# 패링 성공 이펙트 (2026-11-17 사용자 요청: 노란 성공 파티클). 흰 십자 섬광 → 노란 고리 → 불꽃이 튀며 식음.
# on_top: 인물 위에 그린다. 터지는 점은 주인공 칸에서 바라보는 쪽으로 PARRY_SPARK_OFFSET (앞으로, 위로) 칸.
PARRY_SPARK_EFFECT = {
    "path": EFFECT_IMAGE_DIR / "parry_spark.png",
    "frame_size": 64,
    "columns": 9,
    "frames": 9,
    "fps": 24,
    "on_top": True,
}
PARRY_SPARK_OFFSET = (0.6, 1.0)
# ① 내려찍기 충격 (2026-11-17 사용자 요청): 짧은 금·튀는 돌 파편·먼지, 약한 흔들림. 앞 범위 칸들의 가운데에서.
#   생성 스크립트: assets/concepts/vfx/slam/build_golem_slam_impact.py (160×160, 16프레임, 12fps)
GOLEM_SLAM_EFFECT = {
    "path": EFFECT_IMAGE_DIR / "golem_slam.png",
    "frame_size": 160,
    "columns": 8,
    "frames": 16,
    "fps": 12,
    "shake": {"amplitude": 4, "duration": 0.25, "frequency": 20},
}

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
