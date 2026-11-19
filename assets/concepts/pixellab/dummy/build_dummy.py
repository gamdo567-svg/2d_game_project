"""연습용 허수아비 그림을 게임용으로 내보내기 (2026-11-20 사용자 요청: 도형 허수아비 → PixelLab 밀짚 더미,
체력이 닳으며 부서지고 맞을 때 자연스럽게 흔들리게).

PixelLab 원본 (48×56, 이 폴더):
  dummy_stage0.png  멀쩡함 (straw_A 에서 발밑에 떨어진 밀짚 조각을 지움)
  dummy_stage1.png  베인 자국·삐져나온 밀짚 (edit_image)
  dummy_stage2.png  머리가 기울고 왼팔 밀짚이 떨어져 나감 (edit_image)
  dummy_broken.png  부러진 기둥 밑동 + 흩어진 밀짚 (edit_image)
  break/f1~f8.png   stage2 → broken 으로 무너지는 8장 (animate_image, 시작·끝 지정)
출력 (assets/images/dummy/):
  stage0~2.png, stage0~2_white.png (맞을 때 하얗게 깜빡이는 실루엣), break.png (가로 8장, 마지막 = 부서진 모습)
기둥 밑(회전 축)은 원본 (23, 50) — game/config.py DUMMY_PIVOT 과 같아야 한다.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'images', 'dummy')
W, H = 48, 56


def drop_specks(im, max_size=4):
    """몸에서 떨어진 작은 점(PixelLab 이 남긴 얼룩)을 지운다."""
    im = im.copy()
    px = im.load()
    seen = set()
    for y in range(H):
        for x in range(W):
            if px[x, y][3] == 0 or (x, y) in seen:
                continue
            comp, stack = [], [(x, y)]
            seen.add((x, y))
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and px[nx, ny][3]:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
            if len(comp) <= max_size:
                for p in comp:
                    px[p] = (0, 0, 0, 0)
    return im


def white(im):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    src, dst = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            if src[x, y][3]:
                dst[x, y] = (255, 255, 255, 255)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for k, name in enumerate(('dummy_stage0', 'dummy_stage1', 'dummy_stage2')):
        im = drop_specks(Image.open(os.path.join(HERE, f'{name}.png')).convert('RGBA'))
        im.save(os.path.join(OUT, f'stage{k}.png'))
        white(im).save(os.path.join(OUT, f'stage{k}_white.png'))
    frames = [Image.open(os.path.join(HERE, 'break', f'f{i}.png')).convert('RGBA') for i in range(1, 9)]
    frames[-1] = drop_specks(Image.open(os.path.join(HERE, 'dummy_broken.png')).convert('RGBA'))  # 끝은 정리한 부서진 모습
    sheet = Image.new('RGBA', (W * len(frames), H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * W, 0))
    sheet.save(os.path.join(OUT, 'break.png'))
    print('ok', OUT)


if __name__ == '__main__':
    main()
