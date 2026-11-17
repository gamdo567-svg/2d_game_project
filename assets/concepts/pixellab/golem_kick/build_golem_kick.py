"""골렘 ② 올려차기 4방향 프레임 정리 + 미리보기.

2026-11-18: PixelLab 만으로는 방향마다 차는 다리가 바뀌거나 다리가 늘어나고 후면을 못 그렸다
(first_try/, rise_try/, short_try/, skeleton_try/). 그래서 핵심 자세(준비·차기)를 ChatGPT 이미지로 그리고
(chatgpt_kit/result_<dir>.png → process_results.py → chatgpt_kit/keys/), 서기→준비, 차기→서기 사이만 PixelLab 으로 채웠다.

입력
- kick_<dir>_frames.png : join 결과 14장 (들기 0~6: 서기 → 준비 / 되돌아옴 7~13: 차기 → 서기). 칸 크기는 SIZES.
- chatgpt_kit/keys/<dir>_{windup,kick}.png : 핵심 자세 원본 (128×128, 발 밑 = 서 있는 그림과 같은 자리)
조립 (11장): 들기 0~2 → 준비(핵심 그림) → 차기(핵심 그림) → 되돌아옴 8~13
- 들기 마지막 장(6)·되돌아옴 첫 장(7)은 PixelLab 이 흐리게 그린 경우가 있어 핵심 그림으로 바꾼다.
- 몸에서 떨어진 작은 점(PixelLab 이 그린 흰 부스러기)은 지운다.
- 들기 구간은 첫 장(서기)을, 되돌아옴 구간은 끝 장(서기)을 서 있는 그림의 발 밑에 맞춘다.
출력: aligned/kick_<dir>.png (가로 한 줄 11장, CANVAS), kick_4dir_preview.gif
실행: python build_golem_kick.py
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "aligned"
KEYS = HERE / "chatgpt_kit" / "keys"
DIRS = ("south", "east", "north", "west")
SIZES = {"south": (148, 128), "east": (140, 128), "north": (140, 128), "west": (132, 128)}
CANVAS = (160, 144)
FOOT = (80, 132)  # 서 있는 그림의 발 밑 가운데가 놓일 자리
LIFT = 3  # 들기는 앞 3장만 (뒤쪽은 측면에서 몸이 정면으로 돌아가는 경우가 있어 버림)
WINDUP, KICK = LIFT, LIFT + 1  # 조립된 장에서 준비·차기 장 (모두 11장: 들기 0~2, 준비 3, 차기 4, 되돌아옴 5~10)
MIN_SPECK = 60  # 이보다 작은 떨어진 덩어리(PixelLab 흰 궤적·부스러기)는 지움


def cells(name):
    w, h = SIZES[name]
    im = Image.open(HERE / f"kick_{name}_frames.png").convert("RGBA")
    cols = im.width // w
    return [im.crop(((i % cols) * w, (i // cols) * h, (i % cols) * w + w, (i // cols) * h + h)) for i in range(14)]


def foot(b):
    return (b[0] + b[2]) / 2, b[3]


def drop_specks(im: Image.Image) -> Image.Image:
    im = im.copy()
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    for sy in range(h):
        for sx in range(w):
            if seen[sy * w + sx] or px[sx, sy][3] == 0:
                continue
            comp, q = [], deque([(sx, sy)])
            seen[sy * w + sx] = 1
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny][3]:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            if len(comp) < MIN_SPECK:
                for x, y in comp:
                    px[x, y] = (0, 0, 0, 0)
    return im


def place(img: Image.Image, ref_foot: tuple[float, int]) -> Image.Image:
    c = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    c.alpha_composite(img, (round(FOOT[0] - ref_foot[0]), FOOT[1] - ref_foot[1]))
    return c


def build():
    OUT.mkdir(exist_ok=True)
    sets = {}
    for name in DIRS:
        if name == "west":
            # 서쪽 생성본은 흰 궤적이 몸에 붙어 남아, 깨끗한 동쪽 전체를 좌우 반전해 쓴다 (골렘은 좌우 대칭,
            # 전체를 뒤집으므로 준비·차기 다리는 그대로 같은 다리)
            frames = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in sets["east"]]
            assert FOOT[0] * 2 == CANVAS[0]
            sets[name] = frames
            strip = Image.new("RGBA", (CANVAS[0] * len(frames), CANVAS[1]), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                strip.paste(f, (i * CANVAS[0], 0))
            strip.save(OUT / f"kick_{name}.png")
            continue
        fr = [drop_specks(f) for f in cells(name)]
        lift_ref = foot(fr[0].getbbox())        # 들기 첫 장 = 서기
        back_ref = foot(fr[13].getbbox())       # 되돌아옴 끝 장 = 서기
        idle_ref = foot(Image.open(KEYS / f"{name}_stand.png").getbbox())
        key_w = Image.open(KEYS / f"{name}_windup.png").convert("RGBA")
        key_k = Image.open(KEYS / f"{name}_kick.png").convert("RGBA")
        frames = [place(f, lift_ref) for f in fr[0:LIFT]]
        # 핵심 그림은 서 있는 그림(stand)과 같은 캔버스·같은 발 자리로 정리돼 있다
        frames += [place(key_w, idle_ref), place(key_k, idle_ref)]
        frames += [place(f, back_ref) for f in fr[8:14]]
        sets[name] = frames
        strip = Image.new("RGBA", (CANVAS[0] * len(frames), CANVAS[1]), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            strip.paste(f, (i * CANVAS[0], 0))
        strip.save(OUT / f"kick_{name}.png")
        boxes = [f.getbbox() for f in frames]
        print(name, "범위", min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
              max(b[3] for b in boxes))
    return sets


def preview(sets):
    T, N, SC, TICK = 32, 8, 2, 1 / 24
    SZ = N * T
    floor = Image.new("RGBA", (SZ, SZ), (88, 84, 80, 255))
    d = ImageDraw.Draw(floor)
    for x in range(0, SZ, T):
        for y in range(0, SZ, T):
            d.rectangle((x, y, x + T - 1, y + T - 1), outline=(76, 72, 68, 255))
    seq = [i for i in range(WINDUP) for _ in range(2)] + [WINDUP] * 6 + [KICK] * 5
    seq += [i for i in range(KICK + 1, len(sets["south"])) for _ in range(2)] + [0] * 10
    shake = [(0, 0), (2, -1), (-2, 1), (1, 0)]
    out, k = [], 0
    for gi in seq:
        sh = shake[k] if gi == KICK and k < len(shake) else (0, 0)
        k = k + 1 if gi == KICK else 0
        sheet = Image.new("RGBA", (SZ * 2, SZ * 2), (30, 28, 32, 255))
        for n, name in enumerate(DIRS):
            world = floor.copy()
            world.alpha_composite(sets[name][gi], (SZ // 2 - FOOT[0], SZ // 2 + T - FOOT[1]))
            ImageDraw.Draw(world).text((4, 4), name, fill=(255, 255, 255, 255))
            screen = Image.new("RGBA", (SZ, SZ), (30, 28, 32, 255))
            screen.alpha_composite(world, sh)
            sheet.paste(screen, ((n % 2) * SZ, (n // 2) * SZ))
        out.append(sheet.resize((SZ * 2 * SC, SZ * 2 * SC), Image.NEAREST))
    out[0].save(HERE / "kick_4dir_preview.gif", save_all=True, append_images=out[1:],
                duration=round(TICK * 1000), loop=0)


if __name__ == "__main__":
    preview(build())


