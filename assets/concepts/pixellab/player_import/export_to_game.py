"""PixelLab 으로 새로 만든 주인공 그림(remake_raw)을 게임 그림으로 내보낸다 (2026-11-17).

- 측면 공격 1·2·3타: build_remake_preview.build_layers 의 레이어(잔상+몸 / 손)를 96×64 캔버스 8프레임 시트로.
  칼 위치표(손 x, 손 y, 각도, 몸 뒤)는 config.PLAYER_ATTACK_SWORD 에 붙여 넣을 값으로 출력한다.
- 걷기 4방향: PixelLab 걷기 템플릿(32×48, 8프레임). 발이 2~3픽셀 위에 있어 방향별로 내려 서 있는 그림과 맞춘다.
- 점프 4방향: PixelLab 8프레임 중 방향마다 5장(웅크림, 도약, 최고점, 다리 펴기, 착지)을 골라 32×48 로 자른다.
  높이는 게임 코드가 띄우므로, 그림 안에서 떠오른 만큼은 머리 높이를 기준 자세에 맞춰 줄인다.
Pillow 필요 (게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/pixellab/player_import/export_to_game.py`
"""
import os
import sys
from collections import Counter

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_remake_preview as b  # noqa: E402

ROOT = b.ROOT
OUT = os.path.join(ROOT, 'assets', 'images', 'player')
CELL = b.CELL
SPRITE_W, SPRITE_H = 32, 48
ATTACK_W, ATTACK_H = 96, 64
ATTACK_FOOT_ROW = ATTACK_H - 8 - 1  # config.PLAYER_ATTACK_FOOT_MARGIN = 8

# 점프: 방향별로 쓸 PixelLab 프레임 (1~8): 웅크림, 도약, 최고점, 다리 펴기, 착지
JUMP_PICK = {
    'front': (0, [1, 2, 4, 5, 6]),      # (시트 행, 프레임) south
    'side': (1, [1, 2, 4, 6, 7]),       # east
    'back': (2, [2, 3, 5, 7, 8]),       # north
    'side_left': (3, [1, 2, 4, 7, 8]),  # west (왼손·오른손이 다르므로 뒤집지 않은 왼쪽 전용 그림)
}
WALK_ROWS = {'front': 0, 'side': 1, 'back': 2}  # south, east, north (왼쪽은 측면을 뒤집는다)


def ref_anchor(frame):
    """기준(서 있는) 자세의 발 아래 가운데: (가운데 x, 발끝 줄 y)."""
    x0, y0, x1, y1 = frame.getchannel('A').getbbox()
    return (x0 + x1) // 2, y1 - 1, y0


def export_attacks():
    tables = []
    for hit, (name, path, row) in enumerate(b.ATTACKS, start=1):
        frames = b.cells(path, row)
        cx, foot, _ = ref_anchor(frames[0])
        dx, dy = ATTACK_W // 2 - cx, ATTACK_FOOT_ROW - foot
        layers, _, _ = b.build_layers(name, frames[1:])
        body = Image.new('RGBA', (ATTACK_W * len(layers), ATTACK_H), (0, 0, 0, 0))
        hand = Image.new('RGBA', body.size, (0, 0, 0, 0))
        table = []
        for i, layer in enumerate(layers):
            body.alpha_composite(layer['body'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
            hand.alpha_composite(layer['hand'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
            hx, hy, angle, behind = layer['sword']
            table.append((round(hx + dx), round(hy + dy), round(angle), behind))
        body.save(os.path.join(OUT, 'sword_attack', f'side_{hit}.png'))
        hand.save(os.path.join(OUT, 'sword_attack', f'side_{hit}_hand.png'))
        tables.append(table)
    return tables


def _src_box(dx, dy):
    """68 칸에서 96×64 캔버스 안에 들어오는 부분."""
    return (max(0, -dx), max(0, -dy), min(CELL, ATTACK_W - dx), min(CELL, ATTACK_H - dy))


def _dst(i, dx, dy):
    return (i * ATTACK_W + max(0, dx), max(0, dy))


def clean_white(img):
    """걷기 템플릿에 섞인 흰 점(작은 덩어리)을 둘레 색으로 바꾼다."""
    px = img.load()
    w, h = img.size
    white = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and min(px[x, y][:3]) > 170]
    for comp in b.components(white):
        if len(comp) > 6:
            continue
        for x, y in comp:
            near = [px[x + ex, y + ey] for ex in (-1, 0, 1) for ey in (-1, 0, 1)
                    if (ex or ey) and 0 <= x + ex < w and 0 <= y + ey < h and px[x + ex, y + ey][3]
                    and min(px[x + ex, y + ey][:3]) <= 170]
            px[x, y] = Counter(near).most_common(1)[0][0] if near else (0, 0, 0, 0)


def export_walk():
    sheet = Image.open(os.path.join(b.RAW, 'walk_sheet_32x48.png')).convert('RGBA')
    for view, row in WALK_ROWS.items():
        frames = [sheet.crop((c * SPRITE_W, row * SPRITE_H, (c + 1) * SPRITE_W, (row + 1) * SPRITE_H))
                  for c in range(8)]
        lowest = max(f.getchannel('A').getbbox()[3] for f in frames)
        shift = SPRITE_H - lowest  # 발끝을 맨 아래 줄로 (서 있는 그림과 같게)
        out = Image.new('RGBA', (SPRITE_W * 8, SPRITE_H), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            clean_white(f)
            out.alpha_composite(f.crop((0, 0, SPRITE_W, SPRITE_H - shift)), (i * SPRITE_W, shift))
        out.save(os.path.join(OUT, 'walk', f'{view}.png'))


def export_jump():
    sheet = Image.open(os.path.join(b.RAW, 'jump_sheet_68.png')).convert('RGBA')
    for view, (row, picks) in JUMP_PICK.items():
        cells = [sheet.crop((c * CELL, row * CELL, (c + 1) * CELL, (row + 1) * CELL)) for c in range(9)]
        cx, foot, top = ref_anchor(cells[0])
        left, bottom = cx - SPRITE_W // 2, foot + 1
        out = Image.new('RGBA', (SPRITE_W * len(picks), SPRITE_H), (0, 0, 0, 0))
        for i, c in enumerate(picks):
            f = cells[c]
            _, y0, _, y1 = f.getchannel('A').getbbox()
            # 땅에서 뜬 그림은 머리를 기준 자세 높이까지만 (떠오르는 높이는 게임 코드가 그린다)
            lift = max(0, top - y0) if y1 - 1 < foot else 0
            out.alpha_composite(f.crop((left, bottom - SPRITE_H - lift, left + SPRITE_W, bottom - lift)),
                                (i * SPRITE_W, 0))
        out.save(os.path.join(OUT, 'jump', f'{view}.png'))


def main():
    tables = export_attacks()
    export_walk()
    export_jump()
    print('PLAYER_ATTACK_SWORD = (')
    for t in tables:
        print('    (' + ', '.join(f'({x}, {y}, {a}, {bh})' for x, y, a, bh in t) + '),')
    print(')')


if __name__ == '__main__':
    main()
