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
