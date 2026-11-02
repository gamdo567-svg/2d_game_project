"""게임 실행 진입점.

사용법:
    python main.py              # 게임 실행 (ESC 로 종료)
    python main.py --frames 60  # 60프레임 실행 후 자동 종료 (자동 테스트용)
"""
from __future__ import annotations

import argparse
import sys


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("1 이상의 정수여야 합니다.")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="2D Action RPG (Python + Pico2D)")
    parser.add_argument(
        "--frames",
        type=_positive_int,
        default=None,
        help="지정한 프레임 수만큼 실행한 뒤 자동 종료합니다 (자동 테스트용).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # pico2d 는 여기서 불러온다. --help 는 pico2d 없이도 동작한다.
    from game.core.app import run

    frames = run(max_frames=args.frames)
    if args.frames is not None:
        print(f"[smoke] {frames} frames OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
