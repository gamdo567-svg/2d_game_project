import ctypes, sys
sys.path.insert(0, r"C:\Users\gamdo\2d_game_project")
import pico2d, sdl2
import pico2d.pico2d as P
from PIL import Image
from game import config
from game.input.input_state import InputState
from game.render.renderer import Renderer
from game.scenes.field_scene import FieldScene
from game.world.grid import Grid
pico2d.open_canvas(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, sync=False)
r = Renderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
s = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
inp = InputState()
if len(sys.argv) > 3:  # 주인공을 이 칸에 세움 (벽 뒤에 선 모습 확인용)
    m = s.player.mover
    m.col, m.row = int(sys.argv[2]), int(sys.argv[3])
    m._from_col, m._from_row = m.col, m.row
for _ in range(10):
    s.update(1 / 60, inp); inp.begin_frame()
s.draw(r)
w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
buf = ctypes.create_string_buffer(w * h * 4)
sdl2.SDL_RenderReadPixels(P.renderer, None, sdl2.SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", 0, 1).convert("RGB").save(sys.argv[1])
pico2d.close_canvas()
print("ok")
