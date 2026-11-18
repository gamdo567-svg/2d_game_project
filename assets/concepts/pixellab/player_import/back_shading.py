"""후면(뒷모습) 망토 명암 넣기 (2026-11-18 사용자: 후면은 정면·측면보다 망토 주름이 적고 색이 밝아 보임).

뒷모습은 망토가 몸을 덮어 어두운 부분이 적고, 망토 절반이 중간 갈색 한 색이라 밝고 밋밋해 보였다
(아주 어두운 픽셀 14% / 정면 33%, 몸 색 11 / 22, 하이라이트 없음). 자세·모양은 그대로 두고 망토 색만 바꾼다:
빛은 왼쪽 위에서 온다고 보고 밑단과 오른쪽 가장자리는 그늘, 왼쪽 위 가장자리는 하이라이트, 망토의 어두운 주름 줄은
위아래로 그늘을 이어 주름을 또렷하게 한다. 색은 정면 그림이 쓰는 망토 색 단계(RAMP)에서 고른다.

게임 그림을 고치면 다시 돌릴 때 두 번 어두워지므로, 명암을 넣기 전 그림을 back_shading/flat/ 에 두고 늘 그것에서 만든다.
  python back_shading.py              후면 공격 그림 전부 (flat 이 없으면 지금 게임 그림을 flat 으로 보관)
  python back_shading.py --refresh P  내보내기가 게임 그림 P 를 새로 썼을 때: P 를 flat 으로 보관하고 명암을 넣음
"""
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
PLAYER = os.path.join(ROOT, 'assets', 'images', 'player')
FLAT = os.path.join(HERE, 'back_shading', 'flat')
# 후면 공격 그림 (몸·손 레이어)만. 서기·걷기·점프·회피·패링은 원래 그림 그대로 둔다
# (같은 날 사용자: 기존 걷기나 다른 포즈는 명암이 없었으니 새로 넣지 말 것).
TARGETS = ['sword_attack/back_1.png', 'sword_attack/back_1_hand.png', 'sword_attack/back_2.png',
           'sword_attack/back_2_hand.png', 'sword_attack/back_3.png', 'sword_attack/back_3_hand.png']
# 정면 그림의 망토 색 단계 (어두움 → 밝음)
RAMP = [(36, 23, 29), (60, 37, 43), (74, 49, 51), (92, 55, 54), (102, 64, 61), (118, 73, 67), (158, 105, 94)]
BASE = 4  # RAMP 에서 망토 기본색 자리


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def is_blue(c):
    return c[2] > 150 and c[0] < 90


def is_cape(c):
    """명암을 넣을 망토·후드 색 (중간~밝은 갈색). 테두리·다리·주름 줄·파랑은 그대로."""
    return c[3] == 255 and not is_blue(c) and 60 <= lum(c) <= 95 and c[0] > c[2]


def is_fold(c):
    """망토 안의 어두운 주름 줄."""
    return c[3] == 255 and not is_blue(c) and 30 <= lum(c) < 55


def nearest_step(c):
    return min(range(len(RAMP)), key=lambda i: abs(lum(RAMP[i]) - lum(c)))


def shade(im):
    im = im.convert('RGBA')
    src = im.load()
    out = im.copy()
    dst = out.load()
    w, h = im.size

    def empty(x, y):
        return not (0 <= x < w and 0 <= y < h) or src[x, y][3] < 128

    def run(x, y, dx, dy, limit=4):
        """(x, y) 에서 (dx, dy) 쪽으로 빈칸까지 몇 칸 (limit 넘으면 limit+1)."""
        for k in range(1, limit + 1):
            if empty(x + dx * k, y + dy * k):
                return k
        return limit + 1

    for y in range(h):
        for x in range(w):
            c = src[x, y]
            if not is_cape(c):
                continue
            # 명암 대비를 정면·측면에 맞춤 (같은 날 사용자: 정면·측면과 색감이 다름 → 어두운 픽셀 24% / 정면 45%, 밝은 픽셀 1% / 10%):
            # 빛은 왼쪽 위. 가로 위치로 밝은 쪽(왼쪽 1/3)·가운데·그늘 쪽(오른쪽 1/3)을 나누고 가장자리·밑단·주름은 더 어둡게,
            # 왼쪽 테두리·후드 왼쪽 위는 밝게.
            down, right, left, up = run(x, y, 0, 1), run(x, y, 1, 0), run(x, y, -1, 0), run(x, y, 0, -1)
            wide_l, wide_r = run(x, y, -1, 0, 30), run(x, y, 1, 0, 30)
            fx = wide_l / (wide_l + wide_r)  # 0 = 왼쪽 끝, 1 = 오른쪽 끝
            below_dark = any(0 <= y + k < h and src[x, y + k][3] == 255 and lum(src[x, y + k]) < 30 for k in (1, 2))
            above_dark = any(0 <= y - k < h and src[x, y - k][3] == 255 and lum(src[x, y - k]) < 30 for k in (1, 2))
            step = BASE + 1 if fx < 0.22 else BASE if fx < 0.42 else BASE - 1 if fx < 0.62 else BASE - 2 if fx < 0.8 else BASE - 3
            if right <= 2:
                step -= 1  # 오른쪽 가장자리 그늘
            if right == 1:
                step -= 1
            if down <= 2 or below_dark:
                step -= 1  # 밑단·다리 위 그늘
            if down == 1:
                step -= 1
            if above_dark and up > 1:
                step -= 1  # 후드 아래·어두운 줄 바로 밑 그늘
            if any(is_fold(src[x, y + k]) for k in (-2, -1, 1, 2) if 0 <= y + k < h):
                step -= 1  # 주름 줄 위아래로 그늘을 이어 주름을 또렷하게
            if left == 1 and down > 2:
                step += 1  # 왼쪽 가장자리 하이라이트
            if up <= 2 and fx < 0.45:
                step += 1  # 후드·어깨 왼쪽 위 하이라이트
            if up == 1 and fx < 0.3:
                step += 1
            step = max(0, min(len(RAMP) - 1, step))
            dst[x, y] = RAMP[step] + (255,)
            continue
            step = max(1, min(len(RAMP) - 1, step))
            dst[x, y] = RAMP[step] + (255,)
    return out


def apply(rel):
    flat = os.path.join(FLAT, rel)
    game = os.path.join(PLAYER, rel)
    if not os.path.exists(flat):
        os.makedirs(os.path.dirname(flat), exist_ok=True)
        shutil.copyfile(game, flat)
    shade(Image.open(flat)).save(game)


def refresh(game_path):
    rel = os.path.relpath(os.path.abspath(game_path), PLAYER).replace(os.sep, '/')
    flat = os.path.join(FLAT, rel)
    os.makedirs(os.path.dirname(flat), exist_ok=True)
    shutil.copyfile(game_path, flat)
    shade(Image.open(flat)).save(game_path)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == '--refresh':
        for p in sys.argv[2:]:
            refresh(p)
        return
    for rel in TARGETS:
        if os.path.exists(os.path.join(PLAYER, rel)):
            apply(rel)
            print('shaded', rel)


if __name__ == '__main__':
    main()
