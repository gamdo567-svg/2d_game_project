import unittest

from game.world.camera import Camera


class CameraTest(unittest.TestCase):
    def setUp(self):
        # 화면 1024×576, 맵 2048×1152 (32×18칸 × 64px)
        self.camera = Camera(1024, 576, 2048, 1152)

    def test_centers_target(self):
        self.camera.follow(1056, 608)
        self.assertEqual((self.camera.left, self.camera.bottom), (544, 320))

    def test_stops_at_map_edges(self):
        self.camera.follow(10, 10)
        self.assertEqual((self.camera.left, self.camera.bottom), (0, 0))
        self.camera.follow(5000, 5000)
        self.assertEqual((self.camera.left, self.camera.bottom), (2048 - 1024, 1152 - 576))

    def test_offset_is_whole_pixels(self):
        self.camera.follow(1000.4, 700.6)
        self.assertIsInstance(self.camera.left, int)
        self.assertIsInstance(self.camera.bottom, int)

    def test_small_map_is_centered(self):
        camera = Camera(1024, 576, 512, 576)
        camera.follow(100, 100)
        self.assertEqual((camera.left, camera.bottom), (-256, 0))

    def test_rejects_empty_view(self):
        with self.assertRaises(ValueError):
            Camera(0, 576, 100, 100)


if __name__ == "__main__":
    unittest.main()
