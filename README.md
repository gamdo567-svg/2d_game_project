# 2D Game Project

Python과 [Pico2D](https://pypi.org/project/pico2d/)로 만드는 **탑다운 2D 액션 RPG**입니다.

- 8방향 실시간 칸 이동
- 검술 · 회피 · 패링 전투
- 마법석을 검에 부여해 전투 능력이 바뀌는 성장
- 던전 탐험, 일반 몬스터, 보스전
- 픽셀풍 2D 그래픽

> **현재 상태: 초기 개발 환경 구성 완료.**
> 실행하면 칸 격자와 확인용 표식이 있는 창이 열립니다. 게임플레이 기능은 아직 없습니다.
> 기획은 [`PRE-PRD.md`](PRE-PRD.md), 진행 상황은 [`TASKS.md`](TASKS.md)를 참고하세요.

---

## 요구 사항

- Python **3.10 이상** (Python 3.13에서 검증)
- pico2d 1.5.1 (`requirements.txt`로 설치. SDL2 바이너리가 함께 설치됩니다)

## 설치

저장소 루트에서 가상 환경을 만들고 의존성을 설치합니다.

**Windows (PowerShell)**

```powershell
git clone https://github.com/gamdo567-svg/2d_game_project.git
cd 2d_game_project
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
git clone https://github.com/gamdo567-svg/2d_game_project.git
cd 2d_game_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> PyCharm을 사용한다면 프로젝트 인터프리터를 `.venv`로 지정하고 `main.py`를 실행하면 됩니다.

## 실행

```bash
python main.py
```

| 키 | 동작 |
|---|---|
| `ESC` | 종료 |
| 창 닫기 버튼 | 종료 |

화면 구성: **1024×576(16:9)** 창에 **32×32px 타일, 32×18 칸 격자**를 표시합니다. 왼쪽 아래 보라색 칸은 좌표 원점 `(0, 0)`, 중앙의 노란 표식은 0.5초마다 깜빡입니다(delta time 기반).

주인공 스프라이트 제작 기준은 **32×48px**입니다. 현재는 아직 실제 주인공 스프라이트가 구현되지 않았으며, 타일 충돌 영역과 스프라이트 표시 영역은 독립적으로 관리할 예정입니다.

## 테스트

```bash
python -m unittest           # 전체 테스트
python -m unittest -v        # 테스트 이름까지 출력
python main.py --frames 60   # 60프레임 실행 후 자동 종료
```

- `tests/test_smoke.py`는 창을 띄우지 않고(SDL 더미 드라이버) 게임을 30프레임 실행해 정상 종료를 확인합니다.
- pico2d가 설치되지 않은 환경에서는 스모크 테스트만 건너뛰고 나머지 로직 테스트는 실행됩니다.

## 폴더 구조

```
2d_game_project/
├── main.py              # 실행 진입점
├── requirements.txt
├── game/
│   ├── config.py        # 설정값 (화면·칸 크기, 시간, 색상)
│   ├── core/            # 메인 루프, delta time
│   ├── input/           # 입력 상태(Action), pico2d 이벤트 변환
│   ├── world/           # 칸 좌표 ↔ 픽셀 좌표 변환
│   ├── physics/         # 충돌 판정 (예정)
│   ├── render/          # pico2d 그리기
│   └── scenes/          # 장면
├── assets/              # images / sounds / fonts
├── tests/               # 단위 테스트, 스모크 테스트
└── docs/                # 인수인계, 기술 결정 기록
```

## 문서

| 문서 | 내용 |
|---|---|
| [`PRE-PRD.md`](PRE-PRD.md) | 게임 기획 기준 문서 ([확정] / [제안] / [미정] 구분) |
| [`AGENTS.md`](AGENTS.md) | Claude Code · Codex 공통 개발 지침 (코드·Git·커밋 규칙) |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code 전용 지침 |
| [`TASKS.md`](TASKS.md) | 기능별 개발 진행 상황 |
| [`docs/HANDOFF.md`](docs/HANDOFF.md) | AI 간 작업 인수인계 |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | 주요 기술적 결정 기록 |
| [`assets/README.md`](assets/README.md) | 에셋 규칙, 출처·라이선스 기록 |

## 개발 방식

Claude Code와 OpenAI Codex가 번갈아 개발하며, GitHub를 코드 공유의 기준으로 사용합니다.
`main` 브랜치는 항상 정상 동작하는 버전을 유지하고, 기능은 `claude/*` 또는 `codex/*` 브랜치에서 개발한 뒤 Pull Request로 병합합니다.
자세한 규칙은 [`AGENTS.md`](AGENTS.md)를 참고하세요.

## 문제 해결

| 증상 | 해결 |
|---|---|
| `ModuleNotFoundError: No module named 'pico2d'` | 가상 환경을 활성화했는지 확인하고 `pip install -r requirements.txt` 실행 |
| `ModuleNotFoundError: No module named 'game'` | 저장소 루트에서 `python main.py`로 실행 |
| `WARNING: Audio functions are disabled ...` | 사운드 장치가 없을 때 pico2d가 출력하는 경고입니다. 실행에는 문제 없습니다 |
| 화면 없는 서버에서 실행 | `SDL_VIDEODRIVER=dummy python main.py --frames 60` (실행 확인만 가능) 또는 `xvfb-run -a python main.py --frames 60` |
