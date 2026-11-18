"""후면 공격 흔들림 줄이기: 후드를 서기 그림의 후드로 바꿔 끼운다 (2026-11-19 사용자: 픽셀을 잘못 그려 생기는 흔들림).

후면 공격 8장은 장마다 따로 그려 후드 모양·너비(17~20 픽셀)·테두리가 장마다 달라 재생하면 머리가 꿈틀거렸다.
화면에서 가장 크게 보이는 후드를 게임 뒷모습 서기 그림(idle/back.png 첫 장)의 후드와 똑같이 맞춘다:
장마다 후드 꼭대기·가운데를 찾아 그 자리에 서기 그림 후드(2~18줄)를 놓고, 그 줄들에서 서기 후드 밖으로 삐져나온
예전 후드 픽셀은 지운다. 같은 서기 후드에서 늘 다시 만들므로 여러 번 돌려도 결과가 같다.
export_to_game.py 가 후면 공격 그림을 쓴 뒤 apply_sheet 를 부른다.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYER = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'images', 'player'))
HOOD_ROWS = (2, 18)  # 서기 그림(32×48)에서 후드 줄 (꼭대기 ~ 어깨 위 테두리 전)
CLEAR_ROWS = 12  # 후드 위쪽 이만큼 줄에서만 서기 후드 밖 픽셀을 지운다 (아래는 팔·어깨가 붙어 있을 수 있음)


def is_body(c):
    """몸 픽셀: 불투명하고 잔상(흰빛)이 아님."""
    return c[3] > 128 and not (c[0] > 200 and c[2] > 200)


def idle_hood():
    idle = Image.open(os.path.join(PLAYER, 'idle', 'back.png')).convert('RGBA').crop((0, 0, 32, 48))
    y0, y1 = HOOD_ROWS
    hood = idle.crop((0, y0, 32, y1 + 1))
    xs = [x for y in range(hood.height) for x in range(32) if hood.getpixel((x, y))[3] > 128]
    return hood, (min(xs) + max(xs)) / 2


def hood_anchor(frame):
    """장의 후드 꼭대기 줄과 가로 가운데 (꼭대기에서 6줄)."""
    px = frame.load()
    rows = [y for y in range(frame.height) if any(is_body(px[x, y]) for x in range(frame.width))]
    top = rows[0]
    xs = [x for y in range(top, top + 7) for x in range(frame.width) if is_body(px[x, y])]
    return top, (min(xs) + max(xs)) / 2


def apply_frame(frame, hood, hood_cx):
    out = frame.copy()
    px = out.load()
    top, cx = hood_anchor(frame)
    ox = round(cx - hood_cx)
    hpx = hood.load()
    mask = {(x + ox, y + top) for y in range(hood.height) for x in range(hood.width) if hpx[x, y][3] > 128}
    # 서기 후드 밖으로 삐져나온 예전 후드 픽셀 지우기 (위쪽 줄만, 잔상은 그대로)
    for y in range(top, top + CLEAR_ROWS):
        for x in range(frame.width):
            if (x, y) not in mask and is_body(px[x, y]):
                px[x, y] = (0, 0, 0, 0)
    for (x, y) in mask:
        if 0 <= x < out.width and 0 <= y < out.height:
            px[x, y] = hpx[x - ox, y - top]
    return out


def apply_sheet(path, frames=8, skip=()):
    """시트의 장마다 후드를 바꿔 끼운다. skip: 바꾸지 않을 장 번호(0 부터, 후드가 크게 기울거나 가려진 장)."""
    sheet = Image.open(path).convert('RGBA')
    w = sheet.width // frames
    hood, hood_cx = idle_hood()
    out = sheet.copy()
    for k in range(frames):
        if k in skip:
            continue
        cell = sheet.crop((k * w, 0, (k + 1) * w, sheet.height))
        out.paste(apply_frame(cell, hood, hood_cx), (k * w, 0))
    out.save(path)
