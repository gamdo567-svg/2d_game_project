"""퍼펙트 회피 잔상 그림 (2026-11-18 사용자 요청): 회피 그림(assets/images/player/dodge/<view>.png)을 하늘색으로 바꾼다.
테두리(가장 어두운 색)는 짙은 하늘색, 나머지는 밝기에 따라 옅은 하늘색 단계로. 게임이 비쳐 보이게(opacity) 그린다.
출력: assets/images/player/dodge_ghost/<view>.png (회피 그림과 같은 크기·칸)
실행: python build_dodge_ghost.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SRC = ROOT / 'assets/images/player/dodge'
OUT = ROOT / 'assets/images/player/dodge_ghost'
RAMP = [(90, 140, 220), (140, 200, 255), (191, 230, 255), (238, 248, 254)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for view in ('front', 'side', 'back'):
        im = Image.open(SRC / f'{view}.png').convert('RGBA')
        px = im.load()
        lums = sorted({sum(px[x, y][:3]) for y in range(im.height) for x in range(im.width) if px[x, y][3]})
        lo, hi = lums[0], lums[-1]
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if not a:
                    continue
                t = (r + g + b - lo) / max(1, hi - lo)
                px[x, y] = RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))] + (255,)
        im.save(OUT / f'{view}.png')
    print('ok')


if __name__ == '__main__':
    main()
