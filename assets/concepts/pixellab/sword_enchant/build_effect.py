"""검 속성 이펙트 시트 만들기 (2026-11-20 사용자 요청: 검에 불·전기·어둠 이펙트).

PixelLab VFX(vfx_workbench)로 세운 칼(낡은 검을 90도 돌린 그림) 둘레에 만든 반복 이펙트를
게임의 칼 그림과 같은 방향(칼끝이 오른쪽 0도, 손이 그림 한가운데)으로 돌려 한 줄 시트로 내보낸다.
게임은 칼을 그릴 때 이 시트를 칼과 같은 손 위치·각도로 돌려 겹친다 (칼을 바꿔 끼워도 그대로 붙음).

원본: <속성>/dl/pack/whole.png (게임 팩의 '이펙트만' 클립, 16×45 프레임, 5열). 세운 칼의 손(칼 그림 한가운데)은
프레임의 (8, 35), 칼끝은 위쪽. 오른쪽으로 90도 돌리면 위 → 오른쪽.
출력: assets/images/effects/sword_enchant/<속성>.png (FRAME_W × FRAME_H 프레임을 가로로 FRAMES 장)
"""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'images', 'effects', 'sword_enchant')
FRAME_W, FRAME_H = 80, 24  # game/config.py SWORD_EFFECT_FRAME_SIZE 와 같게
HAND = (40, 12)  # 출력 프레임에서 손 자리 (그림 한가운데)
SRC_HAND = (8, 35)  # 원본 프레임에서 손 자리
ELEMENTS = ('fire',)  # 그림이 있는 속성 (전기·어둠은 만들 때 추가)


def rotate_frame(frame):
    """세운 칼 기준 프레임 → 칼끝이 오른쪽인 프레임 (손을 HAND 에)."""
    out = Image.new('RGBA', (FRAME_W, FRAME_H), (0, 0, 0, 0))
    src, dst = frame.load(), out.load()
    for fy in range(frame.height):
        for fx in range(frame.width):
            c = src[fx, fy]
            if not c[3]:
                continue
            x = HAND[0] + (SRC_HAND[1] - fy)  # 위로 갈수록 칼끝 쪽 (오른쪽)
            y = HAND[1] + (fx - SRC_HAND[0])  # 칼의 오른쪽 → 아래
            if 0 <= x < FRAME_W and 0 <= y < FRAME_H:
                dst[x, y] = c
    return out


def build(element):
    pack = os.path.join(HERE, element, 'dl', 'pack')
    manifest = json.load(open(os.path.join(pack, 'manifest.json'), encoding='utf-8'))
    clip = next(c for c in manifest['clips'] if c['name'] == 'whole')
    fw, fh = clip['frame']['w'], clip['frame']['h']
    sheet_info = clip['sheets'][0]
    cols = sheet_info['columns']
    sheet = Image.open(os.path.join(pack, sheet_info['file'])).convert('RGBA')
    n = clip['frames']
    strip = Image.new('RGBA', (FRAME_W * n, FRAME_H), (0, 0, 0, 0))
    for i in range(n):
        frame = sheet.crop(((i % cols) * fw, (i // cols) * fh, (i % cols + 1) * fw, (i // cols + 1) * fh))
        strip.alpha_composite(rotate_frame(frame), (i * FRAME_W, 0))
    os.makedirs(OUT, exist_ok=True)
    strip.save(os.path.join(OUT, f'{element}.png'))
    print(element, n, 'frames', manifest['fps'], 'fps')


if __name__ == '__main__':
    for e in ELEMENTS:
        build(e)
