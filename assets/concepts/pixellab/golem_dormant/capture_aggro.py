"""실제 pico2d 창: 휴면 골렘 → 주인공이 6칸 안으로 다가감 → 코어가 켜지며 깨어나고 붉은 ! (확인용 GIF)."""
import ctypes
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
import pico2d  # noqa: E402
import pico2d.pico2d as P  # noqa: E402
import sdl2  # noqa: E402
from PIL import Image  # noqa: E402

from game import config  # noqa: E402
from game.input.input_state import Action, InputState  # noqa: E402
from game.render.renderer import Renderer  # noqa: E402
from game.scenes.field_scene import FieldScene  # noqa: E402
from game.world.grid import Grid  # noqa: E402

OUT = sys.argv[1]
pico2d.open_canvas(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, sync=False)
r = Renderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
s = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
s.dummies.clear()
golem = s.golems[0]
inp = InputState()
w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
frames = []
for k in range(200):
    if k == 20:
        inp.press(Action.MOVE_RIGHT)  # 골렘 쪽으로 걸어감
    if golem.state != 'dormant' and k > 20:
        inp.release(Action.MOVE_RIGHT)
    s.update(1 / 60, inp)
    inp.begin_frame()
    s.draw(r)
    buf = ctypes.create_string_buffer(w * h * 4)
    sdl2.SDL_RenderReadPixels(P.renderer, None, sdl2.SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'RGBA', 0, 1).convert('RGB')
    frames.append(im.crop((180, 80, 1000, 460)))
    pico2d.update_canvas()
    pico2d.clear_canvas()
pico2d.close_canvas()
pal = [f.convert('P', palette=Image.ADAPTIVE) for f in frames]
pal[0].save(OUT + '.gif', save_all=True, append_images=pal[1:], duration=17, loop=0)
pal[0].save(OUT + '_slow.gif', save_all=True, append_images=pal[1:], duration=45, loop=0)
print('ok', golem.state)
