# HANDOFF — AI 간 작업 인수인계

> 작업 세션을 마칠 때마다 **맨 위에** 새 항목을 추가합니다. 오래된 항목은 지우지 않습니다.
> 다음 작업자(Claude Code 또는 Codex)는 작업을 시작하기 전에 최신 항목을 먼저 읽습니다.

## 작성 양식

```markdown
## YYYY-MM-DD — <작업 이름> (<작업자>)
- 브랜치 / 마지막 커밋:
- 한 일:
- 현재 상태: (동작 여부, 테스트 결과)
- 다음 작업자가 알아야 할 것:
- 남은 문제 / 다음 할 일:
```

---

## 2026-11-10 — 주인공 점프·패링 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (`claude/player-idle-walk-v3` 위에서 분기. 앞선 PR들이 아직 `main`에 병합되지 않음)
- **한 일**
  - `Space` 점프, `F` 패링. 상태 머신에 `jump`·`parry`, `game/player/actions.py`(`Jump`, `Parry`), 무기 레이어 그리기, 점프 그림자 (D-019)
  - 에셋: `jump/`·`parry/`(v3 Idle 재조립), `weapon/parry/`(검), `shadow.png` — 모두 임시 에셋 (`assets/README.md`)
  - PRE-PRD 2.1·2.2·2.7 점프·패링 규칙 확정 (사용자 승인)
- **현재 상태**: `python -m unittest` 105개 통과, `python main.py --frames 60` 실행 성공.
  실제 창 캡처(코드로 입력)에서 4방향 점프(그림자·높이)·패링(검 레이어, 후면은 몸 뒤, 왼쪽은 반전)·Idle 복귀 확인. **키보드로 직접 조작해 본 확인은 안 함.**
- **다음 작업자가 알아야 할 것**
  - 패링 성공 판정은 `player.parry.is_active`, 점프 공중 여부는 `player.jump.is_airborne`. 몬스터 공격 처리에서 이 값을 쓰면 된다.
  - 무기 레이어는 `weapon_sheet_path(상태, 방향)`. 공격 등 다른 상태에 검을 그리려면 같은 경로에 시트를 추가하고 `Player.draw`의 조건을 넓힌다.
- **남은 문제**: 패링 몸은 서 있는 자세 그대로(팔을 든 원본 없음). ChatGPT 패링·점프 자세를 받으면 교체 권장.

---

## 2026-11-10 — Walk 문제 프레임 2장 수정 (Claude Code)

- **브랜치**: `claude/player-idle-walk-v3` (같은 PR에 추가)
- **한 일**: 정면 Walk 2번째를 중립 자세로(다리를 Idle 다리로 교체, 왼발 1줄 들기), 측면 Walk 3번째의 다리 명암을 1번째 프레임 색 분포로 옮겨 칠함.
  둘 다 v3 원본 픽셀만 재조립했고 새로 그린 부분은 없음.
- **결정**: 그림은 ChatGPT 원본을 쓰고 Claude Code는 가공·보정만 함. Claude Code가 직접 그린 정면 시험 그림은 사용자가 원본보다 못하다고 판단해 쓰지 않음(저장소에 넣지 않음).
- **현재 상태**: `python -m unittest` 88개 통과, `python main.py --frames 60` 실행 성공. 키보드로 직접 조작해 본 확인은 안 함.
- **남은 문제**: 32×48 축소로 생긴 몸통 얼룩 픽셀, 정면 2번째 부츠 하이라이트가 조금 밝음.

---

## 2026-11-03 — 주인공 Idle/Walk v3 에셋 보정·적용 (Claude Code)

- **브랜치**: `claude/player-idle-walk-v3` (`claude/render-scale-2x` 위에서 분기. 앞선 PR들이 아직 `main`에 병합되지 않음)
- **한 일**
  - `player_idle_reference_v3.png`, `player_walk_reference_v3.png`에서 `assets/images/player/{idle,walk}/{front,back,side}.png` 생성 (각 4프레임 128×48)
  - 컨셉아트 기준 색 보정 + 공용 28색 팔레트, Idle 몸 고정(망토 끝만), Walk 머리 고정 (D-018)
  - 코드: `sprite_sheet_path`를 `<상태>/<방향>.png`로, `PLAYER_IDLE_FRAMES = 4`, `PLAYER_IDLE_FRAME_DURATION = 0.2`. 이동·상태 머신·그리기는 그대로
  - 에셋 검사 테스트 확장 (발·알파·초록, Idle 고정 영역, Walk 머리·다리 중복)
- **현재 상태**: `python -m unittest` 88개 통과. `python main.py --frames 60` 실제 창 실행 성공.
  실제 창 캡처(코드로 입력)에서 4방향 Idle/Walk 재생, 전환 시 발 위치 0px 변화, 화면 초록 픽셀 0개 확인. **사람이 키보드로 조작해 본 확인은 안 함.**
- **다음 작업자가 알아야 할 것**
  - 작업 폴더에 커밋하지 않은 이전 시도 파일이 있습니다: `assets/images/player/master/`, `palette.json`, `sprites.json`(player_master_v1, 64×96 기준),
    `assets/concepts/player_idle_walk_source_sheet.png`. 게임 코드는 이 파일들을 쓰지 않습니다.
  - `player_character_concept_v1.png`는 작업 폴더에서 RGB→RGBA로만 바뀌어 있고 픽셀은 같습니다 (커밋하지 않음).
- **남은 문제 / 다음 할 일**
  - ~~Walk 정면 2번째 프레임(중립이 아님), Walk 측면 3번째 프레임(다리 명암만 보정) 재작업~~ (2026-11-10 수정)
  - 32×48 축소로 작은 디테일이 뭉개짐 — 32×48 도트로 직접 손보는 것이 가장 확실함

---

## 2026-11-03 — 화면 표시 2배 확대 + 추적 카메라 (Claude Code)

- **브랜치**: `claude/render-scale-2x` (`claude/player-walk-sprites` 위에서 분기. 앞선 PR들이 아직 `main`에 병합되지 않았기 때문)
- **한 일**
  - 설정 분리: `LOGICAL_TILE_SIZE = 32`, `RENDER_SCALE = 2`, `RENDER_TILE_SIZE = 64`, `PLAYER_RENDER_WIDTH/HEIGHT = 64×96`. `TILE_SIZE` 삭제 (D-017)
  - `Renderer.draw_sprite_frame`에 표시 크기(`draw_width`, `draw_height`) 추가, nearest 확대
  - `game/world/camera.py` `Camera` 추가, `FieldScene`이 주인공을 따라 스크롤 (맵 32×18칸, 화면 16×9칸)
  - PRE-PRD 2.5·3.2의 [확정] 크기 항목을 취소선으로 남기고 갱신 (사용자 요청)
- **현재 상태**: `python -m unittest` 86개 통과. `python main.py --frames 60` 실제 창 실행 성공.
  실제 창 캡처로 타일 64px, 주인공 64×96 nearest 확대(2×2 블록), 카메라 중앙 추적·맵 모서리 정지 확인.
  **사람이 키보드로 직접 조작해 본 확인은 하지 않았습니다.**
- **다음 작업자가 알아야 할 것**
  - 크기를 바꿀 때는 `RENDER_SCALE`만 바꾸세요. 로직(칸 좌표)과 에셋 원본 크기는 그대로입니다.
  - 카메라 위치는 `Grid.origin_x/origin_y`에 반영됩니다. 같은 `Grid`를 쓰는 `GridMover`는 원점을 쓰지 않으므로 영향이 없습니다.
  - 맵 맨 위 줄에서 주인공 머리 32px가 화면 위로 잘립니다.

---

## 2026-11-03 — 새 Walk 스프라이트 적용 (Claude Code)

- **브랜치**: `claude/player-walk-sprites` (`claude/player-move-anim` 위에서 분기. 그 PR이 아직 `main`에 병합되지 않았기 때문)
- **한 일**
  - 사용자가 만든 `assets/concepts/player_walk_reference.png`(3×4, 초록 배경)에서 `walk_{front,back,side}.png` 재추출 (각 128×48, 4프레임)
  - 상태별 프레임 수 설정 `PLAYER_IDLE_FRAMES = 5`, `PLAYER_WALK_FRAMES = 4` (D-016). 이동·상태 머신·그리기 코드는 그대로
  - Walk 프레임의 발 위치·알파·초록 잔여 픽셀 검사 테스트 추가 (표준 라이브러리로 PNG 읽기)
- **현재 상태**: `python -m unittest` 80개 통과. `python main.py --frames 60` 실제 창 실행 성공.
  코드로 입력을 흉내 낸 실제 창 캡처에서 4방향 Walk 재생, 왼쪽 반전, Idle 복귀, 발 높이 유지, 화면에 초록 픽셀 0개 확인.
  **사람이 키보드로 직접 조작해 본 확인은 하지 않았습니다.**
- **다음 작업자가 알아야 할 것**
  - 추출 방법과 품질 문제는 `assets/README.md`. 추출 스크립트는 저장소에 넣지 않았습니다 (Pillow 필요, requirements 밖).
  - Idle은 예전 임시 에셋이라 새 Walk와 그림체·측면 키(약 3px)가 다릅니다. Idle도 같은 방식의 참고 시트로 다시 만드는 것을 권합니다.

---

## 2026-11-03 — 대각선 이동 제거, 걷기 모션 점검 (Claude Code)

- **브랜치**: `claude/player-move-anim` (같은 PR에 추가)
- **한 일**
  - 사용자 요청으로 대각선 이동 제거 → 상하좌우 4방향. 두 키를 누르면 나중에 누른 방향 (D-015). PRE-PRD 8방향 [확정] 항목을 취소선으로 남기고 변경.
  - 테스트 79개 통과. 칸이 바뀌어도 걷기 프레임이 처음으로 돌아가지 않고 5프레임을 모두 재생하는지 테스트 추가.
- **걷기 모션이 약해 보이는 원인 (사용자 질문)**
  - 코드는 walk 시트 5프레임을 0.1초 간격으로 재생하고 있음 (테스트·캡처로 확인).
  - 원인은 **참고 시트의 Walk 프레임 자체**: 측면 5프레임은 다리 자세가 거의 같고, 정면·후면도 다리 차이가 작음. 32×48로 줄이면 차이가 몇 픽셀뿐.
  - 해결하려면 다리 교차가 분명한 Walk 프레임을 다시 그려야 함 (T-015).

---

## 2026-11-03 — 주인공 기본 이동 + Idle/Walk 애니메이션 (Claude Code)

- **브랜치**: `claude/player-move-anim` (Pull Request로 검토, `main` 자동 병합 안 함)
  - 미병합 상태였던 `codex/player-animation-fsm-spec`(명세 문서)을 기준으로 삼기 위해 이 브랜치에 포함했습니다. 해당 PR을 따로 병합해도 충돌 없이 합쳐집니다.
- **한 일**
  - `game/player/` 패키지 추가: `movement.py`(칸 이동·보간·화면 경계), `facing.py`(4방향과 front/back/side 선택), `state_machine.py`(transitions idle/walk), `animation.py`(dt 기반 반복 애니메이션), `player.py`(묶음)
  - `game/scenes/field_scene.py` 추가, `game/core/app.py`가 `BootScene` 대신 `FieldScene`을 실행. (`BootScene`과 그 테스트는 남겨 둠)
  - 입력: `Action.MOVE_UP/DOWN/LEFT/RIGHT`, WASD·방향키 배치, `InputState.move_direction()`
  - `Renderer.draw_sprite_frame()`(스프라이트 시트 프레임, 좌우 반전, 정수 픽셀, nearest)
  - 스프라이트 6장 `assets/images/player/` (참고 시트에서 추출한 **임시 에셋**), 참고 시트 `assets/concepts/player_body_animation_reference.png` 커밋
  - `requirements.txt`에 `transitions==0.9.3` 추가
- **현재 상태**: `python -m unittest` 77개 통과. `python main.py --frames 60` 실제 창 실행 성공. 코드로 입력을 흉내 낸 실제 창 캡처에서 방향별 그림·반전·발 위치·선명도 확인.
  **사람이 키보드로 직접 조작해 본 확인은 하지 않았습니다.**
- **다음 작업자가 알아야 할 것**
  - 개발 환경: Windows, Python 3.14.7, `.venv`. 스프라이트 추출에만 Pillow를 썼고 `requirements.txt`에는 넣지 않았습니다.
  - 새 상태 추가는 `state_machine.py`의 `STATES`·`TRANSITIONS`와 `Player.animations`에 항목을 더하고 `<상태>_<방향>.png`를 넣으면 됩니다.
  - 화면 맨 위 줄(row 17)에 서면 48px 그림의 머리 16px가 화면 밖으로 잘립니다(논리 위치는 화면 안).
- **남은 문제 / 다음 할 일**
  - 정식 도트 에셋으로 교체 (임시 에셋 문제점은 `assets/README.md`)
  - PRE-PRD 2.1 [미정] 대각선 이동 시간 결정, [제안] 이동 입력 버퍼 여부
  - `AGENTS.md` 2장 폴더 구조에 `game/player/` 반영 (공통 규칙 문서라 사용자 승인 후)

---

## 2026-11-02 — 주인공 애니메이션/FSM 설계 정리 (ChatGPT)

- **브랜치**: `codex/player-animation-fsm-spec` (PR에서 검토 후 병합)
- **기획 반영**: idle/walk/jump/dodge/sword_attack/parry/hurt/stun = 8개, 3방향 원본+측면 반전, 각 4~5프레임 초기 목표.
- **전투 구분**: Jump=하단 공격 회피, Dodge=별도 회피, Hurt=피격 자세, Stun=강공격 후 2~3초 행동 불가.
- **기술 결정**: 수업에서 사용한 `transitions`를 상태 머신에 사용하기로 사용자 결정.
- **코드 변경 여부**: 이번 작업은 기획 및 명세 문서만 수정. 실제 이미지 생성·transitions 설치·코드 구현 및 런타임 테스트는 아직 진행하지 않음.
- **다음 작업**: 캐릭터의 정면/후면/측면 정지 원본을 공식 컨셉 기준으로 제작 후 애니메이션 프레임 확정.

---

## 2026-11-02 — 화면·타일·주인공 스프라이트 규격 변경 (ChatGPT)

- **브랜치**: `codex/display-and-sprite-sizing` (main 병합 전 PR 검토 필요)
- **변경 사항**: 화면 1024×576, 타일 32×32, 화면 격자 32×18, 스프라이트 표시 기준 32×48px 설정.
- **변경 파일**: `game/config.py`, 테스트, `PRE-PRD.md`, `README.md`, `docs/DECISIONS.md`, `TASKS.md`.
- **검증**: 설정값 및 격자 연산 정합성 검토, GitHub 연결 환경에서는 Pico2D 실제 실행 테스트 미실시. 사용자 VS Code에서 `python -m unittest`와 `python main.py` 검증 필요.
- **다음 작업**: 주인공 스프라이트 제작 후 렌더링 구현. 실제 에셋은 아직 적용되지 않음.

---

## 2026-11-02 — 프로젝트 초기 환경 구성 (Claude Code)

- **브랜치 / 마지막 커밋**: `main` / `git log`로 확인 (이 문서는 해당 커밋들에 포함됨)
- **한 일**
  - 기준 문서 작성: `PRE-PRD.md`, `AGENTS.md`, `CLAUDE.md`, `TASKS.md`, `docs/DECISIONS.md`, `docs/HANDOFF.md`, `README.md`
  - `.gitignore`, `requirements.txt`(`pico2d==1.5.1`) 추가
  - 최소 Pico2D 프로그램: 960×640 창, 32px 칸 격자, 원점 칸 (0, 0) 표시, 화면 중앙 칸 표식(0.5초마다 깜빡임, dt 기반), FPS·좌표 정보, ESC 또는 창 닫기로 종료
  - 계층 분리: `core`(루프·dt) / `input`(Action 기반 입력) / `world`(칸↔픽셀 변환) / `physics`(빈 패키지) / `render` / `scenes`
  - `main.py --frames N` 자동 종료 옵션 (스모크 테스트용)
  - 테스트 29개 (`tests/`): FrameClock, Grid, InputState, BootScene(FPS 독립성 포함), 실행 스모크 테스트
- **현재 상태**
  - `python -m unittest` 29개 통과 (Linux, Python 3.13, pico2d 1.5.1)
  - pico2d가 없는 환경에서도 순수 로직 테스트 28개 통과 (스모크 테스트 1개는 건너뜀)
  - 가상 디스플레이(Xvfb)에서 실제 창으로 300프레임 실행·종료 확인, 화면 캡처로 격자·한글 글자 표시 확인
  - 실제 SDL 이벤트를 넣어 ESC 키와 창 닫기가 종료로 이어지는지 확인
  - **실제 모니터(Windows/macOS)에서는 아직 실행해 보지 않았습니다.**
- **다음 작업자가 알아야 할 것**
  - 게임플레이 기능은 아직 하나도 없습니다. `BootScene`은 환경 확인용이며, 첫 기능을 만들 때 새 장면으로 바꾸거나 대체해도 됩니다.
  - `Action`에는 `QUIT`만 있습니다. 이동·전투 행동은 해당 기능에서 추가하고 키 배치는 `KEY_BINDINGS`에만 둡니다.
  - pico2d `get_events()`는 호출할 때마다 창 제목을 FPS 표시로 덮어씁니다. 창 제목을 바꾸려면 이 점을 고려해야 합니다.
  - pico2d `clear_canvas()`는 기본 격자 배경을 그리므로 `app.py`에서 `hide_lattice()`를 호출합니다.
- **남은 문제 / 다음 할 일**
  - GitHub 푸시: 저장소 권한 연결 후 `main`에 푸시 완료 (2026-11-02)
  - 사용자 PC에서 `python main.py` 실행 확인
  - 다음 기능은 사용자 지시를 기다립니다. (후보: TASKS.md T-001 맵 표시, T-002 8방향 칸 이동)
