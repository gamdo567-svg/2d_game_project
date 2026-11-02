import unittest

from game import config
from game.input.input_state import InputState
from game.scenes.boot_scene import BootScene
from game.world.grid import Grid


class _RecordingRenderer:
    """pico2d 없이 그리기 호출을 기록하는 가짜 Renderer."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append(name)

        return record


def _run(scene, fps, seconds):
    input_state = InputState()
    dt = 1.0 / fps
    for _ in range(round(seconds * fps)):
        scene.update(dt, input_state)


class BootSceneTest(unittest.TestCase):
    def make_scene(self):
        return BootScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.TILE_SIZE))

    def test_marker_starts_at_grid_center(self):
        scene = self.make_scene()
        self.assertEqual((scene.marker_col, scene.marker_row), (16, 9))

    def test_time_progress_is_independent_of_fps(self):
        # 같은 실제 시간 동안 실행하면 FPS 가 달라도 결과가 같아야 한다.
        slow, fast = self.make_scene(), self.make_scene()
        _run(slow, fps=20, seconds=1.25)
        _run(fast, fps=200, seconds=1.25)
        self.assertAlmostEqual(slow.elapsed, fast.elapsed, places=6)
        self.assertEqual(slow.marker_visible, fast.marker_visible)

    def test_marker_blinks_every_interval(self):
        scene = self.make_scene()
        self.assertTrue(scene.marker_visible)
        _run(scene, fps=100, seconds=BootScene.BLINK_INTERVAL + 0.01)
        self.assertFalse(scene.marker_visible)
        _run(scene, fps=100, seconds=BootScene.BLINK_INTERVAL)
        self.assertTrue(scene.marker_visible)

    def test_fps_measurement(self):
        scene = self.make_scene()
        _run(scene, fps=60, seconds=1.0)
        self.assertAlmostEqual(scene.fps, 60.0, delta=1.0)

    def test_draw_uses_renderer_only(self):
        scene = self.make_scene()
        renderer = _RecordingRenderer()
        scene.draw(renderer)
        self.assertIn("fill_screen", renderer.calls)
        self.assertIn("draw_grid", renderer.calls)
        self.assertIn("fill_tile", renderer.calls)


if __name__ == "__main__":
    unittest.main()
