"""감전 그림 (2026-11-20 사용자: 감전되면 만화처럼 검정색 됐다가 하얀색 됐다가 찌릿찌릿).

서 있는 그림의 모양(알파)만 살려 검은 그림자·흰 그림 두 벌을 만든다. 게임은 감전 동안 이 둘과 원래 그림을 번갈아 그린다.
- 골렘: golem/<방향>.png (96×96, 방향마다 따로 그림) → golem/shock_<방향>_black.png, _white.png
- 허수아비: dummy/stage<k>.png (망가진 단계 0~2) → dummy/stage<k>_black.png (흰 그림은 맞았을 때 쓰는 stage<k>_white.png 를 같이 씀)
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.normpath(os.path.join(HERE, '..', '..', 'images'))
BLACK = (22, 20, 32)
WHITE = (244, 248, 255)


def silhouette(src: str, dst: str, colour) -> None:
    im = Image.open(src).convert('RGBA')
    out = Image.new('RGBA', im.size, colour + (0,))
    out.putalpha(im.getchannel('A'))
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            a = px[x, y][3]
            px[x, y] = colour + (a,)
    out.save(dst)


def main():
    for view in ('south', 'north', 'east', 'west'):
        src = os.path.join(IMAGES, 'golem', f'{view}.png')
        silhouette(src, os.path.join(IMAGES, 'golem', f'shock_{view}_black.png'), BLACK)
        silhouette(src, os.path.join(IMAGES, 'golem', f'shock_{view}_white.png'), WHITE)
    for k in range(3):
        silhouette(os.path.join(IMAGES, 'dummy', f'stage{k}.png'), os.path.join(IMAGES, 'dummy', f'stage{k}_black.png'), BLACK)
    print('shock silhouettes')


if __name__ == '__main__':
    main()
