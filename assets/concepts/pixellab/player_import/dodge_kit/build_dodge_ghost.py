"""퍼펙트 회피 잔상 그림 (2026-11-18 사용자 요청): 회피 그림(assets/images/player/dodge/<view>.png)을 그림자로 바꾼다.
~~하늘색~~ → 그림자 느낌 (같은 날 사용자 요청: 하늘색은 캐릭터 컨셉과 안 어울림): 몸은 바닥보다 어두운 검보라 단계,
테두리(가장 어두운 색)만 살짝 밝은 보라로 남겨 어두운 바닥에서도 모양이 읽히게. 게임이 비쳐 보이게(opacity) 그린다.
출력: assets/images/player/dodge_ghost/<view>.png (회피 그림과 같은 크기·칸)
실행: python build_dodge_ghost.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SRC = ROOT / 'assets/images/player/dodge'
OUT = ROOT / 'assets/images/player/dodge_ghost'
RAMP = [(6, 4, 10), (12, 9, 17), (19, 14, 25), (27, 20, 34)]  # 몸: 어두운 곳 → 밝은 곳 (바닥 (24, 20, 32) 보다 어둡게)
RIM = (58, 40, 70)  # 테두리


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for view in ('front', 'side', 'back'):
        im = Image.open(SRC / f'{view}.png').convert('RGBA')
        px = im.load()
        lums = sorted({sum(px[x, y][:3]) for y in range(im.height) for x in range(im.width) if px[x, y][3]})
        lo, hi = lums[0], lums[-1]
        solid = lambda x, y: 0 <= x < im.width and 0 <= y < im.height and px[x, y][3] > 0  # noqa: E731
        edge = {(x, y) for y in range(im.height) for x in range(im.width) if solid(x, y)
                and not all(solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if not a:
                    continue
                if (x, y) in edge:
                    px[x, y] = RIM + (255,)
                    continue
                t = (r + g + b - lo) / max(1, hi - lo)
                px[x, y] = RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))] + (255,)
        im.save(OUT / f'{view}.png')
    print('ok')


if __name__ == '__main__':
    main()
