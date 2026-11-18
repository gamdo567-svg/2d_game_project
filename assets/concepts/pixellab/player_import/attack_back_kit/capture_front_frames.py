"""실제 pico2d 창: 정면(아래를 볼 때) 1·2·3타의 8장을 게임 그대로 잡아 ChatGPT 키트용 그림으로 (2026-11-18).

공격 버튼을 누르고 있어 1 → 2 → 3타로 이어 가며, 타마다 그림(프레임)이 바뀌는 순간을 한 장씩 모은다.
출력: <out>/front_hit<N>_8frames_x5.png (번호 1~8), <out>/front_hit<N>_8frames_mirror_x5.png (좌우 뒤집음 = 뒤에서 본 좌우)
"""
import ctypes
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
import pico2d  # noqa: E402
import pico2d.pico2d as P  # noqa: E402
import sdl2  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from game import config  # noqa: E402
from game.input.input_state import Action, InputState  # noqa: E402
from game.player import player as pl  # noqa: E402
from game.player.facing import Facing  # noqa: E402
from game.render.renderer import Renderer  # noqa: E402
from game.scenes.field_scene import FieldScene  # noqa: E402
from game.world.grid import Grid  # noqa: E402

OUT = sys.argv[1]
VIEW = sys.argv[2] if len(sys.argv) > 2 else 'front'  # 'back' 이면 위를 보고 후면 1~3타를 잡는다
FLOOR = {(24, 20, 32), (52, 46, 68)}  # 바닥·격자 색 → 회색 (ChatGPT 에 넘길 때 배경을 단색으로)


def to_grey(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] in FLOOR:
                px[x, y] = (128, 128, 128)
    return im

pico2d.open_canvas(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, sync=False)
renderer = Renderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
scene = FieldScene(Grid(config.GRID_COLS, config.GRID_ROWS, config.RENDER_TILE_SIZE))
scene.golems.clear()
scene.dummies.clear()
p = scene.player
p.facing = Facing.DOWN if VIEW == 'front' else Facing.UP
inp = InputState()
inp.press(Action.ATTACK)
got = {}
for k in range(600):
    scene.update(1 / 120, inp)
    inp.begin_frame()
    cur = p.combo.current
    if p.state != pl.ATTACK or cur.finished:
        if len(got) >= 24:
            break
        continue
    ends = pl.ATTACK_FRAME_ENDS[VIEW][p.combo.index]
    fr = pl.frame_for_progress(cur.progress, ends) if ends else min(7, int(cur.progress * 8))
    key = (p.combo.index, fr)
    if key in got:
        continue
    scene.draw(renderer)
    buf = ctypes.create_string_buffer(w * h * 4)
    sdl2.SDL_RenderReadPixels(P.renderer, None, sdl2.SDL_PIXELFORMAT_ABGR8888, buf, w * 4)
    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'RGBA', 0, 1)
    got[key] = to_grey(im.crop((w // 2 - 80, h // 2 - 96, w // 2 + 80, h // 2 + 62)).convert('RGB'))
    pico2d.update_canvas()
    pico2d.clear_canvas()
pico2d.close_canvas()
print(sorted(got))
for hit in (1, 2, 3):
    for mirror in (False, True):
        sheet = Image.new('RGB', (160 * 8, 158 + 30), (128, 128, 128))
        d = ImageDraw.Draw(sheet)
        for f in range(8):
            im = got.get((hit - 1, f))
            if im is None:
                continue
            # 게임 바닥(어두운 배경)을 회색으로: 아주 어두운 바닥·격자 색만 바꾼다
            im = im.transpose(Image.FLIP_LEFT_RIGHT) if mirror else im
            sheet.paste(im, (f * 160, 30))
            d.text((f * 160 + 76, 8), str(f + 1), fill=(255, 255, 255))
        name = f'{VIEW}_hit{hit}_8frames{"_mirror" if mirror else ""}_x5.png'
        sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(OUT, name))
