"""실행 스모크 테스트: main.py 를 실제로 띄워 몇 프레임 실행한 뒤 정상 종료되는지 확인한다.

- pico2d 가 설치되어 있지 않으면 건너뛴다.
- 기본적으로 SDL 더미 드라이버를 사용하므로 창이 뜨지 않는다.
  (환경 변수 SDL_VIDEODRIVER 를 직접 지정하면 그 값을 따른다.)
"""
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipIf(importlib.util.find_spec("pico2d") is None, "pico2d 가 설치되어 있지 않음")
class SmokeTest(unittest.TestCase):
    def test_game_runs_and_exits(self):
        env = os.environ.copy()
        env.setdefault("SDL_VIDEODRIVER", "dummy")
        env.setdefault("SDL_AUDIODRIVER", "dummy")
        result = subprocess.run(
            [sys.executable, "main.py", "--frames", "30"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[smoke] 30 frames OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
