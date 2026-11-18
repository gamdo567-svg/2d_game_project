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

## 2026-11-18 — 골렘 후면 내려찍기 일어섬 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (푸시 안 함, 사용자 요청으로 보류)
- **한 일**: 후면 ① 내려찍기의 착지·일어섬을 ChatGPT 핵심 자세 + PixelLab 사이 동작으로 다시 만들었다 (D-041).
  손은 등에 가려지고, 팔이 몸과 함께 올라온다.
- **현재 상태**: 테스트 245개 통과. 실제 pico2d 창 캡처로 들기 → 착지 → 일어섬 확인. 직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: 다시 만들려면 `golem_slam/chatgpt_kit_back/process_results.py` → `build_north.py` →
  `aligned/slam_north.png` 를 `assets/images/golem/` 로 복사.
- **남은 문제 / 다음 할 일**: 발 구르기 후면 일어섬 확인. 푸시·PR 은 사용자 결정 대기.

---

## 2026-11-18 — 골렘 레이저 다시 넣기, 스택 발사 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (푸시 안 함, 사용자 요청으로 보류)
- **한 일**: ④ 레이저를 다시 켰다. 막지 못한 빨강·노랑 공격 4스택 또는 주인공이 8칸보다 멀면 발사 (D-040, PRE-PRD 2.4).
  맞은 공격은 스택에 세지 않는다 (사용자 요청). 코어 충전 구(점점 커짐, 다 커도 코어의 두 배 정도) → 하얀 레이저 → 조준점 4×4 폭발.
  충전·폭발 그림은 사용자 요청으로 PixelLab VFX Creator 로 다시 만듦 (`assets/concepts/vfx/laser/pixellab/`, 바꾸려면 pixellab.ai
  내 이펙트에서 고쳐 내보낸 뒤 `pack_for_game.py`). 레이저 단면만 `build_golem_laser.py` 계산 그림.
- **현재 상태**: 테스트 245개 통과. 실제 pico2d 창 캡처로 충전 → 발사 → 폭발 확인 (`assets/concepts/vfx/laser/golem_laser_ingame_capture.png`).
  직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: 스택 수는 화면에 표시하지 않는다 (요청 범위 밖). 수치는 `GOLEM_LASER_STACKS`, `GOLEM_LASER_FAR`.
- **남은 문제 / 다음 할 일**: 스택 표시 UI 여부, 골렘 충전 자세 그림(지금은 서 있는 그림). 발 구르기·내려찍기 후면 일어섬 문제. 푸시·PR 은 사용자 결정 대기.

---

## 2026-11-18 — 주인공 후면 패링 모션 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (푸시 안 함, 사용자 요청으로 보류)
- **한 일**: 후면 패링(당김 → 쳐올림 → 막기 ×2 → 당김)을 넣었다 (D-039, PRE-PRD 2.2). PixelLab 이 후면을 못 그려
  핵심 자세는 사용자가 ChatGPT 로 그렸다 (`assets/concepts/pixellab/player_import/parry_back_kit/`).
  위를 볼 때 패링 불꽃은 화면 왼쪽(칼날 쪽).
- **현재 상태**: 테스트 240개 통과. 실제 pico2d 창 캡처로 쳐올림 잔상 → 왼쪽 위 막기 → 당김 확인. 직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: 그림을 바꾸려면 `result_back.png` 를 바꾸고 `build_parry_back.py` → `export_to_game.py` 를 돌린 뒤
  출력된 `PLAYER_PARRY_SWORD['back']` 를 `game/config.py` 에 옮긴다. 칼 자리는 `build_remake_preview.OVERRIDES` 의 `parry_back`.
- **남은 문제 / 다음 할 일**: ④ 레이저 그림. 발 구르기·내려찍기 후면 일어섬 문제. 푸시·PR 은 사용자 결정 대기.

---

## 2026-11-18 — 골렘 올려차기 동작 그림, 앞차기 앞으로 4칸 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (푸시 안 함, 사용자 요청으로 보류)
- **한 일**: ② 올려차기 4방향 그림을 넣고(화면 흔들림·이펙트 없음), 범위를 가로 3 × 앞으로 4 로 줄였다 (D-038, PRE-PRD 2.4).
  PixelLab 만으로는 실패해, 핵심 자세는 사용자가 ChatGPT 로 그리고(`assets/concepts/pixellab/golem_kick/chatgpt_kit/`)
  사이는 PixelLab 으로 채웠다.
- **현재 상태**: 테스트 240개 통과. 실제 pico2d 창 캡처로 서쪽을 볼 때 당김 → 차기 → 되돌아옴과 4×3 예고 칸 확인
  (`assets/concepts/pixellab/golem_kick/ingame_capture_contact.png`). 직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: 그림을 바꾸려면 chatgpt_kit/README.txt 순서대로 `result_<dir>.png` 를 바꾸고
  `process_results.py` → PixelLab 사이 동작 → `build_golem_kick.py` → `aligned/kick_*.png` 를 `assets/images/golem/` 로 복사.
  `*_try/` 폴더는 실패한 시안 (커밋 안 함).
- **남은 문제 / 다음 할 일**: ④ 레이저 그림(지금은 설정으로 꺼 둠). 발 구르기·내려찍기 후면 일어섬 문제. 푸시·PR 은 사용자 결정 대기.

---

## 2026-11-17 — 패링 모션(측면) + 패링 성공 이펙트 (Claude Code)

- **브랜치**: `claude/player-parry` (`claude/golem-stomp-vfx` 위에서 시작, 그 브랜치가 아직 푸시 전이라 푸시 보류)
- **한 일**: PixelLab 패링 측면 5장(칼 분리)과 노란 불꽃 이펙트, 패링 성공 시 재생 (D-037).
- **현재 상태**: 테스트 전체 통과. 그리기는 PIL 캡처로 확인, 실제 창 확인 못 함.
- **이어서 (2026-11-18)**: 정면 패링을 측면 기준으로 다시 그려 넣음 (`Parry Ready` → `Parry Guard`, 몸 색을 게임 색으로 맞춤).
- **다음 작업**: 후면 패링 그림 (PixelLab 이 고개를 돌려 두 번 실패. 막기·당김 자세 state 는 4방향 있음: `remake_raw/parry_guard_<방향>.png`, `parry_ready_<방향>.png`).

---

## 2026-11-17 — 골렘 두 손 내려찍기 동작 그림 + 충격 이펙트 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (푸시 안 함, 사용자 요청으로 보류)
- **한 일**: ① 내려찍기 4방향 동작 그림(PixelLab 핵심 자세 + 구간 잇기)과 충격 이펙트(짧은 금·돌 파편·먼지, 약한 흔들림)를 넣었다 (D-036).
  공격 동작 그림 고르기를 ①·③ 공용(`attack_frame`, `attack_squash`, `attack_sprite_path`)으로 묶었다.
- **현재 상태**: 테스트 231개 통과. 실제 pico2d 창 캡처로 들기 → 착지 → 이펙트 → 일어섬 확인
  (`assets/concepts/pixellab/golem_slam/ingame_capture_contact.png`, 서쪽을 볼 때). 직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: 그림을 다시 만들면 `assets/concepts/pixellab/golem_slam/build_golem_slam.py` (방향별 원본은 SOURCES)
  → `aligned/slam_*.png` 를 `assets/images/golem/` 로 복사. 이펙트는 `assets/concepts/vfx/slam/build_golem_slam_impact.py` 가
  `assets/images/effects/golem_slam.png` 까지 저장. PixelLab state: Slam Raise(3be21c60…), Slam Impact(b8f7f352…), Slam Impact Flat(6eedb94b…).
- **남은 문제 / 다음 할 일**: **후면 일어섬에서 팔이 먼저 옆으로 돌아감** (사용자 확인: 해결 안 됨, 시간이 없어 일단 적용).
  ② 앞차기·④ 레이저 동작 그림. 3×3 몸에 비해 그림이 작아 보일 수 있음.

---

## 2026-11-17 — 골렘 몸 3×3 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (골렘 작업 세션과 조율해 그 브랜치에 커밋)
- **한 일**: `GOLEM_SIZE` 2 → 3 (판정·이동). ①·② 가로 3 범위가 대칭이 됨. 2×2 설명·테스트 갱신 (D-035).
  게임 화면 위쪽 조작 안내·칸/상태 글자도 지움 (사용자 요청).
  이어서 골렘 공격 범위의 기준을 발 칸(몸 맨 아래 줄 가운데)으로 바꿈: ①·② 는 그 칸 바로 앞부터, ③ 은 그 칸 가운데 (D-035).
  ③ 은 8×8 → 7×7 (대칭), 바닥 이펙트도 7×7 크기로 그림 (`draw_tiles`).
  이어서 몸을 1×2(발 칸과 그 위 칸, `GOLEM_BODY`)로 줄이고, ④ 레이저는 시험을 위해 잠시 뺌 (`GOLEM_LASER_ENABLED = False`).
- **현재 상태**: 테스트 전체 통과. 실제 창 확인 못 함.
- **다음 작업**: 골렘 그림을 몸(3×3)에 맞춰 키울지 사용자 확인.

---

## 2026-11-17 — 골렘 걷기 4방향 동작 그림 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (아직 푸시 안 함, 사용자 요청으로 보류)
- **한 일**: PixelLab skeleton-v3 `walking-8-frames`(보폭 0.85·팔 0.6)로 골렘 걷기 4방향을 만들어 넣었다 (D-034).
  한 칸 옮겨 가는 동안 걸은 거리로 그림을 골라 발이 미끄러지지 않음. 동작 그림 그리기를 `_draw_anim` 으로 묶음.
- **현재 상태**: 테스트 223개 통과. 실제 pico2d 창 캡처로 측면·정면 걷기가 그려지는 것 확인
  (`assets/concepts/pixellab/golem_walk/ingame_capture_contact.png`). 직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: PixelLab 애니메이션 그룹 16d3588d(걷기 skeleton). 다시 만들면 `skeleton_4dir.png`(8장 × 4줄,
  south·east·north·west)를 바꾸고 `python assets/concepts/pixellab/golem_walk/build_golem_walk.py` → `aligned/walk_*.png` 를
  `assets/images/golem/` 로 복사. 그 폴더의 다른 시험 파일(v3_*, template_*, step_*)은 쓰지 않기로 한 시안이라 커밋하지 않았다.
- **남은 문제 / 다음 할 일**: ①·②·④ 동작 그림. 푸시·PR 은 사용자 결정 대기.

---

## 2026-11-17 — 골렘 발 구르기 4방향 동작 그림 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (아직 푸시 안 함, 사용자 요청으로 보류)
- **한 일**: PixelLab 으로 ③ 발 구르기 4방향 동작(무릎·팔을 높이 듦 → 쾅 → 깊게 쪼그린 반동 → 일어섬)을 만들어 넣었다 (D-033).
  구간마다 골렘이 아래로 밀리던 것을 `assets/concepts/pixellab/golem_stomp_anim/align_stomp_frames.py` 로 맞춤.
  예고 동안 들기·멈춤·떨어짐, 터진 뒤 착지 붙잡기·눌림(squash)·반동. 바닥 이펙트·화면 흔들림(D-032)과 같은 순간.
- **현재 상태**: 테스트 220개 통과. **실제 pico2d 창에서 캡처로 확인**: 들기·떨어짐·착지·바닥 이펙트가 그려짐
  (`assets/concepts/pixellab/golem_stomp_anim/ingame_capture_contact.png`). 직접 조작해 본 확인은 아님.
- **다음 작업자가 알아야 할 것**: PixelLab 캐릭터 `Stone Golem Simple` 그룹에 state `Stomp High`(9d9160df…), `Stomp Impact`(cc05f941…)가 있고,
  애니메이션 그룹 f2ec79cc(들기)·267d684b(떨어짐)·ddace6bf(반동)에 4방향이 있다. 그림을 다시 만들면 방향별
  `<dir>_c_frames.png`(19장)를 만들고 `align_stomp_frames.py` → `aligned/` 를 `assets/images/golem/stomp_<dir>.png` 로 복사.
  이 브랜치에는 다른 세션의 정면 3타 커밋(a34feef·9f96988·cf627be)이 섞여 있다 (같은 내용이 `claude/pixellab-player-anims` 에도 있음).
- **남은 문제 / 다음 할 일**: ①·②·④·걷기 동작 그림. 옆모습 들기가 앞차기처럼 보이는 면. 푸시·PR 은 사용자 결정 대기.

---

## 2026-11-17 — 골렘 발 구르기 바닥 이펙트 + 화면 흔들림 (Claude Code)

- **브랜치**: `claude/golem-stomp-vfx` (`claude/pixellab-player-anims` 위에서 시작)
- **한 일**: ③ 발 구르기가 터지는 순간 골렘 몸 가운데에서 바닥 이펙트(거미줄 금, 크레이터, 땅을 뚫고 솟았다 가라앉는 바닥 판,
  포물선으로 튀는 돌과 그림자, 먼지, 2.5초)를 재생하고 화면을 0.45초 흔든다 (D-032).
  `game/effects/effect.py` (SpriteEffect, ScreenShake), `Renderer.draw_sheet_frame`, 골렘 `effects`, FieldScene 재생·흔들림.
- **현재 상태**: 테스트 215개 통과(이펙트 7개 추가), 스모크 실행 성공. 그림은 Pillow 미리보기로 확인했고
  **실제 창에서 이펙트가 그려지는 것은 확인하지 못했다** (pico2d 시트 자르기 좌표 포함).
- **다음 작업자가 알아야 할 것**: 이펙트 그림을 바꾸려면 `python assets/concepts/vfx/stomp/build_golem_stomp.py` 를 실행하면
  `assets/images/effects/golem_stomp.png` 까지 다시 만든다 (Pillow 필요, 게임 실행에는 불필요).
  같은 폴더에서 다른 세션이 정면 3타 작업(`config.PLAYER_ATTACK_SWORD_FRONT` 등)을 하고 있어 그 변경은 이 브랜치에 넣지 않았다.
- **남은 문제 / 다음 할 일**: 이펙트를 인물보다 먼저 그려 골렘 앞으로 튄 돌도 인물 뒤에 보임. ①·②·④ 이펙트, 골렘 공격 애니메이션.

---

## 2026-11-17 — 주인공 그림 PixelLab 교체: 점프·측면 3타 (Claude Code)

- **브랜치**: `claude/pixellab-player-anims` (`claude/golem-sprite` 위에서 시작)
- **한 일**: PixelLab 으로 주인공 점프 4방향, 측면 1·2·3타를 다시 만들어 게임에 넣음. 걷기는 PixelLab 그림 두 가지를 넣어 봤으나
  사용자 판단으로 예전 그림(4프레임) 유지. 칼은 계속 분리(칼 그림 한 장 + 손 위치·각도 표).
  측면 공격은 8프레임 같은 간격, 0.675 / 0.675 / 0.75초, 판정 프레임 ⑤ ③ ⑤ (D-029).
- **현재 상태**: 테스트 197개 통과(예전 그림 전용 검사 2개를 새 그림 규칙으로 바꿈), 스모크 실행 성공.
  Pillow 로 `Player.draw` 를 그대로 그려 공격(오른쪽·왼쪽·아래)·걷기·점프를 캡처해 확인. 실제 창에서 직접 조작 확인은 안 함.
- **점프 (같은 날 이어서)**: 사용자와 여러 번 다시 그려 정면 `jump_v7` + 측면 `jump_v19` + 후면 `jump_v14` 로 결정.
  10프레임 0.7초, 착지 두 장, 후드 잡기 없음, 왼쪽은 측면 반전, 그림 48×56. 그림은 고치지 않고 자르기·순서·위치만 (D-029).
- **후딜 캔슬·걷다가 공격 (같은 날 이어서, D-030)**: 판정 뒤에는 회피·점프·패링으로 공격을 끊는다(3타는 쿨타임 유지).
  걷는 중 공격은 걷던 칸을 0.05초에 마저 간 뒤 시작. 테스트 204개 통과.
- **평타 판정·정면 공격 (같은 날 이어서, D-031)**: 1·2타 앞 1칸 × 가로 3칸, 3타 앞 2칸 × 1칸. 정면 1타만 PixelLab 그림,
  정면 2타는 이어서 v9(끝 자세를 create_character_state 로 만들어 지정)로 교체, 3타는 예전 5프레임, 후면은 측면 그림.
  정면 1·2타는 휘두르는 그림이 판정 시점에 맞게 프레임 표를 따로 둠. 테스트 208개 통과.
  이어서 정면 3타도 같은 방법(찌르기 끝 자세 지정)으로 PixelLab 두 손 찌르기로 교체 (사용자 확정). 테스트 215개 통과.
  찌르는 순간 다리가 잘려 보여(칼 아래 다리가 없음) 그 3프레임의 PixelLab 칼을 무기별 찌르기용 칼 그림
  (`weapons/old_sword_front_3.png`)으로 떼어 몸 위에 겹침. 칼 바꿔 끼우기 유지 (D-031). 새 무기는 이 그림도 만들어야 함.
  찌르기 직전 멈칫함은 프레임 시간 배분으로 고침 (2~4번째 빨리 넘김).
  핵심 자세는 `create_character_state`(10회분, 4방향)로 만들고 pixminimax 시작·끝 자세로 넣는 방법이 가장 잘 됨.
- **다음 작업자가 알아야 할 것**: 그림을 다시 만들면 `python assets/concepts/pixellab/player_import/export_to_game.py` 를 실행하고
  출력되는 `PLAYER_ATTACK_SWORD` 를 `game/config.py` 에 붙여 넣는다. 미리보기 GIF 는 `build_remake_preview.py`.
  정면 공격은 예전 5프레임 그림이라 `PLAYER_ATTACK_FRAME_ENDS_FRONT` 로 따로 프레임을 고른다.
- **남은 문제 / 다음 할 일**: 정면·후면 공격 PixelLab 교체, 골렘 공격 애니메이션 적용, 브랜치 정리(PR 순서대로 병합).

---

## 2026-11-17 — 골렘 그림 적용 (Claude Code)

- **브랜치**: `claude/golem-sprite` (`claude/golem` 위에서 시작)
- **한 일**: PixelLab 골렘 그림(`golem_simple` 상하좌우 4장)을 `assets/images/golem/` 으로 옮겨 적용. 바라보는 방향 그림을 2배로,
  발 밑을 2×2칸 바닥 가운데에 맞춤. 맞으면 깜빡임, 막대는 머리 위. 그림을 못 읽으면 임시 도형 (D-028).
- **현재 상태**: 테스트 198개 통과, 스모크 실행 성공, 실제 창 캡처로 네 방향·예고·조준선·겹침·STUN 확인
  (`assets/concepts/golem_sprite_ingame.png`). 직접 조작 확인은 안 함.
- **다음 작업자가 알아야 할 것**: 새 방향 그림으로 바꾸면 `config.GOLEM_SPRITE_FOOT_MARGIN` 을 그림의 발 아래 투명 줄 수에 맞춰야 한다
  (`tests/test_golem.py` 의 GolemSpriteTest 가 확인).
- **남은 문제 / 다음 할 일**: 골렘 공격 애니메이션(사용자 제작 예정), 사람형 몬스터, 사망, 브랜치 정리.

---

## 2026-11-17 — 골렘 조정·퍼펙트 회피·조작감 (Claude Code)

- **브랜치**: `claude/golem` (같은 브랜치에 이어서)
- **한 일**: 사용자 플레이 피드백 반영 — 주인공 이동 4칸/초, 골렘이 다가오게, 예고 단축(① 0.35 ② 0.55 ③ 0.55초), 공격 종류별 예고 색
  (빨강 패링 가능 / 노랑 패링 불가 / 하늘색 점프로만), 앞차기 가로 3 × 앞으로 5, 발 구르기 8×8, 레이저 조준점 4×4 폭발,
  몬스터형 패링 게이지 유지, 회피 2칸·대기 8초·퍼펙트 회피, 홀수 범위의 남는 줄은 아래쪽, 걷다가 바로 점프, 입력 기억 0.15초 (D-026, D-027).
- **현재 상태**: 테스트 190개 통과, 스모크 실행 성공, 실제 창 캡처 확인. 직접 조작 확인은 사용자가 하고 있음.
- **남은 문제 / 다음 할 일**: 골렘 부위별 그림, 사람형 몬스터, 사망·게임 오버, 회피·패링·피격 그림, 브랜치 정리(PR).

---

## 2026-11-17 — 골렘 (첫 일반 몬스터) (Claude Code)

- **브랜치**: `claude/golem` (`claude/dodge` 위에서 시작)
- **한 일**: 골렘(2×2, 몬스터형) 패턴 4종과 예고 칸 표시, 적 공격 판정(`EnemyAttack` → `Player.receive_attack`),
  패링 게이지(`PostureGauge`)·기절·패링 성공 우선권, 주인공 체력 100·hurt 경직·깜빡임, 체력·게이지 막대 (D-026).
  골렘 그림은 다리·몸통·팔·코어를 나눈 임시 도형.
- **현재 상태**: 테스트 177개 통과, 스모크 실행 성공, 실제 창 캡처로 네 패턴 예고·레이저 확인(`assets/concepts/golem_ingame.png`). 직접 조작해 본 확인은 안 함.
- **다음 작업자가 알아야 할 것**: 골렘 판단은 거리 기반이고 난수를 주입할 수 있다(`tests/test_golem.py` 의 FixedRng). 수치는 모두 `config.GOLEM_*`.
  예고 범위는 예고 시작 때 고정된다. 주인공은 사망이 미정이라 체력 0 이면 다시 채운다.
- **남은 문제 / 다음 할 일**: 사용자가 골렘 그림을 팔·다리 나눠 그릴 예정 → 부위별 그림 붙이기. 사람형 몬스터, 사망·게임 오버, 회피·패링·hurt 그림.

---

## 2026-11-17 — 회피 (Claude Code)

- **브랜치**: `claude/dodge` (`claude/attack-hit` 위에서 시작)
- **한 일**: Q 회피. `GridMover.dash` 로 최대 5칸을 0.25초에 미끄러짐(벽·허수아비 앞에서 멈춤), `dodge` 상태, 회피 중 무적(`is_invincible`),
  끝난 뒤 1초 대기, 걷기 그림 재생 (D-025). 패링 성공 효과·패링 게이지 규칙도 PRE-PRD 에 확정(구현은 몬스터 때).
- **현재 상태**: 테스트 159개 통과, 스모크 실행 성공, 실제 창 캡처 확인(`assets/concepts/dodge_ingame.png`). 직접 조작 확인은 안 함.
- **다음 작업자가 알아야 할 것**: 회피는 논리 위치를 시작 순간 도착 칸으로 옮긴다(한 칸 이동과 같은 규칙). 무적은 아직 확인하는 곳이 없다.
- **남은 문제 / 다음 할 일**: 일반 몬스터(사람형·몬스터형), 패링 성공 효과와 패링 게이지(PRE-PRD 2.2), 회피·정면·후면 그림.

---

## 2026-11-17 — 공격 판정 + 연습용 허수아비 (Claude Code)

- **브랜치**: `claude/attack-hit` (`claude/wall-collision` 위에서 시작)
- **한 일**: 칸 단위 공격 판정(`Strike`, `attack_tiles`), 휘두르는 프레임에 한 번, 1·2타 앞 1칸·3타 앞 2칸, 벽 너머 안 맞음.
  연습용 허수아비(맵 `D` 2개, 막힘, 깜빡임·흔들림·피해 숫자·체력 막대·쓰러졌다 다시 섬). 행 순서로 그리기 (D-024).
- **현재 상태**: 테스트 149개 통과, 스모크 실행 성공, 실제 창 캡처로 맞는 모습 확인(`assets/concepts/attack_hit_ingame.png`). 직접 조작 확인은 안 함.
- **다음 작업자가 알아야 할 것**: 주인공은 `Player.strikes` 로 공격을 내기만 하고, 맞히는 것은 `FieldScene.update` 가 한다. 몬스터도 같은 방식으로 붙이면 된다.
- **남은 문제 / 다음 할 일**: 사용자 제안 순서로 다음은 회피(키·거리·무적·대기 시간 [제안]) → 몬스터.

---

## 2026-11-17 — 글자 맵 + 벽 충돌 (Claude Code)

- **브랜치**: `claude/wall-collision` (`claude/player-sword-attack` 위에서 시작. 앞 PR들이 먼저 병합되어야 함)
- **한 일**: 글자 맵 파일 형식(`#` 벽, `.` 바닥, `P` 시작), 시험 맵 `assets/maps/test_room.txt`(32×18, 방 + 기둥·벽),
  `TileMap`·`can_enter`, 이동이 벽에 막힘(방향은 바뀜), 벽 단색 표시 (D-023).
- **현재 상태**: 테스트 140개 통과, 스모크 실행 성공, 실제 창 캡처로 벽에 막히는 것 확인. 키보드로 직접 조작해 본 확인은 안 함.
- **다음 작업자가 알아야 할 것**: 맵 파일은 맨 위 줄이 가장 위쪽 행이다. 맵 크기는 격자(`GRID_COLS × GRID_ROWS`)와 같아야 한다.
- **남은 문제 / 다음 할 일**: 사용자 제안 순서로 다음은 공격 판정 + 연습용 허수아비(판정 범위 [미정]). 타일 그림, 방 연결은 나중에.

---

## 2026-11-17 — 검 3단 콤보, 칼 분리, 두 손 잡기, 정면 공격 (Claude Code)

- **브랜치**: `claude/player-sword-attack` (`claude/player-jump-parry` 위에서 시작. 점프·패링 PR이 먼저 병합되어야 함)
- **한 일**: 3단 콤보(`SwordCombo`)와 3타 후 쿨타임, 칼 분리(칼 그림 한 장을 손 위치·각도로 돌려 그림), 두 손 잡기(칼 앞 레이어),
  낡은 검 도트, 측면·정면 공격 그림 (D-022).
- **현재 상태**: 테스트 129개 통과, 스모크 실행 성공, 실제 창 캡처로 측면(좌우)·정면 확인. 사용자가 측면은 "지금까지 중 제일 낫다"고 함.
- **다음 작업자가 알아야 할 것**:
  - 공격 그림 제작 흐름: ChatGPT 에 칼만 파란 단색(#0000FF)으로 그린 참고 시트(3행 × 5열, 초록 배경)를 받는다 →
    `python assets/concepts/build_attack_v3.py <시트> <출력>`(측면) 또는 `build_attack_view.py <시트> <front|back> <출력>` →
    출력의 시트를 `assets/images/player/sword_attack/` 로 복사하고 `sword_table.txt` 를 `game/config.py` 칼 위치표에 붙인다.
  - ChatGPT 요청문은 `assets/concepts/attack_reference_prompt.md`. 색 보정은 우리 쪽에서 하므로 ChatGPT 에는 자세·손·칼만 맡긴다.
  - 칼 그림은 `assets/concepts/weapons/build_old_sword.py` 의 칸 목록으로 고친다.
  - 커밋하지 않은 것: `assets/concepts/pixellab/` 새 실험 폴더, `anicraft/`, `handmade/`, `attack_*_out/`(변환 결과·미리보기), 기존부터 있던
    `assets/images/player/master/`, `palette.json`, `sprites.json`, `player_idle_walk_source_sheet.png`, 컨셉 시트 수정본.
- **남은 문제 / 다음 할 일**: 정면 그림을 자세 안내도(`attack_front_pose_guide.png`)로 다시 받기, 후면 그림, 공격 판정(범위 [미정]).
  사용자 제안 순서: 맵 + 벽 충돌 → 공격 판정 + 연습용 허수아비 → 회피 → 몬스터.

---

## 2026-11-16 — 검 공격 1타 (Claude Code)

- **브랜치**: `claude/player-sword-attack` (`claude/player-jump-parry` 위에서 시작. 점프·패링 PR이 먼저 병합되어야 함)
- **한 일**: PixelLab MCP로 공격 그림 생성 → 원본과 느낌이 달라 게임 Idle 후드를 붙이고 팔레트·망토·다리를 보정(v4).
  마우스 왼쪽 클릭 공격, `sword_attack` 상태, 64×64 공격 시트 그리기 (D-021).
- **현재 상태**: 테스트 114개 통과, 스모크 실행 성공. 사용자가 실제 창에서 확인하고 괜찮다고 함.
- **다음 작업자가 알아야 할 것**:
  - `assets/concepts/pixellab/`: `kit/`(PixelLab 기준 그림·가이드), `attack1_side_right_B/`(PixelLab 원본 프레임),
    `build_attack1_side_right.py`(v4 제작 스크립트, 이 폴더에서 실행). PixelLab 체험판은 `transfer_outfit` 등 pro 기능을 못 씀.
  - PixelLab 단독 생성은 후드·체형이 원본과 달라짐. 움직임만 가져오고 머리는 게임 픽셀을 쓰는 방식이 사용자 반응이 좋았음.
- **남은 문제 / 다음 할 일**: 사용자 요청 — 3단 콤보(1·2·3타 모두 다른 동작, 3타 찌르기), 3타 후 약 1초 쿨타임. 2타 동작·콤보 입력 시간은 미정.

---

## 2026-11-11 — 점프: 오른쪽 보기 손 위치 수정 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일**: 사용자 피드백(오른쪽 측면 손 위치가 어색함). 손이 후드 뒤쪽(귀 쪽)을 잡던 것을 팔을 몸 앞으로 들어 앞 챙을 잡게 수정.
  왼쪽 보기(먼 쪽 주먹이 앞 챙)와도 맞춤. `jump/side.png`만 바뀜.
- **현재 상태**: 테스트 통과, 실행 성공, 실제 창 캡처 확인. 키보드로 직접 조작해 본 확인은 안 함.

---

## 2026-11-11 — 점프: 자연스러운 후드 끌어내리기 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일**: 사용자 피드백(정면·후면 팔이 부자연스러움, 정면 외에는 후드가 안 내려가 보임) 반영.
  정면 팔을 몸 가까이 접어 챙을 잡게, 후면 팔 제거, 측면 손은 얼굴을 가리지 않게 후드 옆면으로.
  후드 내림 1→2→2→1줄, 측면은 앞으로 기울어지게.
- **현재 상태**: 테스트 통과, 실행 성공, 실제 창 캡처 확인. 키보드로 직접 조작해 본 확인은 안 함.

---

## 2026-11-11 — 점프: 후드 살짝 내림, 왼쪽 전용 그림 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일**: 후드를 잡는 동안 후드를 1줄 내림. 오른손 후드 잡기가 좌우 비대칭이라 `jump/side_left.png` 추가,
  `LEFT_SHEET_STATES`로 왼쪽을 볼 때 뒤집지 않고 전용 그림 사용 (D-020). PRE-PRD 2.5에 예외 추가.
- **현재 상태**: 테스트 통과, 실행 성공, 실제 창 캡처 확인. 키보드로 직접 조작해 본 확인은 안 함.

---

## 2026-11-11 — 점프: 후드 잡는 오른팔 전체 그리기 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일**: 사용자 피드백(정면 후드 잡기가 안 보임, 측면 손이 갑자기 나옴, 팔 느낌이 없음)으로 오른팔 전체를 그리고,
  손이 프레임마다 올라갔다 내려오게 함. 후면은 들린 팔꿈치가 보임.
- **현재 상태**: `python -m unittest` 105개 통과, 실행 성공, 실제 창 캡처 확인. 키보드로 직접 조작해 본 확인은 안 함.

---

## 2026-11-10 — 점프: 다리 간격 좁힘, 오른손 후드 잡기 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일**: 사용자 피드백(다리를 너무 벌림, 팔이 망토를 뚫음)으로 점프 5프레임 수정. 오른손은 후드를 잡고 왼손은 망토 안에 숨김,
  팔뚝은 실루엣 안쪽으로만. 웅크림만 1칸 벌리고 최고점 무릎·부츠는 모음.
- **현재 상태**: `python -m unittest` 105개 통과, 실행 성공, 실제 창 캡처 확인. 키보드로 직접 조작해 본 확인은 안 함.
- **남은 것**: 손이 2~3픽셀이라 작게 보임. 후면은 손이 보이지 않음.

---

## 2026-11-10 — 점프 모션을 더 역동적으로 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일**: 사용자 요청(다리가 상반신에 닿을 정도로 힘겹게)으로 점프를 5프레임으로 다시 그림. 최고점에 무릎을 벨트 높이까지 당긴 공 자세,
  다리 펴기 프레임 추가, 웅크림·도약 강화. `PLAYER_JUMP_FRAME_ENDS = (0.15, 0.3, 0.68, 0.85, 1.0)`, 0.6초.
- **현재 상태**: `python -m unittest` 105개 통과, 실행 성공, 실제 창 캡처로 4방향 확인. 키보드로 직접 조작해 본 확인은 안 함.

---

## 2026-11-10 — 높은 점프 모션, 패링 애니메이션 제거 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (같은 PR에 추가)
- **한 일 (사용자 피드백 반영)**
  - 패링 검 레이어 제거 (사용자가 요청하지 않음)
  - 점프: 높이 1칸·0.55초로 높게, 최고점에서 무릎을 가슴 쪽으로 당기는 모션. v3 Idle 위에 팔·다리를 v3 팔레트로 손그림 (`assets/README.md`)
  - 점프 프레임 구간을 `PLAYER_JUMP_FRAME_ENDS`로 지정해 최고점에 무릎 당김 프레임이 보이게 함
  - 패링 애니메이션 제거: F·판정 시간·상태는 유지, 그림은 서 있는 그림(`SPRITE_FALLBACK`). 공격 모션 때 함께 제작
- **현재 상태**: `python -m unittest` 105개 통과, `python main.py --frames 60` 실행 성공. 키보드로 직접 조작해 본 확인은 안 함.
- **다음 작업자가 알아야 할 것**: 그림은 ChatGPT 원본이 기준. 자세가 새로 필요한 경우만 Claude Code가 v3 위에 팔·다리를 덧그림.

---

## 2026-11-10 — 주인공 점프·패링 (Claude Code)

- **브랜치**: `claude/player-jump-parry` (`claude/player-idle-walk-v3` 위에서 분기. 앞선 PR들이 아직 `main`에 병합되지 않음)
- **한 일**
  - `Space` 점프, `F` 패링. 상태 머신에 `jump`·`parry`, `game/player/actions.py`(`Jump`, `Parry`), 무기 레이어 그리기, 점프 그림자 (D-019)
  - 에셋: `jump/`·`parry/`(v3 Idle 재조립), `shadow.png` — 모두 임시 에셋 (`assets/README.md`). 처음에 넣었던 패링 검은 사용자 요청이 아니어서 제거
  - PRE-PRD 2.1·2.2·2.7 점프·패링 규칙 확정 (사용자 승인)
- **현재 상태**: `python -m unittest` 105개 통과, `python main.py --frames 60` 실행 성공.
  실제 창 캡처(코드로 입력)에서 4방향 점프(그림자·높이)·패링·Idle 복귀 확인. **키보드로 직접 조작해 본 확인은 안 함.**
- **다음 작업자가 알아야 할 것**
  - 패링 성공 판정은 `player.parry.is_active`, 점프 공중 여부는 `player.jump.is_airborne`. 몬스터 공격 처리에서 이 값을 쓰면 된다.
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
