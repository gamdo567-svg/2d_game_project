# assets

게임 에셋(픽셀풍 2D 그래픽, 사운드, 폰트)을 보관하는 폴더입니다.

| 폴더 | 용도 |
|---|---|
| `images/` | 스프라이트, 타일셋, UI 이미지 (PNG 권장) |
| `sounds/` | 효과음(WAV), 배경음(OGG/MP3) |
| `fonts/` | 게임에서 사용하는 폰트 파일 |

## 규칙

- 외부 에셋을 추가할 때는 아래 **출처 및 라이선스** 표에 반드시 기록합니다.
- 라이선스가 불분명한 에셋은 커밋하지 않습니다.
- 에셋 추가 커밋은 `assets:` 형식을 사용합니다. 예: `assets: 플레이어 대기 스프라이트 추가`
- 파일 이름은 영문 소문자와 밑줄을 사용합니다. 예: `player_idle.png`

## 출처 및 라이선스

| 파일 | 제작자/출처 | 라이선스 | 비고 |
|---|---|---|---|
| `concepts/player_character_concept_v1.png` | 사용자 제공 (주인공 공식 컨셉 시트) | 사용자 소유 | PRE-PRD 2.6 기준 디자인 |
| `concepts/player_body_animation_reference.png` | 사용자 제공 (주인공 애니메이션 참고 시트, 7상태 × 3방향) | 사용자 소유 | 게임에 직접 쓰지 않는 참고 이미지 |
| `concepts/player_idle_reference_v3.png` | 사용자 제공 (주인공 Idle 참고 시트 v3, 3방향 × 4프레임, 초록 배경) | 사용자 소유 | 게임에 직접 쓰지 않는 참고 이미지 |
| `concepts/player_walk_reference_v3.png` | 사용자 제공 (주인공 Walk 참고 시트 v3, 3방향 × 4프레임, 초록 배경) | 사용자 소유 | 게임에 직접 쓰지 않는 참고 이미지 |
| `images/player/{idle,walk}/{front,back,side}.png` | 위 v3 참고 시트 두 장에서 Claude Code가 가공 (2026-11-03) | 사용자 소유 (파생물) | **검증 전 에셋.** 아래 설명 참고 |
| `images/player/jump/{front,back,side,side_left}.png` | v3 Idle 시트에 Claude Code가 팔·다리를 다시 그림 (2026-11-10) | 사용자 소유 (파생물) | **임시 에셋.** 아래 설명 참고 |
| `images/player/shadow.png` | Claude Code 제작 (2026-11-10) | 프로젝트 소유 | 점프 그림자. **임시 에셋** |
| `concepts/pixellab/kit/*` | Claude Code가 게임 스프라이트로 만든 PixelLab 기준 그림과 사용 가이드 (2026-11-11) | 사용자 소유 (파생물) | 게임에 직접 쓰지 않음 |
| `concepts/pixellab/attack1_side_right_B/*` | PixelLab(pixellab.ai) `animate_image_pixminimax` 생성 (2026-11-16) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 공격 1타 움직임 원본. 게임에 직접 쓰지 않음 |
| ~~`images/player/sword_attack/side.png`~~ | ~~위 PixelLab 프레임에 Claude Code가 게임 Idle 후드를 붙이고 보정 (2026-11-16)~~ | | 2026-11-17 아래 3단 콤보 그림으로 교체 (D-022) |
| `concepts/player_attack_reference_v1.png`, `_v2.png` | 사용자가 ChatGPT로 생성한 측면 공격 3단 콤보 참고 시트 (2026-11-16·17). v2는 칼을 파란 단색으로 그림 | 사용자 소유 (생성물) | v2가 지금 게임 그림의 원본. 게임에 직접 쓰지 않음 |
| `concepts/player_attack_reference_v3_hit{1,2,3}.png` | 사용자가 ChatGPT로 생성한 타별 8칸 시트 (2026-11-17) | 사용자 소유 (생성물) | 시험 후 쓰지 않기로 함 (D-022) |
| `concepts/player_attack_reference_front_v1.png` | 사용자가 ChatGPT로 생성한 정면 공격 시트 (2026-11-17) | 사용자 소유 (생성물) | 정면 공격 그림의 원본. 다시 받을 예정 (D-022) |
| `concepts/attack_front_pose_guide.png`, `concepts/player_ingame_*_x10.png` | Claude Code 제작 (2026-11-17): 정면 공격 자세 안내도, 게임 스프라이트 10배 확대본 | 프로젝트 소유 | ChatGPT 요청용 |
| ~~`images/player/sword_attack/{side,front}_{1,2,3}.png`, `*_hand.png`~~ (2026-11-17 모두 아래 PixelLab 그림으로 교체) | 위 참고 시트를 Claude Code가 변환 (`concepts/build_attack_v3.py`, `build_attack_view.py`, 2026-11-17) | 사용자 소유 (파생물) | 96×64 × 5프레임. 몸(칼 없음)과 칼 앞 레이어. **임시 에셋**. D-022 |
| `images/golem/{south,north,east,west}.png` | 사용자가 PixelLab(pixellab.ai)으로 생성 (`concepts/pixellab/golem_simple/rotations/`, 2026-11-17)에서 상하좌우 4장을 복사 | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 96×96, 투명 배경. 게임에서 2배 확대. 대각선 4장은 쓰지 않음. D-028 |
| `images/golem/kick_{south,north,east,west}.png` | 핵심 자세는 사용자가 ChatGPT 로 생성 (`concepts/pixellab/golem_kick/chatgpt_kit/result_*.png`, 2026-11-18), 사이 동작은 사용자 PixelLab 계정으로 생성, Claude Code 가 축소·색 맞춤·조립 (`process_results.py`, `build_golem_kick.py`) | 사용자 소유 (생성물) / PixelLab 이용약관 | 160×144 × 11프레임 가로 한 줄, 발 밑 (80, 132). 서쪽은 동쪽 반전. ② 올려차기. D-038 |
| `images/golem/slam_{south,north,east,west}.png` | 사용자 PixelLab(pixellab.ai) 계정으로 생성 (`concepts/pixellab/golem_slam/`, 2026-11-17)한 것을 Claude Code가 위치 맞춤 (`build_golem_slam.py`) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 144×176 × 14프레임 가로 한 줄, 발 밑 가운데 (72, 166). ① 내려찍기. D-036. 후면 착지·일어섬(7~13장)은 핵심 자세를 사용자가 ChatGPT 로 그림 (`golem_slam/chatgpt_kit_back/`, 2026-11-18), D-041 |
| `images/effects/golem_slam.png` | Claude Code 제작 (`concepts/vfx/slam/build_golem_slam_impact.py` 가 계산해 그림, 2026-11-17). 골렘 팔레트 | 프로젝트 소유 | 160×160 × 16프레임 (8열 × 2줄). ① 충격 이펙트. D-036 |
| `images/golem/walk_{south,north,east,west}.png` | 사용자 PixelLab(pixellab.ai) 계정으로 생성 (`concepts/pixellab/golem_walk/skeleton_4dir.png`, skeleton-v3 walking-8-frames, 2026-11-17)한 것을 Claude Code가 위치 맞춤 (`build_golem_walk.py`) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 128×128 × 8프레임 가로 한 줄, 발 밑 가운데 (64, 118). 걷기. D-034 |
| `images/golem/stomp_{south,north,east,west}.png` | 사용자 PixelLab(pixellab.ai) 계정으로 생성 (`concepts/pixellab/golem_stomp_anim/`, 2026-11-17)한 것을 Claude Code가 위치 맞춤 (`align_stomp_frames.py`) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 176×152 × 19프레임 가로 한 줄, 발 밑 가운데 (88, 140). ③ 발 구르기 동작. D-033 |
| `images/player/parry/{side,front}.png`, `*_hand.png` | 사용자 PixelLab(pixellab.ai) 계정으로 생성 (`concepts/pixellab/player_import/remake_raw/parry_*`, 2026-11-17)한 것을 Claude Code가 변환 (`export_to_game.py`) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 96×64 × 5, 칼 없음 (칼은 `weapons/`). 측면·정면 패링 (정면은 몸 색을 게임 색으로 맞춤). D-037 |
| `images/player/parry/back.png`, `back_hand.png` | 핵심 자세는 사용자가 ChatGPT 로 생성 (`concepts/pixellab/player_import/parry_back_kit/result_back.png`, 2026-11-18), Claude Code 가 축소·색 맞춤·변환 (`build_parry_back.py`, `export_to_game.py`) | 사용자 소유 (생성물) | 96×64 × 5, 칼 없음 (칼은 `weapons/`). 후면 패링. D-039 |
| `images/effects/parry_spark.png` | Claude Code 제작 (`concepts/vfx/parry/build_parry_spark.py` 가 계산해 그림, 2026-11-17) | 프로젝트 소유 | 64×64 × 9 (가로 한 줄). 패링 성공 노란 불꽃. D-037 |
| `images/effects/golem_laser_charge.png` | 사용자 PixelLab(pixellab.ai) 계정의 VFX Creator 로 Claude Code 가 제작 ('Golem laser charge', 2026-11-18), `concepts/vfx/laser/pixellab/pack_for_game.py` 로 변환 | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 88×88 × 24 (칸 가운데 = 코어). D-040 |
| `images/effects/golem_laser_{beam,blast}.png` | Claude Code 제작 (`concepts/vfx/laser/build_golem_laser.py` 가 계산해 그림, 2026-11-18) | 프로젝트 소유 | 레이저 단면 4×12 (늘려 그림), 폭발 160×160 × 16. D-040 |
| `images/effects/golem_stomp.png` | Claude Code 제작 (`concepts/vfx/stomp/build_golem_stomp.py` 가 계산해 그림, 2026-11-17). 색은 골렘 그림 팔레트 | 프로젝트 소유 | 288×288 × 30프레임 (6열 × 5줄). ③ 발 구르기 바닥 이펙트. D-032 |
| `concepts/vfx/stomp/*` | Claude Code 제작 (2026-11-17): 위 시트의 생성 스크립트, 게임 배율 미리보기 | 프로젝트 소유 | 게임에 직접 쓰지 않음 |
| `images/player/jump/{front,back,side}.png`, `images/player/sword_attack/side_{1,2,3}.png`, `side_*_hand.png`, `front_{1,2,3}.png`, `front_{1,2,3}_hand.png` | 사용자 PixelLab(pixellab.ai) 계정으로 생성 (`concepts/pixellab/player_import/remake_raw/`, 2026-11-17)한 것을 Claude Code가 변환 (`export_to_game.py`) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 점프 48×56 × 10 (정면 jump_v7, 측면 jump_v19, 후면 jump_v14, 왼쪽은 측면 반전), 측면 공격·정면 1·2·3타 96×64 × 8 (칼 없음, 칼은 `weapons/`). 위의 점프·측면 공격 그림을 대체 (걷기는 예전 v3 그림 유지). D-029 |
| `maps/test_room.txt` | Claude Code 제작 (2026-11-17) | 프로젝트 소유 | 글자 맵 (D-023). 시험용 방, 허수아비 `D` 2개 (D-024), 골렘 `G` 1개 (D-026) |
| `images/player/weapons/old_sword_front_3.png` | 사용자 PixelLab(pixellab.ai) 계정으로 생성한 정면 3타 그림의 칼을 Claude Code가 떼어 칼 색으로 바꿈 (`export_to_game.py`, 2026-11-17) | PixelLab 이용약관에 따름 (사용자 계정 생성물) | 96×64 × 8, 찌르는 6~8번째만 그림. 정면 3타 찌르기용 칼 그림. D-031 |
| `images/player/weapons/old_sword.png` | Claude Code 제작 (`concepts/weapons/build_old_sword.py`, 2026-11-17). 컨셉 시트의 낡은 검 기준 | 프로젝트 소유 | 56×10, 칼끝 오른쪽, 손이 한가운데. D-022 |

> ~~`concepts/player_walk_reference.png`, `images/player/{idle,walk}_{front,back,side}.png`~~ (2026-11-03 v3로 교체하며 삭제. v1/v2 `player_master` 이미지는 커밋하지 않았고 v3 결과와 섞이지 않음)

### 주인공 스프라이트 (Idle/Walk v3)

- 형식: `images/player/<상태>/<front|back|side>.png`. 32×48px(원본) 프레임 4장을 가로로 이어 붙인 128×48 투명 배경(RGBA) 시트.
  게임 화면에는 `RENDER_SCALE`(2)배, 64×96px로 nearest 확대해 그립니다. 원본 크기와 표시 배율은 따로 관리합니다(DECISIONS D-017).
- `side`는 오른쪽을 보는 그림이며, 왼쪽은 게임에서 좌우 반전해 그립니다. 캐릭터 본체만 포함하고 검은 포함하지 않습니다.
- 원본 분석: 두 시트 모두 1182×1330px, 3행(정면·후면·오른쪽 측면) × 4열, 배경 실측 약 `(4, 249, 5)`.
  캐릭터 한 명은 약 150~190 × 342~353px. 균등 분할하지 않고 초록이 아닌 픽셀의 연결 요소 12개로 실제 위치를 찾았습니다(잡티 없음, 프레임끼리 겹침 없음).
  원본 도트 한 칸이 약 4~5px이지만 정확한 격자가 아닙니다.
- 가공 순서 (DECISIONS D-018)
  1. 초록 제거: 초록 정도로 알파를 추정하고 반투명 경계는 배경색을 역계산해 빼고 초록 기운 제거(디스필). 결과에 반투명·초록 픽셀 0개.
  2. 색 보정: 시트별로 갈색(후드·망토)의 채도·명도·색상과 어두운 옷의 채도를 컨셉아트 중앙값에 맞춤.
     보정 후 갈색 채도/명도 Idle·Walk 모두 0.402/0.400 (컨셉 0.409/0.408). 원본 v3는 컨셉보다 밝고 붉었고 Walk가 더 붉었습니다.
  3. Idle·Walk 24프레임 공용 팔레트 28색 (디더링 없음) → 프레임마다 색이 바뀌지 않음.
  4. 축소: 24프레임 같은 축척(약 1/7.6). 출력 픽셀마다 영역에서 가장 많이 덮는 팔레트 색을 고름(외곽선 가중).
  5. 정렬: 방향마다 Idle 1번 프레임을 기준(master)으로 모든 프레임의 후드를 정합. 발은 맨 아래 줄, 기준 프레임 가로 중심은 16.
  6. Idle: 기준 프레임을 그대로 쓰고, 망토 줄(19~43행)에서 **실루엣이 달라진 픽셀만** 각 원본 프레임에서 가져옴 (후드·얼굴·몸통·벨트·발 고정).
  7. Walk: 머리(후드·얼굴·턱) 영역을 기준 프레임 그림으로 교체하고 상하 반동만 정수 픽셀로 반영 (후드 깜빡임·형태 변화 방지).
- 알려진 문제 (게임용 최종 에셋 아님)
  - 원본(캐릭터 키 약 72도트 상당)을 48px로 줄여 벨트 버클·장갑·가슴 장식 같은 작은 디테일이 뭉개지고, 몸통에 얼룩진 픽셀이 남아 있습니다.
  - **Walk 정면 2번째 프레임** (2026-11-10 수정): 원본은 중립이 아니라 한 발이 앞에 나온 자세였습니다.
    다리(39~47행)를 Idle 기준 프레임의 두 발 모은 다리로 바꾸고, 다음에 나갈 왼발(화면 오른쪽)만 1줄 들었습니다.
    부츠 하이라이트가 다른 Walk 프레임보다 조금 밝습니다.
  - **Walk 측면 3번째 프레임** (2026-11-10 수정): 원본은 1번째와 같은 다리(가까운 다리)가 앞이었습니다.
    다리 모양은 그대로 두고, 1번째 프레임의 가까운 다리 색을 뒤쪽 다리에, 먼 다리 색을 앞쪽 다리에 밝기 순위대로 옮겨 칠했습니다.
  - 어두운 옷 채도는 컨셉보다 약간 높습니다(0.36~0.37, 컨셉 0.31).

### 점프 (임시 에셋, 2026-11-10)

- v3 Idle 기준 그림(후드·얼굴·몸통·색)은 그대로 두고, **팔과 다리만 v3 팔레트로 새로 그렸습니다** (Claude Code 손그림).
- 5프레임 (2026-11-10 역동적으로 다시 그림): ① 깊게 웅크림(바지 4줄 압축, 무릎 살짝 벌림)
  ② 몸을 쭉 뻗으며 도약(바지 3줄 늘림) ③ **최고점: 무릎을 상반신(벨트 높이)까지 당겨 몸을 공처럼**
  (정면은 무릎 두 개를 벨트 앞에 그리고 부츠를 바로 밑에, 측면은 허벅지를 가슴 높이로 비스듬히, 후면은 망토 자락 전체를 젖히고 부츠 밑창)
  ④ 다리를 펴며 착지 준비(망토 젖힘) ⑤ 착지 웅크림. ③은 발이 바닥 줄에 닿지 않습니다. 실제 높이와 그림자는 게임 코드가 처리합니다.
- 팔·후드 (2026-11-11 2차 수정, 사용자 피드백: 정면·후면 팔이 부자연스러움, 후드가 안 내려가 보임):
  정면은 팔꿈치를 몸 가까이 두고 오른팔을 가슴 앞에서 접어 얼굴 바로 위 챙을 잡음(외곽선은 배경과 닿는 곳에만).
  측면은 ~~얼굴을 가리지 않도록 후드 옆면(뺨 쪽)을 잡음~~ → (2026-11-11 3차) 팔을 몸 앞으로 들어 **후드 앞 챙**을 잡음.
  아래팔은 얼굴 앞 가장자리를 따라 세워 턱이 끊기지 않게 함(뒤통수 쪽을 잡으면 끌어내리는 동작으로 보이지 않음). 후면은 팔이 얼굴 앞이라 그리지 않음. 왼손은 망토 안.
  후드는 도약 1줄 → 최고점·다리 펴기 2줄 → 착지 1줄 내려감. 측면은 챙 쪽 2줄, 뒤통수 1줄로 앞으로 기울어짐.
  `side_left.png`(왼쪽 보기 전용)는 팔 없는 오른쪽 그림을 뒤집고 먼 쪽 오른손 주먹 끝만 후드 앞자락에 그렸습니다
  (측면을 그대로 뒤집으면 후드 잡은 손이 왼손이 되므로).
- 다리 (2026-11-10 수정): 웅크림만 1칸 벌리고, 최고점 무릎과 부츠는 모음.
- 그림자(`shadow.png`): 24×6 반투명 타원. 점프 중에만 발 위치에 그립니다.
- ~~패링 몸 4프레임 (`parry/`)~~ (2026-11-10 삭제: 패링 애니메이션은 공격 모션과 함께 제작)

> 현재 화면의 글자는 pico2d 패키지에 포함된 기본 폰트(`ConsolaMalgun.ttf`)를 사용하며, 이 폴더에 복사하지 않습니다.
