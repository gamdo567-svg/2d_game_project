"""실제 pico2d 창: 서기 정면·측면·후면 + 후면 1타 베는 순간 (망토 명암 비교용)."""
import ctypes
import sys

sys.path.insert(0, r"C:\Users\gamdo\2d_game_project")
import pico2d  # noqa: E402
import sdl2  # noqa: E402
from PIL import Image  # noqa: E402

from game import config  # noqa: E402
from game.input.input_state import Action, InputState  # noqa: E402
from game.player.facing import Facing  # noqa: E402
from game.render.renderer import Renderer  # noqa: E402
from game.scenes.field_scene import FieldScene  # noqa: E402
from game.world.grid import Grid  # noqa: E402
import pico2d.pico2d as P  # noqa: E402

OUT = sys.argv[1]
pico2d.open_canvas(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, sync=False)
renderer = Renderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT


def shot(facing, attack_frames=0, wait=10):
    scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
    scene.golems.clear()
    scene.dummies.clear()
    scene.player.facing = facing
    inp = InputState()
    for k in range(wait + attack_frames):
        if attack_frames and k == wait:
            inp.press(Action.ATTACK)
        scene.update(1 / 60, inp)
        inp.begin_frame()
        inp.release(Action.ATTACK)
    scene.draw(renderer)
    buf = ctypes.create_string_buffer(w * h * 4)
    sdl2.SDL_RenderReadPixels(P.renderer, None, sdl2.SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", 0, 1).crop((w // 2 - 80, h // 2 - 120, w // 2 + 80, h // 2 + 40))
    pico2d.update_canvas()
    pico2d.clear_canvas()
    return im.convert("RGB")


ims = [shot(Facing.DOWN), shot(Facing.RIGHT), shot(Facing.UP), shot(Facing.DOWN, 22), shot(Facing.UP, 22), shot(Facing.UP, 34)]
pico2d.close_canvas()
out = Image.new("RGB", (160 * len(ims) * 2, 160 * 2))
for i, im in enumerate(ims):
    out.paste(im.resize((320, 320), Image.NEAREST), (i * 320, 0))
out.save(f"{OUT}/views_still_x2.png")
print("ok")
