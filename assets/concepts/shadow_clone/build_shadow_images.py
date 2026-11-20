"""그림자 분신 그림 (2026-11-20 사용자: 어둠 능력 — 3타를 다 때리면 그 자리에 그림자 분신, 반투명 검은 그림자 + 어둠 기운).

주인공 그림을 그림자로 바꾼다 (회피 잔상 dodge_kit/build_dodge_ghost.py 와 같은 방법): 몸은 바닥보다 어두운 검보라 단계,
테두리만 살짝 밝은 보라로 남겨 어두운 바닥에서도 모양이 읽히게. 게임이 비쳐 보이게(opacity) 그린다.
입력 → 출력 (같은 파일 이름, 같은 칸):
- player/sword_attack/*.png (공격 몸·오른손) → player/shadow/sword_attack/
- player/idle/*.png (서 있기)               → player/shadow/idle/
- player/weapons/old_sword.png, old_sword_front_3.png (칼, 찌르기용 칼) → player/shadow/weapons/
실행: python build_shadow_images.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PLAYER = ROOT / 'assets' / 'images' / 'player'
OUT = PLAYER / 'shadow'
RAMP = [(8, 5, 14), (15, 10, 22), (23, 16, 31), (32, 23, 42)]  # 몸: 어두운 곳 → 밝은 곳
RIM = (74, 50, 96)  # 테두리


def shadow(src: Path, dst: Path) -> None:
    im = Image.open(src).convert('RGBA')
    px = im.load()
    lums = sorted({sum(px[x, y][:3]) for y in range(im.height) for x in range(im.width) if px[x, y][3]})
    if not lums:
        im.save(dst)
        return
    lo, hi = lums[0], lums[-1]
    solid = lambda x, y: 0 <= x < im.width and 0 <= y < im.height and px[x, y][3] > 0  # noqa: E731
    edge = {(x, y) for y in range(im.height) for x in range(im.width) if solid(x, y)
            and not all(solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    out = im.copy()
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            if (x, y) in edge:
                po[x, y] = RIM + (a,)
                continue
            t = (r + g + b - lo) / max(1, hi - lo)
            po[x, y] = RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))] + (a,)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)


def main():
    for folder in ('sword_attack', 'idle'):
        for src in sorted((PLAYER / folder).glob('*.png')):
            shadow(src, OUT / folder / src.name)
    for name in ('old_sword.png', 'old_sword_front_3.png'):
        shadow(PLAYER / 'weapons' / name, OUT / 'weapons' / name)
    print('shadow images')


if __name__ == '__main__':
    main()
