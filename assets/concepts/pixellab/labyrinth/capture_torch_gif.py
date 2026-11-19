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
w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
frames = []
for k in range(90):
    s.update(1 / 30, inp); inp.begin_frame()
    s.draw(r)
    buf = ctypes.create_string_buffer(w * h * 4)
    sdl2.SDL_RenderReadPixels(P.renderer, None, sdl2.SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", 0, 1).convert("RGB")
    frames.append(im.crop((80, 40, 700, 440)).convert("P", palette=Image.ADAPTIVE))
    pico2d.update_canvas(); pico2d.clear_canvas()
pico2d.close_canvas()
frames[0].save(sys.argv[1], save_all=True, append_images=frames[1:], duration=33, loop=0)
frames[0].convert("RGB").save(sys.argv[1].replace(".gif", "_still.png"))
print("ok")
