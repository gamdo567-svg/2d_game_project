"""실제 pico2d 창: 허수아비를 옆에서 몇 번 때려 흔들림·망가짐·무너짐·다시 서기를 GIF 로 (확인용)."""
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
from game.input.input_state import InputState  # noqa: E402
from game.render.renderer import Renderer  # noqa: E402
from game.scenes.field_scene import FieldScene  # noqa: E402
from game.world.grid import Grid  # noqa: E402

OUT = sys.argv[1]
pico2d.open_canvas(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, sync=False)
r = Renderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
s = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
s.golems.clear()
dummy = s.dummies[0]
inp = InputState()
w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
# (프레임, 피해, 방향): 오른쪽에서·왼쪽에서·위에서 번갈아 때림
hits = {10: (12, (1, 0)), 45: (12, (-1, 0)), 80: (14, (0, 1)), 115: (12, (1, 0)), 150: (12, (-1, 0))}
frames = []
for k in range(330):
    if k in hits:
        dummy.take_hit(*hits[k])
    s.update(1 / 60, inp)
    inp.begin_frame()
    s.draw(r)
    buf = ctypes.create_string_buffer(w * h * 4)
    sdl2.SDL_RenderReadPixels(P.renderer, None, sdl2.SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'RGBA', 0, 1).convert('RGB')
    left, bottom, right, top = s.grid.tile_to_pixel_rect(dummy.col, dummy.row)
    cx, cy = int((left + right) / 2), h - int(bottom)
    frames.append(im.crop((cx - 110, cy - 170, cx + 110, cy + 30)))
    pico2d.update_canvas()
    pico2d.clear_canvas()
pico2d.close_canvas()
pal = [f.convert('P', palette=Image.ADAPTIVE) for f in frames]
pal[0].save(OUT + '.gif', save_all=True, append_images=pal[1:], duration=17, loop=0)
pal[0].save(OUT + '_slow.gif', save_all=True, append_images=pal[1:], duration=50, loop=0)
strip = Image.new('RGB', (220 * 10, 200))
for i, k in enumerate((5, 14, 20, 28, 48, 84, 152, 158, 175, 300)):
    strip.paste(frames[k], (i * 220, 0))
strip.save(OUT + '_strip.png')
print('ok')
