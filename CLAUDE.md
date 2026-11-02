# CLAUDE.md — Claude Code 전용 지침

Claude Code는 **`AGENTS.md`의 공통 규칙을 모두 따릅니다.**
아래 두 문서는 import 문법으로 자동으로 함께 읽힙니다.

@AGENTS.md
@PRE-PRD.md

---

## 세션 시작 시

1. `git fetch origin` 후 `git status`로 현재 브랜치와 원격 차이를 확인합니다.
2. `TASKS.md`와 `docs/HANDOFF.md`의 최신 항목을 읽습니다. 다른 AI(Codex)가 남긴 작업이 있는지 확인합니다.
3. 새 작업은 최신 `origin/main`에서 `claude/<작업-이름>` 브랜치를 만들어 시작합니다.

## Claude Code 전용 규칙

- **브랜치 접두사**: `claude/`
- **계획 먼저**: 여러 파일에 걸친 기능이나 구조 변경은 구현 전에 계획을 사용자에게 설명합니다.
- **범위 지키기**: 요청받은 기능만 구현합니다. 이어서 할 만한 작업은 보고서의 "다음 작업"에 적습니다.
- **패키지 설치**: `pip install`로 새 패키지를 설치하거나 `requirements.txt`를 바꾸기 전에 사용자 승인을 받습니다.
- **커밋 메시지**: 제목 줄은 `AGENTS.md` 5.3 형식을 지킵니다. Claude Code 꼬리말(`Co-Authored-By:` 등)은 본문 아래에 둡니다.
- **화면 없는 환경**: 실제 그리기 확인이 필요하면 `xvfb-run -a python main.py --frames 120` 등을 사용하고,
  실제 모니터에서 확인하지 못했다는 사실을 보고에 적습니다.
- **세션 종료 시**: `TASKS.md`와 `docs/HANDOFF.md`를 갱신해 커밋한 뒤, 가능하면 브랜치를 푸시합니다.
- **보고**: 작업마다 `AGENTS.md` 7장의 보고 형식으로 결과를 알립니다.
